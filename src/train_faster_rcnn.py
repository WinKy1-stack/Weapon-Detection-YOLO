import os
import torch
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.transforms import functional as F
from torch.utils.data import DataLoader, Dataset
from PIL import Image
import yaml
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

# =============================
# CONFIG
# =============================
DATA_YAML = "dataset/data.yaml"
RUN_DIR = "runs/detect/faster_rcnn"
os.makedirs(RUN_DIR, exist_ok=True)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Using device: {DEVICE}") # Thêm print để biết device
BATCH_SIZE = 24
EPOCHS = 1
LR = 0.0005

# <-- SỬA ĐỂ CHẠY NHANH: Cấu hình chạy nhanh
# ----------------------------------
QUICK_RUN = True  # Đặt là True để chạy thử, False để chạy thật
MAX_BATCHES = 10    # Số batch tối đa để chạy thử
# ----------------------------------

# =============================
# CUSTOM DATASET
# =============================
class WeaponDataset(Dataset):
    def __init__(self, img_dir, label_dir, transforms=None):
        self.img_dir = img_dir
        self.label_dir = label_dir
        self.imgs = [x for x in os.listdir(img_dir) if x.endswith((".jpg", ".png"))]
        self.transforms = transforms

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        img_name = self.imgs[idx]
        img_path = os.path.join(self.img_dir, img_name)
        label_path = os.path.join(self.label_dir, img_name.replace(".jpg", ".txt").replace(".png", ".txt"))
        img = Image.open(img_path).convert("RGB")
        img_width, img_height = img.size # Lấy kích thước ảnh

        boxes, labels = [], []
        if os.path.exists(label_path):
            with open(label_path) as f:
                for line in f:
                    cls, cx, cy, w, h = map(float, line.split())
                    cls = int(cls)
                    xmin = (cx - w / 2) * img_width
                    ymin = (cy - h / 2) * img_height
                    xmax = (cx + w / 2) * img_width
                    ymax = (cy + h / 2) * img_height
                    boxes.append([xmin, ymin, xmax, ymax])
                    labels.append(cls + 1) # class 0 (YOLO) -> class 1 (Faster R-CNN)

        boxes = torch.as_tensor(boxes, dtype=torch.float32).reshape(-1, 4)
        labels = torch.as_tensor(labels, dtype=torch.int64)
        image_id = torch.tensor([idx])
        
        if boxes.shape[0] == 0:
            area = torch.as_tensor([], dtype=torch.float32)
        else:
            area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0])
            
        iscrowd = torch.zeros((len(boxes),), dtype=torch.int64)

        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["image_id"] = image_id
        target["area"] = area
        target["iscrowd"] = iscrowd

        if self.transforms:
            img = F.to_tensor(img)
        else:
            img = F.to_tensor(img)
            
        # FIX 1: Phải return img, target
        return img, target

# Hàm collate_fn tùy chỉnh cho DataLoader
def collate_fn(batch):
    return tuple(zip(*batch))

# =============================
# HÀM HUẤN LUYỆN CHÍNH
# =============================
def train():
    # FIX 2: Toàn bộ logic phải nằm trong hàm
    print("... Đang tải cấu hình data.yaml ...")
    with open(DATA_YAML, "r") as f:
        data_cfg = yaml.safe_load(f)
    classes = data_cfg["names"]
    NUM_CLASSES = len(classes) + 1  # +1 for background
    train_dir = data_cfg["train"]
    val_dir = data_cfg["val"]

    print("... Đang chuẩn bị DataLoaders ...")
    train_label_dir = os.path.normpath(train_dir.replace("images", "labels"))
    val_label_dir = os.path.normpath(val_dir.replace("images", "labels"))

    print(f"📁 Train Img Dir: {train_dir}")
    print(f"📁 Train Lbl Dir: {train_label_dir}")
    print(f"📁 Val Img Dir: {val_dir}")
    print(f"📁 Val Lbl Dir: {val_label_dir}")

    train_dataset = WeaponDataset(
        img_dir=train_dir,
        label_dir=train_label_dir
    )
    val_dataset = WeaponDataset(
        img_dir=val_dir,
        label_dir=val_label_dir
    )

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=1, shuffle=False, collate_fn=collate_fn)

    print("✅ Đã tạo DataLoaders thành công.")

    print("... Đang tải mô hình Faster R-CNN ...")
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights="FasterRCNN_ResNet50_FPN_Weights.DEFAULT")
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, NUM_CLASSES)
    model.to(DEVICE)
    print("✅ Đã tải mô hình Faster R-CNN.")

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=LR)
    lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

    loss_history = []
    print("\n🔥 Bắt đầu huấn luyện...")
    if QUICK_RUN:
        print(f"⚠️  CHẾ ĐỘ CHẠY THỬ: Sẽ chỉ chạy {MAX_BATCHES} batches.")

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0
        
        # Thêm enumerate để đếm batch
        pbar = tqdm(enumerate(train_loader), desc=f"Epoch {epoch+1}/{EPOCHS}", total=len(train_loader))
        
        # Biến i là chỉ số batch
        for i, (imgs, targets) in pbar:
            imgs = [img.to(DEVICE) for img in imgs]
            targets = [{k: v.to(DEVICE) for k, v in t.items()} for t in targets]

            try:
                loss_dict = model(imgs, targets)
                losses = sum(loss for loss in loss_dict.values())

                if not torch.isfinite(losses):
                    print(f"⚠️ Cảnh báo: Lỗi (Loss) không hữu hạn (non-finite). Bỏ qua batch này.")
                    continue

                optimizer.zero_grad()
                losses.backward()
                optimizer.step()
                
                total_loss += losses.item()
                pbar.set_postfix(loss=f"{losses.item():.4f}")

            except Exception as e:
                print(f"\n❌ LỖI GẶP PHẢI KHI HUẤN LUYỆN: {e}")
                print("--- Thông tin Debug Target ---")
                for i_target, t in enumerate(targets): # Sửa tên biến 'i'
                    print(f"  Target {i_target} boxes: {t['boxes'].shape}, labels: {t['labels'].shape}")
                print("------------------------------")
                continue 

            # <-- FIX 3: Thêm logic để dừng sớm
            if QUICK_RUN and i >= (MAX_BATCHES - 1):
                print(f"\n[QUICK RUN] Đã chạy {MAX_BATCHES} batches, dừng epoch sớm...")
                break # Thoát khỏi vòng lặp train_loader

        lr_scheduler.step()
        
        # Tính toán loss trung bình dựa trên số batch đã chạy
        num_batches_run = i + 1
        avg_loss = total_loss / num_batches_run
        loss_history.append(avg_loss)
        print(f"Epoch [{epoch+1}/{EPOCHS}] Average Loss: {avg_loss:.4f} (trên {num_batches_run} batches)")

    # =============================
    # SAVE MODEL & PLOT LOSS
    # =============================
    print("\n🎉 Huấn luyện hoàn tất!")
    
    model_save_path = os.path.join(RUN_DIR, "faster_rcnn_model.pth")
    plot_save_path = os.path.join(RUN_DIR, "loss_curve.png")

    # FIX 4: Chuẩn hóa đường dẫn cho Windows
    model_save_path_norm = os.path.normpath(model_save_path)
    plot_save_path_norm = os.path.normpath(plot_save_path)

    torch.save(model.state_dict(), model_save_path_norm)
    print(f"✅ Model saved to: {model_save_path_norm}") 

    plt.figure(figsize=(10, 5))
    plt.plot(loss_history, label="Train Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Faster R-CNN Training Loss")
    plt.legend()
    
    plt.savefig(plot_save_path_norm)
    print(f"✅ Loss curve saved to: {plot_save_path_norm}")
    # plt.show()

# =============================
# ENTRY POINT (ĐIỂM KHỞI CHẠY)
# =============================
if __name__ == "__main__":
    train() # FIX 5: Gọi hàm train
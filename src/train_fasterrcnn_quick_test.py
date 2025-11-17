"""
Quick test trainer for Faster R-CNN (small fine-tune, time-limited).

- Loads images and YOLO-format labels from a dataset directory (default: dataset/train)
- Fine-tunes a pretrained torchvision Faster R-CNN (ResNet50-FPN) for a short time
- Stops after --time-limit seconds (default 300s) or when epochs complete
- Saves model state_dict to runs/models/fasterrcnn_quick_test.pth

Usage (PowerShell):
& C:/Workspace/weapon-detection/venv/Scripts/Activate.ps1
python src/train_fasterrcnn_quick_test.py --data-dir dataset --time-limit 300

Note: Ensure torch and torchvision are installed in your venv.
"""

import argparse
import os
import time
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision
from torchvision.transforms import functional as F
import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description="Quick Faster R-CNN fine-tune (time-limited)")
    p.add_argument("--data-dir", default="dataset", help="Dataset root with train/images and train/labels")
    p.add_argument("--split", default="train", help="Which split to use (train/val)")
    p.add_argument("--output", default="runs/models/fasterrcnn_quick_test.pth", help="Output path for saved model")
    p.add_argument("--time-limit", type=int, default=300, help="Time limit in seconds (default 300s)")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--lr", type=float, default=0.005)
    p.add_argument("--momentum", type=float, default=0.9)
    p.add_argument("--weight-decay", type=float, default=0.0005)
    p.add_argument("--max-samples", type=int, default=200, help="Max number of images to use (keeps run short)")
    p.add_argument("--num-classes", type=int, default=6, help="Number of classes (including background). Adjust if needed.")
    return p.parse_args()


class YOLODataset(Dataset):
    """Minimal YOLO-format dataset for object detection.
    Expects directory structure: <data_dir>/<split>/images and <data_dir>/<split>/labels.
    Label file format: class x_center y_center width height (normalized)
    """

    def __init__(self, root, split="train", transforms=None, max_samples=None):
        self.images_dir = os.path.join(root, split, "images")
        self.labels_dir = os.path.join(root, split, "labels")
        self.transforms = transforms
        self.samples = []

        if not os.path.isdir(self.images_dir):
            raise FileNotFoundError(f"Images dir not found: {self.images_dir}")

        files = sorted([f for f in os.listdir(self.images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        if max_samples:
            files = files[:max_samples]

        for img_name in files:
            img_path = os.path.join(self.images_dir, img_name)
            label_name = os.path.splitext(img_name)[0] + ".txt"
            label_path = os.path.join(self.labels_dir, label_name)
            self.samples.append((img_path, label_path))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label_path = self.samples[idx]
        img = Image.open(img_path).convert("RGB")
        w, h = img.size

        boxes = []
        labels = []

        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f.read().strip().splitlines():
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    cls = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    bw = float(parts[3])
                    bh = float(parts[4])

                    # Convert YOLO normalized to pixel coords
                    xmin = (x_center - bw / 2.0) * w
                    ymin = (y_center - bh / 2.0) * h
                    xmax = (x_center + bw / 2.0) * w
                    ymax = (y_center + bh / 2.0) * h

                    # clamp
                    xmin = max(0.0, xmin)
                    ymin = max(0.0, ymin)
                    xmax = min(w, xmax)
                    ymax = min(h, ymax)

                    # torchvision detection labels should be 1..N (0 is background)
                    labels.append(cls + 1)
                    boxes.append([xmin, ymin, xmax, ymax])

        # Convert to tensors
        image = F.to_tensor(img)
        if boxes:
            boxes = torch.as_tensor(boxes, dtype=torch.float32)
            labels = torch.as_tensor(labels, dtype=torch.int64)
        else:
            boxes = torch.zeros((0, 4), dtype=torch.float32)
            labels = torch.zeros((0,), dtype=torch.int64)

        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["image_id"] = torch.tensor([idx])
        target["area"] = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0]) if boxes.shape[0] > 0 else torch.tensor([])
        target["iscrowd"] = torch.zeros((boxes.shape[0],), dtype=torch.int64)

        return image, target


def collate_fn(batch):
    return tuple(zip(*batch))


def make_model(num_classes):
    # Load a pre-trained model for classification and return
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    # Get number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # Replace the pre-trained head with a new one
    model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(in_features, num_classes)
    return model


def train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10):
    model.train()
    lr_scheduler = None
    for i, (images, targets) in enumerate(data_loader):
        images = list(img.to(device) for img in images)
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())

        optimizer.zero_grad()
        losses.backward()
        optimizer.step()

        if i % print_freq == 0:
            print(f"Epoch {epoch} Iter {i}/{len(data_loader)} Loss: {losses.item():.4f}")


def main():
    args = parse_args()
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    dataset = YOLODataset(args.data_dir, split=args.split, max_samples=args.max_samples)
    if len(dataset) == 0:
        print("No images found in dataset. Check your data-dir and split.")
        return

    data_loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn, num_workers=2)

    device = torch.device(args.device if torch.cuda.is_available() and args.device.startswith('cuda') else 'cpu')
    model = make_model(args.num_classes)
    model.to(device)

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=args.lr, momentum=args.momentum, weight_decay=args.weight_decay)

    start_time = time.time()
    elapsed = 0
    epoch = 0

    try:
        while elapsed < args.time_limit:
            epoch += 1
            train_one_epoch(model, optimizer, data_loader, device, epoch)
            elapsed = time.time() - start_time
            print(f"Elapsed: {elapsed:.1f}s / {args.time_limit}s")
            # Save a checkpoint after each epoch
            torch.save(model.state_dict(), args.output)
            if elapsed >= args.time_limit:
                break
    except KeyboardInterrupt:
        print("Training interrupted by user.")

    # Final save
    torch.save(model.state_dict(), args.output)
    print(f"Model saved to: {args.output}")


if __name__ == '__main__':
    main()

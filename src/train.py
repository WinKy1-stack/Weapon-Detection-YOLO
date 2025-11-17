from ultralytics import YOLO
import torch

def train_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🚀 Using device: {device}")

    # Khởi tạo model pretrained
    model = YOLO("yolov8m.pt")  # có thể đổi thành yolov8s.pt nếu GPU yếu

    # Đường dẫn tuyệt đối tới file data.yaml
    data_path = r"C:/Workspace/weapon-detection/dataset/data.yaml"

    results = model.train(
        data=data_path,
        epochs=50,
        imgsz=512, #640
        batch=8,
        optimizer='SGD',
        lr0=0.001,
        lrf=0.01,
        dropout=0.2,
        patience=10,
        weight_decay=0.001,
        device=device,
        name='weapons_yolov8_gpu'
    )

    print("\n✅ Training completed!")
    print("📦 Model saved at: runs/detect/weapons_yolov8/weights/best.pt")

if __name__ == "__main__":
    train_model()

from ultralytics import YOLO

def train_stable():
    # Use the latest optimized stable model as a starting point (if exists)
    model = YOLO(r"runs/detect/weapons_yolov8_optimized_stable/weights/best.pt")

    results = model.train(
        data="dataset/data.yaml",
        epochs=100,
        batch=8,             # vẫn ổn cho RTX 3050
        imgsz=640,
        device=0,
        workers=2,           # giảm worker để tránh MemoryError
        name="weapons_yolov8_optimized_stable",
        optimizer="AdamW",
        lr0=0.001,
        patience=20,
        pretrained=True,
        dropout=0.2,
        cos_lr=True,
        multi_scale=False,   # tắt multi-scale
        cache='disk',        # cache xuống ổ cứng thay vì RAM
        mosaic=0.5,          # giảm mosaic intensity
        mixup=0.0,
        copy_paste=0.0,
        auto_augment="randaugment",
        fliplr=0.5,
        flipud=0.2,
        translate=0.1,
        scale=0.5,
        degrees=5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        amp=True             # mixed precision (tiết kiệm VRAM)
    )

    print("✅ Huấn luyện hoàn tất!")
    print(f"📁 Kết quả lưu tại: {results.save_dir}")

if __name__ == "__main__":
    train_stable()

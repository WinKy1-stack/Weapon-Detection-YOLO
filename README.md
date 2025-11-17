# 🔫 Weapon Detection System

Hệ thống phát hiện vũ khí sử dụng Deep Learning với hai kiến trúc: **YOLOv8** và **Faster R-CNN**. Hệ thống hỗ trợ phát hiện realtime, cảnh báo thông minh và phân tích chi tiết.

## 🌟 Tính năng

### Phát hiện đa nguồn
- 🖼️ **Ảnh tĩnh**: Phát hiện vũ khí trong ảnh đơn lẻ
- 🎥 **Video**: Xử lý và phát hiện trong video files
- 📹 **Realtime**: Phát hiện qua webcam/camera
- 👥 **Person-Weapon Pairing**: Xác định người cầm vũ khí

### Hệ thống cảnh báo thông minh
- 🚨 **Multi-level Alerts**: 3 mức độ nguy hiểm (Cao/Trung/Thấp)
- 💾 **MongoDB Integration**: Lưu trữ cảnh báo với metadata đầy đủ
- 📱 **Telegram Notifications**: Gửi cảnh báo kèm ảnh realtime
- 📊 **Analytics Dashboard**: Streamlit dashboard với biểu đồ và thống kê

### So sánh hai kiến trúc
- ⚡ **YOLOv8m**: Tốc độ cao, phù hợp realtime
- 🎯 **Faster R-CNN**: Độ chính xác cao, phù hợp phân tích chi tiết
- 📈 **Performance Metrics**: mAP, FPS, model size comparison

## 🔧 Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- CUDA 11.8+ (cho GPU training)
- 8GB+ RAM
- GPU với 4GB+ VRAM (khuyến nghị)

### Bước 1: Clone repository
```bash
git clone https://github.com/your-username/weapon-detection.git
cd weapon-detection
```

### Bước 2: Tạo môi trường ảo
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### Bước 3: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình MongoDB (tùy chọn)
```bash
# Cài đặt MongoDB Community Edition
# Khởi động MongoDB service
mongod --dbpath=./data/db
```

### Bước 5: Cấu hình Telegram Bot (tùy chọn)
```bash
# Đặt biến môi trường
$env:TELEGRAM_BOT_TOKEN = "your-bot-token"
$env:TELEGRAM_CHAT_ID = "your-chat-id"
```

## 📂 Cấu trúc dự án

```
weapon-detection/
├── config/                      # Cấu hình tập trung
│   └── config.py
├── dataset/                     # Dataset
│   ├── data.yaml
│   ├── train/
│   ├── val/
│   └── test/
├── src/
│   ├── alert_system/           # Hệ thống cảnh báo
│   │   ├── alert_manager.py    # Quản lý queue & worker
│   │   ├── danger_evaluator.py # Đánh giá mức độ nguy hiểm
│   │   └── notifier.py         # Gửi Telegram
│   ├── database/               # MongoDB integration
│   │   └── mongo_client.py
│   ├── inference/              # Detection logic
│   │   └── detector.py
│   ├── training/               # Training logic
│   │   └── trainer.py
│   ├── utils/                  # Utilities
│   │   └── logging.py
│   ├── dashboard_pair_analytics.py  # Streamlit dashboard
│   ├── train_fasterrcnn_full.py    # Train Faster R-CNN
│   ├── compare_models.py           # So sánh models
│   └── realtime_pair_detect.py     # Realtime detection
├── runs/                       # Training outputs
│   ├── detect/                # YOLO results
│   ├── models/                # Faster R-CNN checkpoints
│   ├── evaluate/              # Evaluation results
│   └── alerts_snapshots/      # Alert images
├── main.py                    # CLI entry point
├── requirements.txt
└── README.md


## 🚀 Sử dụng

### 1. Training YOLOv8

```bash
# Train với cấu hình optimized
python src/train_optimized.py

# Hoặc dùng CLI
python main.py train
```

### 2. Training Faster R-CNN (Full Dataset)

```bash
# Train full dataset với validation
python src/train_fasterrcnn_full.py --epochs 50 --batch-size 4

# Với early stopping
python src/train_fasterrcnn_full.py --epochs 100 --patience 10 --eval-interval 5
```

### 3. So sánh Models

```bash
# Chạy đánh giá và so sánh
python src/compare_models.py

# Kết quả được lưu tại: runs/evaluate/model_comparison.json
```

### 4. Detection

#### Detection trên ảnh/video
```bash
# Sử dụng YOLOv8
python main.py detect --source path/to/image.jpg

# Sử dụng Faster R-CNN (cần implement)
python src/detect_fasterrcnn.py --source path/to/image.jpg
```

#### Realtime detection với person-weapon pairing
```bash
# Terminal-based
python src/realtime_pair_detect.py

# Hoặc chạy dashboard Streamlit
streamlit run src/dashboard_pair_analytics.py
```

### 5. Dashboard & Analytics

```bash
# Khởi động dashboard
streamlit run src/dashboard_pair_analytics.py

# Mở trình duyệt tại: http://localhost:8501
```

**Dashboard features:**
- 🎥 Tab 1: Realtime detection với webcam/video
- 📊 Tab 2: Analytics và biểu đồ thống kê
- 🚨 Tab 3: Alert monitoring với MongoDB data

## ⚙️ Configuration

### Model Configuration (`config/config.py`)

```python
MODEL_CONFIG = {
    "base_model": "yolov8m.pt",
    "best_model": "runs/detect/weapons_yolov8_optimized_stable/weights/best.pt",
    "img_size": 640,
    "conf_threshold": 0.6
}
```

### Alert System

Cấu hình mức độ nguy hiểm trong `src/alert_system/danger_evaluator.py`:

- **🚨 NGUY HIỂM CAO**: Threat score >= 7
- **⚠️ CẢNH BÁO**: Threat score >= 5
- **ℹ️ THEO DÕI**: Threat score < 5

### Environment Variables

```bash
# Telegram (tùy chọn)
$env:TELEGRAM_BOT_TOKEN = "your-bot-token"
$env:TELEGRAM_CHAT_ID = "your-chat-id"

# MongoDB (tùy chọn)
$env:MONGO_URI = "mongodb://localhost:27017/"
```

## 📊 Model Performance

### YOLOv8m (Optimized)

| Metric | Value |
|--------|-------|
| mAP@0.5 | 87.5% |
| mAP@0.5:0.95 | 65.2% |
| Precision | 88.6% |
| Recall | 80.7% |
| FPS (RTX 3050) | ~45 |
| Model Size | 52 MB |

### Faster R-CNN (ResNet50-FPN)

| Metric | Value |
|--------|-------|
| mAP@0.5 | TBD* |
| mAP@0.5:0.95 | TBD* |
| Precision | TBD* |
| Recall | TBD* |
| FPS (RTX 3050) | ~8-12 |
| Model Size | ~160 MB |

*Chạy `python src/train_fasterrcnn_full.py` và `python src/compare_models.py` để có kết quả đầy đủ.

### Classes Detected

0. `fire` - Lửa
1. `firearm` - Súng
2. `grenade` - Lựu đạn
3. `knife` - Dao
4. `pistol` - Súng lục
5. `rocket` - Tên lửa/Rocket

## 🔧 Troubleshooting

### CUDA/GPU Issues

```bash
# Kiểm tra CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Train với CPU nếu không có GPU
python src/train_optimized.py --device cpu
```

### MongoDB Connection

```bash
# Kiểm tra MongoDB đang chạy
mongosh

# Khởi động MongoDB service
net start MongoDB
```

### Import Errors

```bash
# Đảm bảo chạy từ project root
cd C:\Workspace\weapon-detection

# Activate venv
.\venv\Scripts\activate
```

## 📝 TODO

- [ ] Hoàn thiện mAP calculation cho Faster R-CNN
- [ ] Thêm data augmentation nâng cao
- [ ] Implement model ensemble (YOLO + Faster R-CNN)
- [ ] Thêm export ONNX/TensorRT
- [ ] Tối ưu inference speed
- [ ] Thêm multi-camera support
- [ ] Cloud deployment (AWS/Azure)

## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết chi tiết.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

- Author: [Your Name]
- Email: your.email@example.com
- GitHub: [Your GitHub Profile]

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [PyTorch](https://pytorch.org/)
- [Torchvision](https://pytorch.org/vision/)
- [Streamlit](https://streamlit.io/)
- [MongoDB](https://www.mongodb.com/)


## 📝 Logging

Logs được lưu trong:
- Training logs: `logs/trainer_*.log`
- Detection logs: `logs/detector_*.log`
- Realtime detection logs: `runs/realtime_logs/`

## 🔧 Advanced Usage

### Export Model

```python
from src.training.trainer import WeaponTrainer

trainer = WeaponTrainer()
trainer.export_model(format='onnx')  # Export sang ONNX format
```

### Custom Training Configuration

```python
custom_config = {
    'epochs': 100,
    'batch_size': 16,
    'optimizer': 'Adam',
    'lr0': 0.001
}

trainer = WeaponTrainer()
trainer.train(custom_config=custom_config)
```

## 🤝 Contributing

1. Fork repository
2. Tạo branch feature mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 📧 Contact

Your Name - your.email@example.com

Project Link: https://github.com/your-username/weapon-detection

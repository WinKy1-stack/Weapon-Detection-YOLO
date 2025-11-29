# 🔫 Weapon Detection System

AI-powered weapon detection system using YOLOv8 with modern web interface.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![React](https://img.shields.io/badge/React-18-61dafb)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Latest-orange)

## ✨ Features

- 🎯 **Image Detection** - Upload images and detect weapons with bounding boxes
- 🎬 **Video Snapshot** - Process videos and capture frames with weapons
- 📹 **Realtime Webcam** - Live weapon detection via webcam
- 📊 **Dashboard** - Statistics and alerts overview
- 📈 **Analytics** - Charts and trends visualization
- 🚨 **Alert System** - Automated alert creation and management

## 🚀 Quick Start

```powershell
# Start everything
.\start-system.ps1
```

Then open: http://localhost:3000  
Login: `son@gmail.com` / `123456`

## 📸 Screenshots

### Detection Page
Upload images or videos to detect weapons with bounding boxes.

### Video Snapshot Mode
Process videos and automatically capture frames containing weapons.

### Dashboard
Overview of all detections and alerts with statistics.

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- YOLOv8m (trained model)
- OpenCV
- JWT Authentication

**Frontend:**
- React 18
- Vite
- TailwindCSS
- Chart.js

## 📖 Documentation

See [README_FINAL.md](README_FINAL.md) for complete documentation.

## 🎯 Model Performance

- **Model**: YOLOv8m (44.62 MB)
- **Inference Time**: 0.1-0.3s per image
- **Accuracy**: Trained on custom weapon dataset
- **Classes**: Firearm, Knife, etc.

## 🔧 Requirements

- Python 3.9+
- Node.js 16+
- 8GB RAM minimum
- CUDA GPU (optional, for faster processing)

## 📦 Installation

See [README_FINAL.md](README_FINAL.md) for detailed installation guide.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is for educational purposes.

## 🎓 Author

WinKy1-stack

---

⭐ Star this repo if you find it useful!

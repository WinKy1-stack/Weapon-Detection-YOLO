# 🔫 Weapon Detection System - Complete Guide

## 📋 Tổng Quan

Hệ thống phát hiện vũ khí tự động sử dụng YOLOv8 với giao diện web hiện đại.

**Tech Stack:**
- **Backend**: FastAPI + YOLOv8m (trained model)
- **Frontend**: React 18 + Vite + TailwindCSS
- **Database**: In-Memory (có thể migrate sang MongoDB)
- **Authentication**: JWT + bcrypt

---

## 🚀 Quick Start

### 1. Cài Đặt Dependencies

**Backend:**
```powershell
cd backend
pip install -r requirements.txt
```

**Frontend:**
```powershell
cd frontend
npm install
```

### 2. Chạy Hệ Thống

**Tự động (Khuyến nghị):**
```powershell
.\start-system.ps1
```

**Hoặc manual:**

**Terminal 1 - Backend:**
```powershell
cd C:\Workspace\weapon-detection
& backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

### 3. Truy Cập

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/v1/docs
- **Login**: `son@gmail.com` / `123456`

---

## 🎯 Tính Năng Chính

### 1. 🔐 Authentication
- Register/Login với JWT
- Password hashing với bcrypt
- Protected routes

### 2. 📸 Image Detection
- Upload ảnh
- Phát hiện vũ khí với bounding boxes
- Auto-create alerts
- Person-weapon pairing

### 3. 🎬 Video Detection (Snapshot Mode)
- **Upload video** → Model xử lý từng frame
- **Chỉ chụp ảnh** những frame có vũ khí
- Mỗi snapshot có bounding boxes vẽ sẵn
- Download từng snapshot riêng

**Workflow:**
```
Video → Xử lý frame by frame → 
  Frame có vũ khí? 
    → YES: Chụp snapshot với bbox
    → NO: Skip
→ Trả về gallery snapshots
```

### 4. 📹 Realtime Webcam
- WebSocket streaming
- Phát hiện real-time
- FPS counter

### 5. 📊 Dashboard
- Thống kê 7 ngày
- Recent alerts
- Charts: Total, High danger, Medium, Today

### 6. 📈 Analytics
- 4 Chart.js charts:
  - Danger level distribution (Pie)
  - Weapon types (Bar)
  - Daily trends (Line)
  - Hourly activity (Bar)

### 7. 🚨 Alerts Management
- List alerts với pagination
- Filter: weapon_class, danger_level, date
- Delete alerts
- View snapshot details

---

## 📂 Project Structure

```
weapon-detection/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # Entry point
│   │   ├── api/
│   │   │   └── endpoints/     # Detection, Alerts, Auth, Realtime
│   │   ├── core/              # Config, Security, In-Memory DB
│   │   ├── models/            # Pydantic models
│   │   ├── schemas/           # Response schemas
│   │   └── services/          # Detection service (YOLO)
│   └── requirements.txt
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── pages/             # Dashboard, Detection, Alerts, Analytics
│   │   ├── components/        # Layout, Navbar, Sidebar
│   │   ├── services/          # API client (axios)
│   │   └── store/             # Zustand state
│   └── package.json
│
├── runs/detect/               # Trained models
│   └── weapons_yolov8_optimized_stable/
│       └── weights/best.pt    # ⭐ MAIN MODEL
│
├── uploads/                   # Temp files (snapshots, images)
├── start-system.ps1          # 🚀 Start script
└── README_FINAL.md           # 📖 This file
```

---

## 🔧 Configuration

### Backend Config
**File:** `backend/app/core/config.py`

```python
# Model Path
YOLO_MODEL_PATH = "runs/detect/weapons_yolov8_optimized_stable/weights/best.pt"

# CORS
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173"
]

# Upload Directory
UPLOAD_DIR = "uploads"
```

### Frontend Config
**File:** `frontend/.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 🎬 Video Detection - Snapshot Mode

### Cách Hoạt Động

1. **Upload video** (MP4, AVI, MOV)
2. Backend xử lý **từng frame**
3. **Khi phát hiện vũ khí:**
   - Vẽ bounding boxes (màu đỏ)
   - Chụp snapshot
   - Lưu với filename: `snapshot_frame{n}_{timestamp}.jpg`
4. **Response:** Danh sách snapshots
5. **Frontend:** Hiển thị gallery

### Response Format

```json
{
    "success": true,
    "total_frames": 900,
    "snapshots_taken": 5,
    "snapshots": [
        {
            "frame_number": 45,
            "snapshot_url": "/api/v1/detection/image/snapshot_frame45_123456.jpg",
            "weapons_count": 2,
            "timestamp": "1.5s"
        },
        {
            "frame_number": 123,
            "snapshot_url": "/api/v1/detection/image/snapshot_frame123_789012.jpg",
            "weapons_count": 1,
            "timestamp": "4.1s"
        }
    ],
    "fps": 30,
    "duration": "30.0s"
}
```

### Ưu Điểm

✅ **Nhanh hơn**: Không cần encode video output  
✅ **Tiết kiệm**: Chỉ lưu frame có vũ khí  
✅ **Dễ review**: Xem từng ảnh thay vì tua video  
✅ **Tải về dễ**: Download từng snapshot riêng  
✅ **Alert tốt**: Mỗi snapshot là bằng chứng rõ ràng  

---

## 📊 API Endpoints

### Authentication
```
POST /api/v1/auth/register - Register user
POST /api/v1/auth/login    - Login (returns JWT)
```

### Detection
```
POST /api/v1/detection/detect/image-with-pairing - Image detection
POST /api/v1/detection/detect/video              - Video detection (snapshot mode)
GET  /api/v1/detection/video/{filename}          - Serve video file
GET  /api/v1/detection/image/{filename}          - Serve image/snapshot
GET  /api/v1/detection/models                    - List available models
WS   /api/v1/realtime/ws/realtime-detect         - Realtime webcam
```

### Alerts
```
GET    /api/v1/alerts/           - List alerts (pagination, filters)
GET    /api/v1/alerts/stats      - Get stats (7 days)
GET    /api/v1/alerts/{id}       - Get alert by ID
DELETE /api/v1/alerts/{id}       - Delete alert
```

---

## 🧪 Testing

### 1. Test Image Detection
1. **Detection** → **Image Upload**
2. Upload ảnh có vũ khí
3. Xem bounding boxes
4. Check **Dashboard** → Alert mới
5. Check **Alerts** → View details

### 2. Test Video Detection
1. **Detection** → **Video Upload**
2. Upload video (~10-30s)
3. Chờ processing
4. Xem **snapshots gallery**
5. Download từng snapshot
6. Check **Alerts** → Video alert

### 3. Test Dashboard & Analytics
1. Sau khi có alerts
2. **Dashboard**: Stats cards + Recent alerts
3. **Analytics**: 4 charts render

---

## 🔍 Troubleshooting

### Backend không chạy
```powershell
# Kill Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Restart
& backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend không chạy
```powershell
# Kill Node processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# Restart
cd frontend
npm run dev
```

### ERR_CONNECTION_REFUSED
- Backend chưa chạy → Check port 8000
- Frontend chưa connect → Refresh page (Ctrl + Shift + R)

### Video processing chậm
- Dùng video ngắn (<30s) để test
- Model đã preload nên không chậm lần đầu
- Processing ~5-10 FPS

### Alerts không xuất hiện
- Check backend logs
- Verify detection có weapons
- Check In-Memory DB initialized

---

## 📈 Performance

### Metrics

**Image Detection:**
- Model load: ~0s (preloaded)
- Detection: 0.1-0.3s per image

**Video Detection (Snapshot):**
- Processing: ~5-10 FPS
- Storage: ~50-100KB per snapshot
- Much faster than video encoding

**Backend:**
- Startup: ~2-3s
- Memory: ~500MB (YOLO loaded)

---

## ⚠️ Known Issues

### 1. Realtime Webcam Canvas
- Canvas đôi khi không render
- **Workaround**: Refresh page

### 2. In-Memory Database
- Alerts mất khi restart backend
- **TODO**: Migrate to MongoDB/SQLite

### 3. Person Detection
- Tạm disabled (line 268 detection_service.py)
- **TODO**: Re-enable với proper model

---

## 🚀 Next Steps

### High Priority
- [ ] Migrate to persistent database
- [ ] Fix webcam canvas rendering
- [ ] Add video file size validation
- [ ] Progress bar for video processing

### Medium Priority
- [ ] Export alerts to CSV
- [ ] Skip frames option
- [ ] Re-enable person detection
- [ ] Confidence threshold slider

### Low Priority
- [ ] Dark/Light theme
- [ ] Multi-language (EN/VI)
- [ ] Email notifications
- [ ] Telegram bot integration

---

## 🔐 Security

- JWT tokens expire after 7 days
- Passwords hashed với bcrypt
- CORS configured for localhost
- File upload validation
- Protected API routes

---

## 📦 Dependencies

### Backend
```
fastapi==0.104.1
uvicorn==0.24.0
ultralytics==8.0.196
opencv-python==4.8.1
python-jose[cryptography]
passlib[bcrypt]
python-multipart
```

### Frontend
```
react==18.2.0
vite==5.4.21
axios==1.6.2
react-router-dom==6.20.0
zustand==4.4.7
react-hot-toast==2.4.1
chart.js==4.4.0
lucide-react==0.294.0
tailwindcss==3.3.5
```

---

## 🎓 Training (Optional)

Nếu cần train lại model:

```python
# File: src/train_optimized.py
python src/train_optimized.py

# Model sẽ được lưu vào:
# runs/detect/weapons_yolov8_optimized_stable/weights/best.pt
```

---

## 📞 Support

**Issues?**
1. Check backend terminal logs
2. Check frontend console (F12)
3. Verify model path exists
4. Check ports 8000, 3000 available
5. Clear browser cache

---

## ✅ Quick Checklist

Trước khi chạy hệ thống:

- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Model file exists at correct path
- [ ] Ports 8000, 3000 available
- [ ] Python venv activated

---

## 🎉 Summary

**Hệ thống hoàn chỉnh 90%:**
- ✅ Authentication JWT
- ✅ Image Detection với pairing
- ✅ Video Detection với snapshot mode
- ✅ Dashboard với real stats
- ✅ Analytics với 4 charts
- ✅ Alerts management
- ⚠️ Realtime webcam (minor issue)

**Model:**
- YOLOv8m trained on weapon dataset
- 44.62 MB
- Preloaded on startup
- Fast inference (~0.1-0.3s per image)

**Ready for:**
- Demo
- Testing
- Production deployment (after DB migration)

---

**Last Updated:** November 27, 2025  
**Version:** 2.0 (Snapshot Mode)

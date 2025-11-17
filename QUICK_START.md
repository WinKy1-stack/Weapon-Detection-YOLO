# 🚀 Hướng Dẫn Chạy Web App - Weapon Detection

## 🎯 Giới Thiệu

Bạn vừa có một **Web Application hoàn chỉnh** cho hệ thống phát hiện vũ khí với:
- ✅ **Backend API** (FastAPI) - Port 8000
- ✅ **Frontend UI** (React) - Port 3000  
- ✅ **Database** (MongoDB) - Port 27017
- ✅ **Cache** (Redis) - Port 6379
- ✅ **Authentication** (JWT)
- ✅ **Image Detection** (YOLO + Faster R-CNN)
- ✅ **Analytics Dashboard**

---

## 🚀 Cách 1: Chạy Nhanh với Script (Khuyến Nghị)

### Windows PowerShell:

```powershell
# Chạy local (không cần Docker)
.\start-webapp.ps1

# Hoặc chạy với Docker
.\start-docker.ps1
```

Script sẽ tự động:
1. ✅ Kiểm tra Python, Node.js, MongoDB
2. ✅ Cài đặt dependencies
3. ✅ Khởi động backend + frontend
4. ✅ Mở browser tự động

---

## 🐳 Cách 2: Chạy với Docker (Đơn Giản Nhất)

### Yêu cầu:
- Docker Desktop đã cài đặt và đang chạy

### Các bước:

```powershell
# 1. Tạo file .env cho backend
cd backend
Copy-Item .env.example .env
# Chỉnh sửa SECRET_KEY trong .env

# 2. Quay lại thư mục gốc và chạy
cd ..
docker-compose up -d

# 3. Xem logs
docker-compose logs -f

# 4. Dừng services
docker-compose down
```

### Truy cập:
- 🌐 Frontend: http://localhost:3000
- 🔌 Backend: http://localhost:8000
- 📚 API Docs: http://localhost:8000/api/v1/docs

---

## 💻 Cách 3: Chạy Manual (Development)

### A. Chạy Backend

```powershell
# 1. Cài MongoDB (nếu chưa có)
# Download từ: https://www.mongodb.com/try/download/community
# Hoặc dùng Docker:
docker run -d --name mongo -p 27017:27017 mongo:7.0

# 2. Setup Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Tạo file .env
Copy-Item .env.example .env
# Chỉnh sửa SECRET_KEY

# 4. Chạy server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend chạy tại: http://localhost:8000

### B. Chạy Frontend

```powershell
# 1. Mở terminal mới
cd frontend

# 2. Cài đặt dependencies
npm install

# 3. Chạy dev server
npm run dev
```

✅ Frontend chạy tại: http://localhost:3000

---

## 📝 Sử Dụng Web App

### 1️⃣ Đăng Ký Tài Khoản
1. Truy cập http://localhost:3000
2. Click "Create Account"
3. Nhập email, password, full name
4. Đăng ký thành công → Tự động đăng nhập

### 2️⃣ Upload Ảnh Phát Hiện
1. Vào trang "Detection"
2. Chọn model (YOLO hoặc Faster R-CNN)
3. Điều chỉnh confidence threshold
4. Upload ảnh
5. Click "Detect Weapons"
6. Xem kết quả với bounding boxes

### 3️⃣ Xem Alert History
1. Vào trang "Alerts"
2. Lọc theo weapon type hoặc danger level
3. Xem chi tiết từng alert

### 4️⃣ Xem Analytics
1. Vào trang "Analytics"
2. Xem biểu đồ thống kê
3. Chọn period (7/30/90 days)

---

## 🔧 Cấu Hình

### Backend `.env` (quan trọng!)
```env
# Security - ĐỔI KEY NÀY!
SECRET_KEY=your-super-secret-key-at-least-32-characters-long-change-this

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=weapon_detection

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Frontend `.env`
```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 🐛 Troubleshooting

### ❌ Backend không chạy được

**Lỗi: ModuleNotFoundError**
```powershell
# Cài lại dependencies
cd backend
pip install -r requirements.txt
```

**Lỗi: MongoDB connection failed**
```powershell
# Kiểm tra MongoDB đang chạy
docker ps | grep mongo
# Hoặc start MongoDB service
net start MongoDB
```

**Lỗi: Model not found**
```powershell
# Kiểm tra model weights có tồn tại
ls runs/detect/weapons_yolov8_optimized_stable/weights/best.pt
ls runs/models/fasterrcnn_quick_test.pth
```

### ❌ Frontend không chạy được

**Lỗi: npm install failed**
```powershell
# Xóa cache và cài lại
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

**Lỗi: Cannot connect to API**
- Kiểm tra backend đang chạy trên port 8000
- Kiểm tra `frontend/.env` có `VITE_API_URL` đúng
- Mở http://localhost:8000/api/v1/docs để test API

### ❌ Docker issues

**Lỗi: Port already in use**
```powershell
# Dừng services cũ
docker-compose down
# Kiểm tra port đang dùng
netstat -ano | findstr "8000"
netstat -ano | findstr "3000"
```

---

## 📚 API Documentation

Khi backend chạy, truy cập:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Endpoints chính:

#### 🔐 Authentication
- `POST /api/v1/auth/register` - Đăng ký
- `POST /api/v1/auth/login` - Đăng nhập
- `GET /api/v1/auth/me` - Lấy thông tin user

#### 🎯 Detection
- `POST /api/v1/detection/detect/image` - Upload ảnh và detect
- `GET /api/v1/detection/models` - Danh sách models

#### 🚨 Alerts
- `GET /api/v1/alerts/` - Lấy danh sách alerts
- `GET /api/v1/alerts/stats` - Thống kê alerts
- `GET /api/v1/alerts/{id}` - Chi tiết alert
- `DELETE /api/v1/alerts/{id}` - Xóa alert

---

## 📁 Cấu Trúc Project

```
weapon-detection/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Config, security, database
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── main.py      # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/             # React Frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Pages
│   │   ├── services/    # API calls
│   │   └── store/       # State management
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml    # Docker orchestration
├── start-webapp.ps1      # Quick start script
├── start-docker.ps1      # Docker start script
└── WEB_APP_README.md     # Full documentation
```

---

## 🎨 Screenshots (Sẽ có sau khi chạy)

### Login Page
- Modern dark theme
- Email + password authentication

### Dashboard
- Total alerts
- Weapon distribution chart
- Recent alerts
- Daily trends

### Detection Page
- Model selection (YOLO / Faster R-CNN)
- Confidence slider
- Image upload
- Real-time detection results

### Alerts History
- Filter by weapon type
- Filter by danger level
- Alert timeline
- Image snapshots

### Analytics
- Pie chart: Weapon distribution
- Bar chart: Danger levels
- Line chart: Daily trends
- Period selection

---

## 🚀 Next Steps

Sau khi web app chạy thành công:

### 1. Testing
- [ ] Đăng ký account mới
- [ ] Upload test images
- [ ] Kiểm tra alerts được lưu vào DB
- [ ] Test analytics charts

### 2. Customization
- [ ] Thay đổi logo và branding
- [ ] Thêm ngôn ngữ tiếng Việt
- [ ] Custom color theme
- [ ] Thêm features mới

### 3. Production Deployment
- [ ] Setup domain name
- [ ] Configure SSL/HTTPS
- [ ] Deploy lên cloud (AWS/Azure/Vercel)
- [ ] Setup CI/CD pipeline
- [ ] Configure backups
- [ ] Setup monitoring

---

## 💡 Tips

1. **Development**:
   - Dùng `--reload` cho backend để auto-restart
   - Frontend tự động hot-reload khi sửa code
   - Dùng React DevTools extension

2. **Performance**:
   - YOLO nhanh hơn nhưng Faster R-CNN chính xác hơn
   - Giảm confidence threshold để detect nhiều hơn
   - Tăng threshold để giảm false positives

3. **Security**:
   - ĐỔI SECRET_KEY trong production!
   - Không commit .env file lên Git
   - Sử dụng HTTPS trong production
   - Setup rate limiting cho API

---

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra logs: `docker-compose logs -f`
2. Xem API docs: http://localhost:8000/api/v1/docs
3. Check terminal output cho errors
4. Đảm bảo models đã được train

---

## ✨ Tính Năng Nổi Bật

✅ **Full-stack**: Backend + Frontend + Database  
✅ **Authentication**: JWT tokens, secure login  
✅ **Dual Models**: YOLO và Faster R-CNN  
✅ **Real-time**: WebSocket support (có thể thêm)  
✅ **Analytics**: Charts và statistics  
✅ **Responsive**: Chạy trên mobile và desktop  
✅ **Docker**: Easy deployment  
✅ **REST API**: Well-documented với Swagger  
✅ **Modern UI**: Tailwind CSS, dark theme  

---

**🎉 Chúc mừng! Bạn đã có một Web App hoàn chỉnh! 🎉**

Hãy chạy thử và báo lại kết quả nhé! 😊

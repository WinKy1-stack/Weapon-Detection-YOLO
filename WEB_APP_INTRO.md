# 🎉 WEB APPLICATION ĐÃ SẴN SÀNG!

## 🚀 Chạy Ngay Web App

Dự án đã được nâng cấp với **Full-Stack Web Application**!

### ⚡ Quick Start - 3 Cách

#### 1. Script Tự Động (Dễ Nhất)
```powershell
# Chạy local
.\start-webapp.ps1

# Hoặc chạy với Docker
.\start-docker.ps1
```

#### 2. Docker Compose
```powershell
docker-compose up -d
```

#### 3. Manual
```powershell
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend (terminal mới)
cd frontend
npm install
npm run dev
```

### 🌐 Truy Cập

- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs

---

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Hướng dẫn chi tiết chạy web app
- **[WEB_APP_README.md](WEB_APP_README.md)** - Full documentation web app
- **[README.md](README.md)** - Documentation hệ thống cũ (Streamlit)

---

## 🎯 Tính Năng Web App

### Frontend (React)
✅ Modern UI với Tailwind CSS  
✅ Authentication (Login/Register)  
✅ Image Upload & Detection  
✅ Alert History với filters  
✅ Analytics Dashboard với charts  
✅ Responsive design  

### Backend (FastAPI)
✅ REST API với Swagger docs  
✅ JWT Authentication  
✅ MongoDB integration  
✅ YOLO + Faster R-CNN detection  
✅ Alert management  
✅ Statistics & analytics  

### Infrastructure
✅ Docker containerization  
✅ MongoDB database  
✅ Redis caching  
✅ CORS configured  

---

## 🎨 Screenshots

### Dashboard
![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Preview)

### Detection
![Detection](https://via.placeholder.com/800x400?text=Detection+Page)

### Alerts
![Alerts](https://via.placeholder.com/800x400?text=Alerts+History)

---

## 🔥 What's New

### Web Application
- ✨ **Modern Web Interface** thay cho Streamlit
- 🔐 **User Authentication** với JWT tokens
- 📊 **Interactive Charts** với Recharts
- 🎨 **Dark Theme UI** với Tailwind CSS
- 🐳 **Docker Support** để deploy dễ dàng
- 📡 **REST API** hoàn chỉnh với documentation

### Enhanced Features
- ⚡ **Faster Performance** với async processing
- 🔄 **Better State Management** với Zustand
- 📱 **Mobile Responsive** design
- 🌐 **Multi-user Support** với database
- 📈 **Advanced Analytics** với nhiều charts

---

## 📦 Tech Stack

### Backend
- FastAPI
- PyTorch
- Ultralytics YOLO
- MongoDB (Motor)
- Redis
- Python-JOSE (JWT)

### Frontend
- React 18
- Vite
- Tailwind CSS
- Zustand
- Axios
- Recharts
- React Router

### DevOps
- Docker
- Docker Compose
- MongoDB
- Redis

---

## 🧪 Testing

Test API:
```powershell
.\test-api.ps1
```

Test Frontend:
```powershell
cd frontend
npm run build    # Production build
npm run preview  # Preview build
```

---

## 📞 Support

Gặp vấn đề? Check:
1. [QUICK_START.md](QUICK_START.md) - Troubleshooting section
2. API Docs: http://localhost:8000/api/v1/docs
3. Logs: `docker-compose logs -f`

---

**🎊 Enjoy your new Web Application! 🎊**

---

> **Note**: README gốc của hệ thống Streamlit vẫn có trong file này ở bên dưới ↓

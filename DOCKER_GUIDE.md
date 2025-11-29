# 🐳 Docker Quick Start

## 📋 Yêu Cầu

1. **Cài Docker Desktop**: https://www.docker.com/products/docker-desktop
2. Khởi động Docker Desktop
3. Đảm bảo ports 3000 và 8000 chưa bị chiếm

## 🚀 Chạy 1 Lệnh Duy Nhất

### Option 1: Sử dụng Batch File (Khuyến nghị)

```cmd
START-DOCKER.bat
```

**Double-click vào `START-DOCKER.bat`** → Hệ thống tự động build và start!

### Option 2: Sử dụng Docker Compose trực tiếp

```bash
# Build và start
docker-compose up -d --build

# Xem logs
docker-compose logs -f

# Stop
docker-compose down
```

## ⏱️ Lần Đầu Tiên

**Build images:** ~5-10 phút (chỉ lần đầu)
- Backend: Download Python packages + YOLO
- Frontend: npm install

**Lần sau:** <30 giây (containers đã có sẵn)

## 🌐 Truy Cập

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs

**Login:** `son@gmail.com` / `123456`

## 🛑 Dừng Hệ Thống

### Option 1: Batch File
```cmd
STOP-DOCKER.bat
```

### Option 2: Command
```bash
docker-compose down
```

## 📊 Quản Lý

### Xem logs
```bash
# All services
docker-compose logs -f

# Chỉ backend
docker-compose logs -f backend

# Chỉ frontend
docker-compose logs -f frontend
```

### Kiểm tra containers
```bash
docker-compose ps
```

### Restart services
```bash
docker-compose restart
```

### Rebuild sau khi sửa code
```bash
docker-compose up -d --build
```

## 🔧 Troubleshooting

### Docker Desktop không chạy
```
Error: Cannot connect to Docker daemon
→ Solution: Mở Docker Desktop
```

### Port đã bị chiếm
```
Error: port 3000 already in use
→ Solution: Stop app đang chạy trên port đó
→ Or: Đổi port trong docker-compose.yml
```

### Build lỗi
```bash
# Clean và rebuild
docker-compose down
docker system prune -a
docker-compose up -d --build
```

### Container không start
```bash
# Xem logs chi tiết
docker-compose logs backend
docker-compose logs frontend
```

## 📦 Docker Images Size

- **Backend**: ~2GB (Python + YOLO + dependencies)
- **Frontend**: ~500MB (Node + packages)
- **Total**: ~2.5GB

## ✅ Ưu Điểm Docker

1. ✨ **1 lệnh duy nhất** để start tất cả
2. 🔒 **Isolated environment** - không ảnh hưởng hệ thống
3. 🚀 **Dễ deploy** - chạy trên bất kỳ máy nào có Docker
4. 🔄 **Consistent** - luôn chạy giống nhau
5. 🧹 **Clean uninstall** - xóa là sạch

## 🆚 So Sánh

| Method | Lệnh | Thời gian | Độ phức tạp |
|--------|------|-----------|-------------|
| **Manual** | 2 terminals | ~1 min | ⭐⭐⭐ |
| **START.bat** | 1 file | ~1 min | ⭐⭐ |
| **Docker** | 1 file | ~30s | ⭐ |

## 🎯 Production

Để deploy lên server:

```bash
# Copy source code
git clone <repo>

# Start với Docker
docker-compose up -d --build

# Done!
```

---

**🐳 Docker = Chạy 1 lệnh → Mọi thứ tự động!**

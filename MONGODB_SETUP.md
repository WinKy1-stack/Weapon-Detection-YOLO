# MongoDB Setup Guide for Weapon Detection System

## Cài Đặt MongoDB trên Windows

### Bước 1: Download MongoDB Community Edition

1. Truy cập: https://www.mongodb.com/try/download/community
2. Chọn:
   - Version: Latest (7.0 hoặc mới hơn)
   - Platform: Windows
   - Package: MSI
3. Click **Download**

### Bước 2: Cài Đặt MongoDB

1. Chạy file `.msi` vừa download
2. Chọn **Complete** installation
3. Tích chọn **Install MongoDB as a Service**
4. Tích chọn **Install MongoDB Compass** (GUI tool)
5. Click **Install**

### Bước 3: Kiểm Tra MongoDB Đã Chạy

Mở PowerShell và chạy:
```powershell
Get-Service MongoDB
```

Nếu thấy `Status: Running` là OK!

### Bước 4: Tạo Database và Collections

#### Option 1: Sử Dụng MongoDB Compass (GUI)

1. Mở **MongoDB Compass**
2. Connect đến `mongodb://localhost:27017`
3. Click **Create Database**:
   - Database Name: `weapon_detection`
   - Collection Name: `users`
4. Tạo thêm collection `alerts`

#### Option 2: Sử Dụng Command Line

```powershell
# Mở mongo shell
mongosh

# Tạo database và collections
use weapon_detection
db.createCollection("users")
db.createCollection("alerts")

# Tạo indexes (optional nhưng recommended)
db.users.createIndex({ "email": 1 }, { unique: true })
db.alerts.createIndex({ "timestamp": -1 })
db.alerts.createIndex({ "weapon_class": 1 })

# Kiểm tra
show collections

# Exit
exit
```

### Bước 5: Configure Backend

File `backend/app/core/config.py` đã được config sẵn:

```python
MONGODB_URL = "mongodb://localhost:27017"
MONGODB_DB_NAME = "weapon_detection"
```

Không cần thay đổi gì nếu MongoDB chạy local!

### Bước 6: Test Connection

1. Khởi động backend:
```powershell
cd C:\Workspace\weapon-detection
& backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. Kiểm tra log, phải thấy:
```
✅ Connected to MongoDB: weapon_detection
✅ Database indexes created
```

---

## Troubleshooting

### MongoDB Service Không Chạy

```powershell
# Start service
Start-Service MongoDB

# Hoặc restart
Restart-Service MongoDB
```

### Connection Refused

1. Kiểm tra MongoDB đang chạy:
```powershell
Get-Service MongoDB
```

2. Kiểm tra port 27017:
```powershell
Get-NetTCPConnection -LocalPort 27017 -State Listen
```

3. Nếu không thấy, start lại MongoDB service

### Kiểm Tra Database Có Dữ Liệu

```powershell
mongosh
use weapon_detection
db.users.countDocuments()
db.alerts.countDocuments()
```

---

## Production Setup (Nâng Cao)

Cho khóa luận tốt nghiệp, nên:

### 1. Enable Authentication

```javascript
// Tạo admin user
use admin
db.createUser({
  user: "admin",
  pwd: "your_secure_password",
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
})

// Tạo user cho database
use weapon_detection
db.createUser({
  user: "weapon_user",
  pwd: "secure_password_here",
  roles: [{ role: "readWrite", db: "weapon_detection" }]
})
```

Update `config.py`:
```python
MONGODB_URL = "mongodb://weapon_user:secure_password_here@localhost:27017/weapon_detection"
```

### 2. Backup Database

```powershell
# Backup toàn bộ database
mongodump --db weapon_detection --out C:\backup\mongodb

# Restore
mongorestore --db weapon_detection C:\backup\mongodb\weapon_detection
```

### 3. Export Data for Report

```powershell
# Export users collection to JSON
mongoexport --db weapon_detection --collection users --out users.json --pretty

# Export alerts
mongoexport --db weapon_detection --collection alerts --out alerts.json --pretty
```

---

## Database Schema

### Users Collection

```json
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "full_name": "Nguyen Van A",
  "hashed_password": "...",
  "is_active": true,
  "is_admin": false,
  "created_at": ISODate("2024-...")
}
```

### Alerts Collection

```json
{
  "_id": ObjectId("..."),
  "weapon_class": "pistol",
  "confidence": 0.95,
  "danger_level": "high",
  "person_held": true,
  "snapshot_path": "/api/v1/detection/image/...",
  "location": "Camera 1",
  "metadata": {
    "source": "realtime",
    "model": "yolov8"
  },
  "timestamp": ISODate("2024-..."),
  "acknowledged": false
}
```

---

## Kiểm Tra Hoạt Động

### Test Registration

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "full_name": "Test User"
  }'
```

### Test Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=test@example.com&password=test123"
```

### Xem Dữ Liệu Trong MongoDB

```javascript
// Mở mongosh
mongosh

use weapon_detection

// Xem users
db.users.find().pretty()

// Xem alerts
db.alerts.find().sort({ timestamp: -1 }).limit(10).pretty()

// Stats
db.users.countDocuments()
db.alerts.countDocuments()
```

---

✅ **Hoàn thành!** MongoDB đã được setup và kết nối với backend!

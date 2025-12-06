# 🚨 Telegram Alert - Quick Start

## ⚡ Cấu hình nhanh (5 phút)

### 1️⃣ Lấy Bot Token
```
1. Mở Telegram → Tìm @BotFather
2. Gửi: /newbot
3. Đặt tên: Weapon Detection Alert Bot
4. Username: weapon_detection_alert_bot
5. Copy token: 123456789:ABCdefGHI...
```

### 2️⃣ Lấy Chat ID
```
1. Tìm @userinfobot
2. Start conversation
3. Copy số "Id: 123456789"
```

### 3️⃣ Cấu hình Backend
```bash
# Mở file backend/.env
notepad backend\.env

# Thêm 2 dòng này (thay bằng thông tin của bạn):
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...
TELEGRAM_CHAT_ID=123456789
```

### 4️⃣ Test
```bash
cd backend
.\venv\Scripts\Activate.ps1
python test_telegram_alert.py
```

✅ Nếu nhận được tin nhắn Telegram → **Thành công!**

---

## 🚀 Chạy hệ thống

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend  
cd frontend
npm run dev
```

Mở http://localhost:3001 → Detection → Webcam → Bắt đầu phát hiện

**Alert sẽ tự động gửi khi phát hiện vũ khí!** 📱

---

## 🔧 Tùy chỉnh

### Thời gian cooldown
```python
# backend/app/services/alert_service.py
self.cooldown_seconds = 10  # Đổi thành 5, 20, 30, 60...
```

### Nội dung message
```python
# backend/app/api/endpoints/realtime.py
message = f"Detected {weapon_count} weapon(s)\n"
# ← Thêm custom text ở đây
```

---

## 📖 Hướng dẫn chi tiết

Xem file: **TELEGRAM_SETUP.md**

---

## ❓ Troubleshooting

| Lỗi | Giải pháp |
|-----|-----------|
| 401 Unauthorized | Token sai → Check @BotFather |
| 400 Bad Request | Chat ID sai hoặc chưa /start bot |
| Không nhận alert | Đang cooldown 10s hoặc backend chưa restart |

---

**✨ Telegram Alert đã sẵn sàng!**

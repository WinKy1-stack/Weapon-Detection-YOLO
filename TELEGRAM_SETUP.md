# 📱 Hướng dẫn cấu hình Telegram Alert

## 🎯 Tổng quan

Hệ thống Telegram Alert sẽ tự động gửi thông báo khi phát hiện vũ khí qua:
- **Ảnh snapshot** với bounding boxes
- **Thông tin chi tiết** về các vũ khí phát hiện được
- **Timestamp** và camera ID
- **Non-blocking** - không làm chậm video stream

---

## 📋 Yêu cầu

- Tài khoản Telegram
- Bot Token từ @BotFather
- Chat ID của bạn hoặc group

---

## 🔧 Bước 1: Tạo Telegram Bot

### 1.1. Mở Telegram và tìm @BotFather

- Mở app Telegram
- Tìm kiếm: `@BotFather`
- Chọn bot chính thức (có dấu tick xanh)

### 1.2. Tạo bot mới

Gửi các lệnh sau:

```
/newbot
```

BotFather sẽ hỏi tên bot:
```
Weapon Detection Alert Bot
```

Sau đó hỏi username (phải kết thúc bằng "bot"):
```
weapon_detection_alert_bot
```

### 1.3. Lưu Bot Token

BotFather sẽ trả về token dạng:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

**⚠️ QUAN TRỌNG:** Giữ token này bí mật!

---

## 🔧 Bước 2: Lấy Chat ID

### 2.1. Tìm @userinfobot

- Tìm kiếm: `@userinfobot`
- Start conversation

### 2.2. Bot sẽ trả về thông tin

Bạn sẽ nhận được message dạng:
```
Id: 123456789
First name: Your Name
...
```

**Lưu số `Id`** - đây là Chat ID của bạn.

### 2.3. (Tùy chọn) Chat ID cho Group

Nếu muốn gửi alert vào group:

1. Thêm bot vào group
2. Gửi một tin nhắn trong group
3. Truy cập: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Tìm `"chat":{"id":-1001234567890,...}`
5. Lưu số ID (có dấu trừ cho group)

---

## 🔧 Bước 3: Cấu hình Backend

### 3.1. Mở file `.env`

```bash
cd backend
notepad .env
```

### 3.2. Thêm thông tin Telegram

```env
# Telegram Alert Service
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

**Thay thế:**
- `123456789:ABC...` bằng bot token của bạn
- `123456789` bằng chat ID của bạn

### 3.3. Lưu file

Lưu file `.env` và đóng lại.

---

## 🧪 Bước 4: Test Telegram Alert

### 4.1. Activate virtual environment

```bash
cd backend
.\venv\Scripts\Activate.ps1
```

### 4.2. Chạy test script

```bash
python test_telegram_alert.py
```

### 4.3. Kiểm tra Telegram

Bạn sẽ nhận được message với:
- ✅ Ảnh test với bounding box
- ✅ Thông tin chi tiết
- ✅ Danh sách vũ khí phát hiện

**Nếu thành công** → Cấu hình đúng! ✅
**Nếu thất bại** → Xem mục Troubleshooting bên dưới

---

## 🚀 Bước 5: Chạy hệ thống

### 5.1. Start backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Bạn sẽ thấy:
```
✅ Telegram Alert Service initialized (chat_id: 123456789)
```

### 5.2. Start frontend

```bash
cd frontend
npm run dev
```

### 5.3. Test real-time detection

1. Mở http://localhost:3001
2. Vào trang **Detection**
3. Chọn **Webcam Realtime**
4. Click **"Bắt đầu phát hiện"**
5. Đưa vũ khí vào camera
6. **Kiểm tra Telegram** - sẽ nhận alert sau 1-2 giây

---

## ⚙️ Cấu hình nâng cao

### Thay đổi thời gian cooldown

Mở `backend/app/services/alert_service.py`:

```python
class TelegramAlert:
    def __init__(self):
        self.cooldown_seconds = 10  # ← Thay đổi số giây ở đây
```

**Gợi ý:**
- **5 giây**: Test nhanh
- **10-20 giây**: Sử dụng bình thường
- **30-60 giây**: Production (giảm spam)

### Tùy chỉnh message format

Sửa trong `backend/app/api/endpoints/realtime.py`:

```python
def send_alert_background(client_id: str, frame: np.ndarray, detections: list):
    message = f"Detected {weapon_count} weapon(s)\n"
    message += f"Types: {', '.join(unique_weapons)}"
    # ← Thêm nội dung tùy chỉnh ở đây
```

---

## 🔍 Troubleshooting

### ❌ "Telegram not configured"

**Nguyên nhân:** Chưa set TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID

**Giải pháp:**
1. Kiểm tra file `.env` có tồn tại
2. Kiểm tra token và chat ID đã đúng format
3. Restart backend server

---

### ❌ "401 Unauthorized"

**Nguyên nhân:** Bot token sai

**Giải pháp:**
1. Kiểm tra lại token từ @BotFather
2. Không có khoảng trắng thừa trong `.env`
3. Token phải có dạng: `123456:ABC...`

**Test token:**
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

---

### ❌ "400 Bad Request - chat not found"

**Nguyên nhân:** Chat ID sai hoặc bot chưa được start

**Giải pháp:**
1. Mở bot trong Telegram
2. Click **"Start"** hoặc gửi `/start`
3. Kiểm tra lại Chat ID từ @userinfobot
4. Chat ID không được có khoảng trắng

---

### ❌ "Telegram connection error"

**Nguyên nhân:** Không có internet hoặc Telegram bị chặn

**Giải pháp:**
1. Kiểm tra kết nối internet
2. Test: `ping api.telegram.org`
3. Nếu bị chặn, dùng VPN

---

### ❌ Alert không gửi dù có detection

**Debug:**

Thêm log trong `backend/app/api/endpoints/realtime.py`:

```python
# Sau dòng: if len(detections) > 0 and can_send_alert(client_id):
print(f"🔔 Alert check: {len(detections)} weapons, can_send: {can_send_alert(client_id)}")
```

**Nguyên nhân có thể:**
- Đang trong cooldown period (10 giây)
- Detections bị ROI filter hết
- Backend chưa restart sau khi config

---

### ❌ "Image encoding failed"

**Nguyên nhân:** Frame format không đúng

**Giải pháp:**

Thêm validation trong `alert_service.py`:

```python
# Trong _send_alert_worker, trước cv2.imencode:
if len(image.shape) != 3:
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
```

---

## 📊 Performance

### Metrics

| Hoạt động | Thời gian | Impact |
|-----------|-----------|--------|
| Frame processing | 30-50ms | Không đổi |
| Alert thread start | <1ms | Negligible |
| Telegram API call | 200-500ms | Background thread |
| Image encoding | 10-30ms | Background thread |

**✅ Telegram alert chạy hoàn toàn background, không ảnh hưởng FPS!**

### Monitoring

Check terminal output:

```
✅ Telegram Alert Service initialized (chat_id: 123456789)
🔔 Alert thread started for ws_140234567_1701234567
✅ Telegram alert sent: ws_140234567_1701234567 (2 weapons)
```

---

## 🔒 Security Best Practices

### 1. Bảo vệ credentials

```bash
# ✅ Đúng: Dùng .env file
TELEGRAM_BOT_TOKEN=abc123

# ❌ Sai: Hardcode trong code
bot_token = "abc123"
```

### 2. Gitignore

Đảm bảo `.env` trong `.gitignore`:

```gitignore
# .gitignore
.env
*.env
backend/.env
```

### 3. Không commit credentials

```bash
# Kiểm tra trước khi commit
git status
git diff

# Nếu đã commit nhầm
git reset --soft HEAD~1
```

### 4. Sử dụng environment variables

Production deployment:

```bash
# Heroku
heroku config:set TELEGRAM_BOT_TOKEN=abc123

# Docker
docker run -e TELEGRAM_BOT_TOKEN=abc123 ...

# Kubernetes
kubectl create secret generic telegram-creds \
  --from-literal=token=abc123 \
  --from-literal=chat_id=123456
```

---

## 🎉 Hoàn thành!

Bây giờ hệ thống sẽ tự động gửi Telegram alert khi phát hiện vũ khí!

### Next Steps

- ✅ Test với nhiều loại vũ khí
- ✅ Điều chỉnh cooldown phù hợp
- ✅ Thêm alert cho group chat (nếu muốn)
- ✅ Monitor performance trong production

---

## 📚 Tài liệu thêm

- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [BotFather Guide](https://core.telegram.org/bots#6-botfather)
- [Python Requests Library](https://requests.readthedocs.io/)

---

**Có câu hỏi?** Kiểm tra phần Troubleshooting hoặc xem logs trong terminal!

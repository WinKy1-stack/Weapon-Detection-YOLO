# Cập Nhật: Crop Ảnh Cảnh Báo Telegram

## Mô Tả
Theo yêu cầu của thầy, hệ thống cảnh báo đã được cập nhật để gửi ảnh đã được crop, chỉ hiển thị vùng chứa người và vũ khí với khuôn mặt người cầm vũ khí rõ ràng, thay vì gửi toàn bộ frame.

## Các Thay Đổi

### 1. `src/alert_system/notifier.py`
**Hàm `save_snapshot()` đã được cập nhật:**

```python
def save_snapshot(frame, weapon_class, person_box=None, weapon_box=None):
```

**Tính năng mới:**
- Nhận thêm 2 tham số: `person_box` và `weapon_box` (bounding boxes)
- Tính toán bounding box tổng hợp chứa cả người và vũ khí:
  ```python
  x1 = min(person_box[0], weapon_box[0])
  y1 = min(person_box[1], weapon_box[1])
  x2 = max(person_box[2], weapon_box[2])
  y2 = max(person_box[3], weapon_box[3])
  ```
- Thêm margin 15% xung quanh để có context:
  ```python
  margin_x = int((x2 - x1) * 0.15)
  margin_y = int((y2 - y1) * 0.15)
  ```
- Crop frame theo vùng đã tính toán
- Vẽ annotations lên frame đã crop:
  - **Box màu xanh lá**: Người (Person)
  - **Box màu đỏ**: Vũ khí (tên loại vũ khí)
  - **Đường màu vàng**: Kết nối giữa trung tâm người và vũ khí
  - **Text "WEAPON DETECTED!"**: Cảnh báo ở góc trên bên trái
- Lưu frame đã crop thay vì frame gốc

**Kết quả:**
Ảnh Telegram sẽ chỉ hiển thị vùng quan trọng với khuôn mặt người và vũ khí, dễ nhận diện hơn.

---

### 2. `src/alert_system/alert_manager.py`

**Hàm `trigger_alert()` đã được cập nhật:**

```python
def trigger_alert(frame, weapon_class, conf, distance, status, person_box=None, weapon_box=None):
```

**Tính năng mới:**
- Nhận thêm 2 tham số: `person_box` và `weapon_box`
- Đẩy cả bounding boxes vào alert queue:
  ```python
  alert_queue.put_nowait((frame.copy(), weapon_class, conf, distance, status, person_box, weapon_box))
  ```

**Hàm `alert_worker()` đã được cập nhật:**

```python
frame, weapon_class, conf, distance, status, person_box, weapon_box = task
```

**Tính năng mới:**
- Unpack thêm `person_box` và `weapon_box` từ task tuple
- Truyền bounding boxes sang `save_snapshot()`:
  ```python
  img_path, timestamp = save_snapshot(frame, weapon_class, person_box, weapon_box)
  ```

---

### 3. `src/dashboard_pair_analytics.py`

**Detection loop đã được cập nhật:**

**Thay đổi chính:**
```python
# Chuẩn bị bounding boxes cho alert
person_box = list(map(int, nearest_person)) if nearest_person else None
weapon_box = [wx1, wy1, wx2, wy2]
trigger_alert(frame, weapon_name, conf, min_dist / 100, status, person_box, weapon_box)
```

**Tính năng mới:**
- Extract bounding box của `nearest_person` (người gần vũ khí nhất)
- Extract bounding box của vũ khí hiện tại
- Truyền cả 2 boxes vào `trigger_alert()`

---

## Luồng Hoạt Động Mới

```
1. Dashboard phát hiện vũ khí + người
   └─> Tìm người gần nhất với vũ khí
   └─> Extract person_box và weapon_box

2. trigger_alert(frame, weapon_class, conf, distance, status, person_box, weapon_box)
   └─> Đẩy vào alert_queue với đầy đủ thông tin

3. alert_worker() xử lý task
   └─> Unpack person_box và weapon_box
   └─> Gọi save_snapshot(frame, weapon_class, person_box, weapon_box)

4. save_snapshot() crop và annotate
   └─> Tính toán bounding box tổng hợp
   └─> Thêm margin 15%
   └─> Crop frame
   └─> Vẽ boxes, line, text
   └─> Lưu ảnh đã crop

5. send_telegram_alert() gửi ảnh đã crop lên Telegram
```

---

## Lợi Ích

✅ **Dễ nhận diện:** Ảnh chỉ hiển thị vùng quan trọng (người + vũ khí)  
✅ **Thấy rõ mặt:** Margin 15% đảm bảo khuôn mặt người cầm vũ khí được hiển thị đầy đủ  
✅ **Annotations rõ ràng:** Boxes màu sắc, nhãn, đường kết nối giúp hiểu ngay tình huống  
✅ **Giảm dung lượng:** Ảnh nhỏ hơn, gửi Telegram nhanh hơn  
✅ **Tuân thủ yêu cầu:** Đáp ứng yêu cầu của thầy về việc crop ảnh cảnh báo

---

## Testing

Để kiểm tra tính năng mới:

1. **Chạy dashboard:**
   ```bash
   streamlit run src/dashboard_pair_analytics.py
   ```

2. **Chọn Tab "🔴 Detection" và bật camera hoặc upload video**

3. **Khi phát hiện vũ khí:**
   - Hệ thống sẽ tự động crop ảnh vùng người + vũ khí
   - Gửi lên Telegram với annotations đầy đủ
   - Kiểm tra Telegram để xem ảnh đã crop

4. **Xác nhận:**
   - ✓ Ảnh chỉ hiển thị vùng người + vũ khí
   - ✓ Khuôn mặt người cầm vũ khí hiển thị rõ
   - ✓ Boxes và labels được vẽ chính xác
   - ✓ Đường kết nối giữa người và vũ khí rõ ràng

---

## Ghi Chú

- Nếu không có thông tin `person_box` hoặc `weapon_box`, hệ thống sẽ lưu toàn bộ frame như cũ (backward compatible)
- Margin 15% có thể điều chỉnh trong `notifier.py` nếu cần thêm/bớt context
- Ảnh được lưu trong `runs/alerts_snapshots/` với timestamp

---

**Cập nhật:** 2025-01-XX  
**Status:** ✅ Hoàn thành và sẵn sàng testing

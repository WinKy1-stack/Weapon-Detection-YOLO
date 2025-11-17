import cv2
import time
import threading
import queue
from datetime import datetime

from .danger_evaluator import get_danger_level
from .notifier import save_snapshot, send_telegram_alert
from src.database.mongo_client import save_alert

# =========================================
# FAST ASYNC ALERT SYSTEM
# =========================================
alert_queue = queue.Queue(maxsize=100)
_last_alert_time = {}
COOLDOWN = 2  # giây, chỉ để tránh spam cùng loại hung khí
RUNNING = True


# =========== BACKGROUND THREAD ===========
def alert_worker():
    """Xử lý các cảnh báo trong queue mà không làm lag video."""
    while RUNNING:
        try:
            task = alert_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        try:
            frame, weapon_class, conf, distance, status = task
            danger = get_danger_level(weapon_class, conf, distance)
            img_path, timestamp = save_snapshot(frame, weapon_class)

            # Tạo dữ liệu cảnh báo (store timestamp as a proper datetime for sorting)
            alert_data = {
                "timestamp": datetime.utcnow(),
                "weapon_class": weapon_class,
                "confidence": round(conf, 2),
                "distance": round(distance, 2) if distance else None,
                "status": status,
                "danger_level": danger,
                "image_path": img_path,
            }

            # Lưu DB + Gửi Telegram cho TẤT CẢ phát hiện vũ khí
            # Không cần kiểm tra mức độ nguy hiểm, gửi hết để theo dõi
            try:
                threading.Thread(target=save_alert, args=(alert_data,), daemon=True).start()
            except Exception as e:
                print(f"[DB SAVE THREAD ERROR] {e}")

            try:
                threading.Thread(target=send_telegram_alert, args=(img_path, alert_data), daemon=True).start()
                # In thêm log đặc biệt nếu nguy hiểm cao
                if "NGUY HIỂM CAO" in danger:
                    print(f"[❗CẢNH BÁO❗] Phát hiện {weapon_class} - Khoảng cách: {distance}m - Độ tin cậy: {conf:.0%}")
            except Exception as e:
                print(f"[TELEGRAM THREAD ERROR] {e}")

        except Exception as e:
            print(f"[ALERT WORKER ERROR] {e}")
        finally:
            alert_queue.task_done()


# =========== STARTUP ===========
def start_alert_worker():
    """Khởi động luồng nền (1 lần duy nhất, an toàn cho Streamlit)."""
    import streamlit as st
    if "alert_worker_started" not in st.session_state:
        thread = threading.Thread(target=alert_worker, daemon=True)
        thread.start()
        st.session_state.alert_worker_started = True
        print("[✅ Fast Async Alert Worker Started]")


# =========== MAIN TRIGGER ===========
def trigger_alert(frame, weapon_class, conf, distance, status):
    """Thêm frame vào hàng đợi xử lý cảnh báo (gần như tức thời)."""
    now = time.time()
    global _last_alert_time

    # Chặn spam cùng loại hung khí trong 2s
    if weapon_class in _last_alert_time and now - _last_alert_time[weapon_class] < COOLDOWN:
        return

    _last_alert_time[weapon_class] = now

    # Đẩy frame vào queue (nếu đầy, bỏ frame cũ)
    if alert_queue.full():
        try:
            alert_queue.get_nowait()
        except queue.Empty:
            pass

    alert_queue.put_nowait((frame.copy(), weapon_class, conf, distance, status))

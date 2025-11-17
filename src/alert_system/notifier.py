import os
import cv2
import requests
import numpy as np
from datetime import datetime

# Prefer environment variables for tokens; fall back to the value in code if present
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8570133185:AAENKL-AItf6bzpMQ_lnuBfpTiGuc0TZ7ws")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5444586273")

SNAPSHOT_DIR = "runs/alerts_snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

def save_snapshot(frame, weapon_class, person_box=None, weapon_box=None):
    """
    Lưu frame phát hiện vào thư mục snapshot.
    Nếu có thông tin person_box và weapon_box, sẽ crop vùng chứa cả người và vũ khí.
    
    Args:
        frame: Frame gốc
        weapon_class: Loại vũ khí
        person_box: [x1, y1, x2, y2] của người (optional)
        weapon_box: [x1, y1, x2, y2] của vũ khí (optional)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nếu có thông tin bounding box, crop vùng chứa người + vũ khí
    if person_box is not None and weapon_box is not None:
        h, w = frame.shape[:2]
        
        # Tìm bounding box bao toàn bộ người + vũ khí
        x1 = int(min(person_box[0], weapon_box[0]))
        y1 = int(min(person_box[1], weapon_box[1]))
        x2 = int(max(person_box[2], weapon_box[2]))
        y2 = int(max(person_box[3], weapon_box[3]))
        
        # Thêm margin 15% để ảnh đẹp hơn và có context
        margin_x = int((x2 - x1) * 0.15)
        margin_y = int((y2 - y1) * 0.15)
        
        x1 = max(0, x1 - margin_x)
        y1 = max(0, y1 - margin_y)
        x2 = min(w, x2 + margin_x)
        y2 = min(h, y2 + margin_y)
        
        # Crop frame
        cropped_frame = frame[y1:y2, x1:x2].copy()
        
        # Vẽ bounding boxes lên frame đã crop (điều chỉnh tọa độ)
        # Tọa độ mới = tọa độ cũ - offset
        person_box_crop = [
            int(person_box[0] - x1),
            int(person_box[1] - y1),
            int(person_box[2] - x1),
            int(person_box[3] - y1)
        ]
        weapon_box_crop = [
            int(weapon_box[0] - x1),
            int(weapon_box[1] - y1),
            int(weapon_box[2] - x1),
            int(weapon_box[3] - y1)
        ]
        
        # Vẽ box người (màu xanh lá)
        cv2.rectangle(cropped_frame, 
                     (person_box_crop[0], person_box_crop[1]),
                     (person_box_crop[2], person_box_crop[3]),
                     (0, 255, 0), 3)
        cv2.putText(cropped_frame, "Person", 
                   (person_box_crop[0], person_box_crop[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # Vẽ box vũ khí (màu đỏ)
        cv2.rectangle(cropped_frame,
                     (weapon_box_crop[0], weapon_box_crop[1]),
                     (weapon_box_crop[2], weapon_box_crop[3]),
                     (0, 0, 255), 3)
        cv2.putText(cropped_frame, weapon_class.upper(),
                   (weapon_box_crop[0], weapon_box_crop[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        
        # Vẽ line nối giữa người và vũ khí
        person_center = (
            (person_box_crop[0] + person_box_crop[2]) // 2,
            (person_box_crop[1] + person_box_crop[3]) // 2
        )
        weapon_center = (
            (weapon_box_crop[0] + weapon_box_crop[2]) // 2,
            (weapon_box_crop[1] + weapon_box_crop[3]) // 2
        )
        cv2.line(cropped_frame, person_center, weapon_center, (255, 255, 0), 3)
        
        # Thêm text warning lớn ở góc trên
        cv2.putText(cropped_frame, "WEAPON DETECTED!",
                   (10, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        
        frame_to_save = cropped_frame
    else:
        # Nếu không có box info, lưu toàn bộ frame
        frame_to_save = frame
    
    img_path = os.path.join(SNAPSHOT_DIR, f"{weapon_class}_{timestamp}.jpg")
    cv2.imwrite(img_path, frame_to_save)
    return img_path, timestamp

def send_telegram_alert(image_path, data):
    """Gửi cảnh báo Telegram kèm ảnh cho mọi phát hiện vũ khí."""
    # Định dạng tiêu đề dựa vào mức độ nguy hiểm
    is_high_danger = "NGUY HIỂM CAO" in data['danger_level']
    
    # Chọn icon và tiêu đề theo mức độ nguy hiểm
    if is_high_danger:
        title = "🔴 ‼️ CẢNH BÁO NGUY HIỂM CAO ‼️"
        alert_tag = "#NGUY_HIỂM_CAO"
    elif "CẢNH BÁO" in data['danger_level']:
        title = "� Phát hiện Đáng Chú Ý"
        alert_tag = "#THEO_DÕI"
    else:
        title = "🔍 Phát hiện Vũ khí"
        alert_tag = "#GHI_NHẬN"
    
    caption = (
        f"{title}\n\n"
        f"• Vũ khí: `{data['weapon_class']}`\n"
        f"• Độ tin cậy: `{data['confidence']:.0%}`\n"
        f"• Khoảng cách: `{data.get('distance', 'N/A')}m`\n"
        f"• Trạng thái: `{data['status']}`\n"
        f"• Mức đe dọa: *{data['danger_level']}*\n\n"
        f"{alert_tag}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(image_path, "rb") as img:
            resp = requests.post(url, data={
                "chat_id": CHAT_ID,
                "caption": caption,
                "parse_mode": "Markdown"
            }, files={"photo": img}, timeout=10)

        if resp.status_code != 200:
            print(f"[TELEGRAM SEND ERROR] status={resp.status_code} text={resp.text}")
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] {e}")
# Here is the token for bot BOT_TOKENbot @TOKEN_notifier_BOT:

# 8410225620:AAFxzjamibgze87BwrjMlRzUJa_z1-9-AYQ
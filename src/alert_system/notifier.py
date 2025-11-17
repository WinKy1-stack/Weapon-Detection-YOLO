import os
import cv2
import requests
from datetime import datetime

# Prefer environment variables for tokens; fall back to the value in code if present
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8570133185:AAENKL-AItf6bzpMQ_lnuBfpTiGuc0TZ7ws")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5444586273")

SNAPSHOT_DIR = "runs/alerts_snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

def save_snapshot(frame, weapon_class):
    """Lưu frame phát hiện vào thư mục snapshot."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(SNAPSHOT_DIR, f"{weapon_class}_{timestamp}.jpg")
    cv2.imwrite(img_path, frame)
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
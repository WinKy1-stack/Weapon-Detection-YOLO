"""
Test Realtime Detection với Telegram Alert
Sử dụng ảnh test để trigger alert
"""
import cv2
import numpy as np
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv('backend/.env')

from app.services.alert_service import telegram_alert
from app.services.weapon_detector import WeaponDetector

print("=" * 60)
print("🧪 TESTING REALTIME DETECTION + TELEGRAM")
print("=" * 60)

# Check Telegram
if not telegram_alert.enabled:
    print("❌ Telegram not enabled!")
    sys.exit(1)

print(f"✅ Telegram enabled (chat_id: {telegram_alert.chat_id})")

# Load detector
print("\n📦 Loading YOLO detector...")
detector = WeaponDetector(model_path="best.pt")
print("✅ Detector loaded")

# Tìm ảnh test có weapon
test_images = [
    "dataset/test/images",
    "dataset/train/images",
    "uploads/videos"
]

test_image_path = None
for folder in test_images:
    folder_path = os.path.join(os.path.dirname(__file__), folder)
    if os.path.exists(folder_path):
        images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
        if images:
            test_image_path = os.path.join(folder_path, images[0])
            break

if not test_image_path:
    print("❌ Không tìm thấy ảnh test!")
    print("   Sử dụng ảnh mẫu...")
    # Create sample image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (30, 30, 30)
    cv2.putText(img, "TEST IMAGE", (200, 240), cv2.FONT_HERSHEY_BOLD, 1.5, (255, 255, 255), 3)
    test_image_path = "test_sample.jpg"
    cv2.imwrite(test_image_path, img)

print(f"\n📸 Using test image: {os.path.basename(test_image_path)}")

# Load and detect
frame = cv2.imread(test_image_path)
if frame is None:
    print("❌ Cannot read image!")
    sys.exit(1)

print("🔍 Running detection...")
detections = detector.detect(frame)

print(f"✅ Found {len(detections)} detections")

if len(detections) > 0:
    print("\n📋 Detections:")
    for i, det in enumerate(detections):
        print(f"   {i+1}. {det.class_name} - {det.confidence:.2%}")
    
    print("\n📤 Sending Telegram alert...")
    
    # Tạo message chi tiết
    weapon_list = ', '.join([f"{d.class_name} ({d.confidence:.1%})" for d in detections])
    message = f"🚨 WEAPON DETECTION TEST\n\n"
    message += f"📊 Detected: {len(detections)} weapon(s)\n"
    message += f"🔫 Types: {weapon_list}\n"
    message += f"📸 Source: Test Image\n"
    message += f"⚠️ Danger Level: {'HIGH' if len(detections) >= 3 else 'MEDIUM' if len(detections) == 2 else 'LOW'}"
    
    telegram_alert.send_alert(
        camera_id="test_detection",
        image=frame,
        message=message,
        detections=detections
    )
    
    print("✅ Alert sent! Check your Telegram...")
    
    import time
    print("   Waiting for background thread (5s)...")
    time.sleep(5)
    
    print("\n🎯 SUCCESS! Alert should be in your Telegram now!")
    
else:
    print("\n⚠️  No weapons detected in test image")
    print("   Telegram alert will only trigger when weapons are found")

print("\n" + "=" * 60)

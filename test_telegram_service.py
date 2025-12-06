"""
Test Telegram Alert qua Backend Service
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


def create_test_image():
    """Create a test image"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (30, 30, 30)
    
    cv2.putText(img, "WEAPON DETECTED!", (150, 240), 
                cv2.FONT_HERSHEY_BOLD, 1.5, (0, 0, 255), 3)
    cv2.rectangle(img, (200, 150), (440, 350), (0, 0, 255), 3)
    
    return img


class MockDetection:
    def __init__(self, class_name, confidence):
        self.class_name = class_name
        self.confidence = confidence


print("=" * 60)
print("🧪 TESTING TELEGRAM ALERT SERVICE")
print("=" * 60)

if not telegram_alert.enabled:
    print("\n❌ Telegram service không được enabled!")
    print(f"   Bot token: {telegram_alert.bot_token}")
    print(f"   Chat ID: {telegram_alert.chat_id}")
    sys.exit(1)

print(f"\n✅ Telegram service enabled")
print(f"   Chat ID: {telegram_alert.chat_id}")

# Create test image
print("\n📸 Creating test image...")
test_image = create_test_image()

# Create mock detections
mock_detections = [
    MockDetection("pistol", 0.95),
    MockDetection("knife", 0.88)
]

# Send alert
print("\n📤 Sending alert to Telegram...")
telegram_alert.send_alert(
    camera_id="test_camera_001",
    image=test_image,
    message="🚨 TEST ALERT: 2 weapons detected from backend service!",
    detections=mock_detections
)

# Wait for background thread
import time
print("   Waiting for background thread to complete...")
time.sleep(5)

print("\n✅ Test completed!")
print("\n📱 Check your Telegram chat for the alert message!")
print("=" * 60)

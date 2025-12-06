"""
Test Telegram Alert Service
Run this to verify Telegram configuration
"""
import cv2
import numpy as np
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.alert_service import telegram_alert


def create_test_image():
    """Create a test image with text"""
    # Create blank image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add colored background
    img[:] = (30, 30, 30)  # Dark gray
    
    # Add title
    cv2.putText(
        img, "TELEGRAM ALERT TEST", 
        (50, 100), 
        cv2.FONT_HERSHEY_BOLD, 
        1.2, 
        (0, 255, 0),  # Green
        3
    )
    
    # Add timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(
        img, timestamp,
        (50, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),  # White
        2
    )
    
    # Add weapon icon (rectangle)
    cv2.rectangle(img, (200, 250), (440, 380), (0, 0, 255), 3)  # Red box
    cv2.putText(
        img, "WEAPON DETECTED",
        (220, 320),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),  # Red
        2
    )
    
    # Add confidence score
    cv2.putText(
        img, "Confidence: 95.3%",
        (220, 360),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),  # Yellow
        2
    )
    
    return img


class MockDetection:
    """Mock detection object for testing"""
    def __init__(self, class_name, confidence):
        self.class_name = class_name
        self.confidence = confidence


def test_telegram_alert():
    """Test Telegram alert with sample image"""
    print("=" * 60)
    print("🧪 TESTING TELEGRAM ALERT SERVICE")
    print("=" * 60)
    
    # Check if Telegram is configured
    if not telegram_alert.enabled:
        print("\n❌ TELEGRAM NOT CONFIGURED!")
        print("\nPlease set the following in backend/.env:")
        print("  TELEGRAM_BOT_TOKEN=your_bot_token")
        print("  TELEGRAM_CHAT_ID=your_chat_id")
        print("\n📝 How to get credentials:")
        print("  1. Bot Token: Talk to @BotFather on Telegram")
        print("  2. Chat ID: Talk to @userinfobot on Telegram")
        return
    
    print(f"\n✅ Telegram configured")
    print(f"   Chat ID: {telegram_alert.chat_id}")
    
    # Create test image
    print("\n📸 Creating test image...")
    test_image = create_test_image()
    
    # Create mock detections
    mock_detections = [
        MockDetection("pistol", 0.953),
        MockDetection("knife", 0.876)
    ]
    
    # Send alert
    print("\n📤 Sending test alert to Telegram...")
    print("   (This may take a few seconds...)")
    
    telegram_alert.send_alert(
        camera_id="test_camera_001",
        image=test_image,
        message="This is a test alert from Weapon Detection System",
        detections=mock_detections
    )
    
    # Wait for background thread to complete
    import time
    time.sleep(3)
    
    print("\n✅ Test completed!")
    print("\n📱 CHECK YOUR TELEGRAM:")
    print("   You should receive a message with:")
    print("   - Test image with weapon detection box")
    print("   - Alert details (camera ID, timestamp)")
    print("   - Detection list (pistol 95.3%, knife 87.6%)")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_telegram_alert()

"""
Test Telegram Alert trực tiếp
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv

# Load .env từ backend folder
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
load_dotenv(env_path)

print("=" * 60)
print("🧪 TESTING TELEGRAM CONFIGURATION")
print("=" * 60)

# Kiểm tra env vars
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

print(f"\n📋 Environment Variables:")
print(f"   .env path: {env_path}")
print(f"   .env exists: {os.path.exists(env_path)}")
print(f"   TELEGRAM_BOT_TOKEN: {bot_token[:20]}..." if bot_token else "   TELEGRAM_BOT_TOKEN: NOT SET")
print(f"   TELEGRAM_CHAT_ID: {chat_id}")

if not bot_token or not chat_id:
    print("\n❌ Telegram không được cấu hình!")
    sys.exit(1)

# Test gửi message
print("\n📤 Sending test message...")
import requests

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = {
    "chat_id": chat_id,
    "text": f"🧪 **TEST ALERT FROM WEAPON DETECTION**\n\n✅ Backend đang hoạt động!\n⏰ Timestamp: {os.popen('date /t && time /t').read().strip()}"
}

try:
    response = requests.post(url, json=data, timeout=10)
    result = response.json()
    
    if result.get("ok"):
        print("✅ Message sent successfully!")
        print(f"   Message ID: {result['result']['message_id']}")
        print(f"   Chat: {result['result']['chat']['first_name']}")
    else:
        print(f"❌ Failed to send: {result.get('description', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

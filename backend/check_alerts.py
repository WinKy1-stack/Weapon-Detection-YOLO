"""
Quick script to check alerts in MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def check_alerts():
    # Connect to MongoDB
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['weapon_detection']
    
    # Count total alerts
    count = await db.alerts.count_documents({})
    print(f"\n📊 Total alerts in MongoDB: {count}")
    
    if count > 0:
        # Get latest 10 alerts
        print("\n📋 Latest alerts:")
        alerts = await db.alerts.find().sort('timestamp', -1).limit(10).to_list(10)
        
        for i, alert in enumerate(alerts, 1):
            timestamp = alert.get('timestamp', 'N/A')
            weapon = alert.get('weapon_class', 'unknown')
            danger = alert.get('danger_level', 'low')
            camera = alert.get('camera_id', 'N/A')
            
            print(f"  {i}. [{timestamp}] {weapon} - Danger: {danger} - Camera: {camera}")
    else:
        print("\n⚠️  No alerts found in database")
        print("\n💡 To create test alerts:")
        print("   1. Go to Detection page")
        print("   2. Start Webcam/Video detection")
        print("   3. Show a weapon to camera")
        print("   4. Wait for detection")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_alerts())

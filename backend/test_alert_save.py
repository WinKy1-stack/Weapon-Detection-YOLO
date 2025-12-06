"""
Test script to verify alert saving to MongoDB
"""
import asyncio
from datetime import datetime
from app.core.database import get_database


async def test_save_alert():
    """Test saving alert to MongoDB"""
    print("🧪 Testing alert save to MongoDB...")
    
    db = get_database()
    
    # Create test alert
    alert_data = {
        "weapon_class": "pistol",
        "confidence": 0.95,
        "total_weapons": 1,
        "all_weapons": ["pistol"],
        "status": "active",
        "danger_level": "high",
        "location": "Test Camera",
        "image_path": "/snapshots/test_alert.jpg",
        "timestamp": datetime.utcnow(),
        "acknowledged": False
    }
    
    # Save to database
    result = await db.alerts.insert_one(alert_data)
    alert_id = str(result.inserted_id)
    
    print(f"✅ Alert saved with ID: {alert_id}")
    
    # Verify by reading back
    saved_alert = await db.alerts.find_one({"_id": result.inserted_id})
    
    if saved_alert:
        print(f"✅ Alert verified in database:")
        print(f"   Weapon: {saved_alert['weapon_class']}")
        print(f"   Confidence: {saved_alert['confidence']}")
        print(f"   Danger Level: {saved_alert['danger_level']}")
        print(f"   Location: {saved_alert['location']}")
    else:
        print("❌ Alert not found in database!")
    
    # Count total alerts
    count = await db.alerts.count_documents({})
    print(f"\n📊 Total alerts in database: {count}")


if __name__ == "__main__":
    asyncio.run(test_save_alert())

"""
Create test alerts in MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random

async def create_test_alerts():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['weapon_detection']
    
    weapons = ['pistol', 'knife', 'rifle', 'gun']
    danger_levels = ['high', 'medium', 'low']
    
    print("\n🔧 Creating 10 test alerts...\n")
    
    for i in range(10):
        # Random data
        weapon = random.choice(weapons)
        danger = random.choice(danger_levels)
        timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 48))
        
        alert = {
            "weapon_class": weapon,
            "danger_level": danger,
            "confidence": round(random.uniform(0.7, 0.99), 2),
            "timestamp": timestamp,
            "camera_id": f"webcam_{random.randint(1, 5)}",
            "location": f"Zone {random.choice(['A', 'B', 'C'])}",
            "image_path": f"/snapshots/alert_{int(timestamp.timestamp())}.jpg",
            "bbox": {
                "x1": random.randint(100, 300),
                "y1": random.randint(100, 300),
                "x2": random.randint(400, 600),
                "y2": random.randint(400, 600)
            }
        }
        
        result = await db.alerts.insert_one(alert)
        print(f"✅ Alert {i+1}: {weapon} ({danger}) - ID: {result.inserted_id}")
    
    # Check total
    total = await db.alerts.count_documents({})
    print(f"\n📊 Total alerts in database: {total}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_alerts())

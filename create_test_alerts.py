"""
Script to create test alerts in MongoDB
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["weapon_detection"]

# Sample data
weapons = ["pistol", "knife", "firearm", "grenade"]
danger_levels = ["high", "medium", "low"]
statuses = ["held_by_person", "no_owner"]
locations = ["Main Entrance", "Parking Lot", "Building A", "Gate 1", "Security Check"]

# Create 10 test alerts
alerts = []
for i in range(10):
    alert = {
        "weapon_class": random.choice(weapons),
        "confidence": round(random.uniform(0.6, 0.95), 2),
        "danger_level": random.choice(danger_levels),
        "status": random.choice(statuses),
        "location": random.choice(locations),
        "timestamp": datetime.utcnow() - timedelta(days=random.randint(0, 7)),
        "image_path": f"/static/results/test_alert_{i}.jpg",
        "acknowledged": False
    }
    alerts.append(alert)

# Insert alerts
result = db.alerts.insert_many(alerts)
print(f"✅ Created {len(result.inserted_ids)} test alerts successfully!")

# Show count
total_alerts = db.alerts.count_documents({})
print(f"📊 Total alerts in database: {total_alerts}")

# Show sample
print("\n📋 Sample alerts:")
for alert in db.alerts.find().limit(3):
    print(f"  - {alert['weapon_class']} ({alert['confidence']*100:.0f}%) - {alert['danger_level']} - {alert['timestamp']}")

client.close()

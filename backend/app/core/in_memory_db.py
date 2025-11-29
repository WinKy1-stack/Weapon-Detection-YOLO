"""
Simple in-memory database for testing without MongoDB
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid

class InMemoryDB:
    def __init__(self):
        self.users: Dict[str, dict] = {}
        self.alerts: List[dict] = []
        
    async def insert_user(self, user_data: dict) -> str:
        """Insert user and return ID"""
        user_id = str(uuid.uuid4())
        user_data["_id"] = user_id
        self.users[user_id] = user_data
        print(f"✅ User registered: {user_data.get('email')} with ID: {user_id}")
        print(f"📊 Total users in DB: {len(self.users)}")
        return user_id
    
    async def find_user_by_email(self, email: str) -> Optional[dict]:
        """Find user by email"""
        print(f"🔍 Searching for user with email: {email}")
        for user in self.users.values():
            if user.get("email") == email:
                print(f"✅ Found user: {user.get('full_name', 'Unknown')}")
                return user
        print(f"❌ User not found")
        return None
    
    async def find_user_by_id(self, user_id: str) -> Optional[dict]:
        """Find user by ID"""
        return self.users.get(user_id)
    
    async def insert_alert(self, alert_data: dict) -> str:
        """Insert alert and return ID"""
        alert_id = str(uuid.uuid4())
        alert_data["_id"] = alert_id
        alert_data["timestamp"] = datetime.utcnow()
        self.alerts.append(alert_data)
        return alert_id
    
    async def get_alerts(self, limit: int = 50, skip: int = 0, filters: dict = None) -> List[dict]:
        """Get alerts with filters"""
        filtered_alerts = self.alerts
        
        if filters:
            if filters.get("weapon_class"):
                filtered_alerts = [a for a in filtered_alerts if a.get("weapon_class") == filters["weapon_class"]]
            if filters.get("danger_level"):
                filtered_alerts = [a for a in filtered_alerts if a.get("danger_level") == filters["danger_level"]]
        
        # Sort by timestamp descending
        filtered_alerts = sorted(filtered_alerts, key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        return filtered_alerts[skip:skip+limit]
    
    async def get_alert_by_id(self, alert_id: str) -> Optional[dict]:
        """Get alert by ID"""
        for alert in self.alerts:
            if alert.get("_id") == alert_id:
                return alert
        return None
    
    async def count_alerts(self, filters: dict = None) -> int:
        """Count alerts"""
        if not filters:
            return len(self.alerts)
        
        filtered_alerts = self.alerts
        if filters.get("weapon_class"):
            filtered_alerts = [a for a in filtered_alerts if a.get("weapon_class") == filters["weapon_class"]]
        if filters.get("danger_level"):
            filtered_alerts = [a for a in filtered_alerts if a.get("danger_level") == filters["danger_level"]]
        
        return len(filtered_alerts)
    
    async def delete_alert(self, alert_id: str) -> bool:
        """Delete alert"""
        for i, alert in enumerate(self.alerts):
            if alert.get("_id") == alert_id:
                self.alerts.pop(i)
                return True
        return False

# Singleton instance
in_memory_db = InMemoryDB()

# Add some dummy data for testing
async def init_dummy_data():
    """Initialize dummy alerts for testing"""
    from datetime import timedelta
    
    dummy_alerts = [
        {
            "weapon_class": "firearm",
            "confidence": 0.95,
            "danger_level": "high",
            "person_held": True,
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "location": "Camera 1",
        },
        {
            "weapon_class": "knife",
            "confidence": 0.87,
            "danger_level": "medium",
            "person_held": True,
            "timestamp": datetime.utcnow() - timedelta(hours=5),
            "location": "Camera 2",
        },
        {
            "weapon_class": "firearm",
            "confidence": 0.92,
            "danger_level": "high",
            "person_held": False,
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "location": "Camera 3",
        },
        {
            "weapon_class": "other",
            "confidence": 0.75,
            "danger_level": "low",
            "person_held": False,
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "location": "Camera 1",
        },
        {
            "weapon_class": "knife",
            "confidence": 0.88,
            "danger_level": "medium",
            "person_held": True,
            "timestamp": datetime.utcnow() - timedelta(days=3),
            "location": "Camera 2",
        },
    ]
    
    for alert in dummy_alerts:
        await in_memory_db.insert_alert(alert)
    
    print(f"✅ Initialized {len(dummy_alerts)} dummy alerts")

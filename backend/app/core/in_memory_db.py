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
        return user_id
    
    async def find_user_by_email(self, email: str) -> Optional[dict]:
        """Find user by email"""
        for user in self.users.values():
            if user.get("email") == email:
                return user
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

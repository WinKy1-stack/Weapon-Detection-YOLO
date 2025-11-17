"""
User database model
"""
from datetime import datetime
from typing import Optional
from bson import ObjectId


class UserModel:
    """User document structure in MongoDB"""
    
    @staticmethod
    def create(email: str, hashed_password: str, full_name: Optional[str] = None, is_admin: bool = False):
        return {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "is_active": True,
            "is_admin": is_admin,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    
    @staticmethod
    def serialize(user: dict) -> dict:
        """Convert MongoDB document to JSON-serializable dict"""
        if user and "_id" in user:
            user["_id"] = str(user["_id"])
        return user

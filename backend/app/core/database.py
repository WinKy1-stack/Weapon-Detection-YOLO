"""
MongoDB database connection and utilities
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from .config import settings

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

db = Database()


async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.db = db.client[settings.MONGODB_DB_NAME]
        
        # Test connection
        await db.client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print(f"⚠️  Make sure MongoDB is running on {settings.MONGODB_URL}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        print("❌ Closed MongoDB connection")


async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # User indexes
        await db.db.users.create_index("email", unique=True)
        await db.db.users.create_index("created_at")
        
        # Alert indexes
        await db.db.alerts.create_index("timestamp")
        await db.db.alerts.create_index("weapon_class")
        await db.db.alerts.create_index("danger_level")
        await db.db.alerts.create_index("acknowledged")
        
        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️  Failed to create indexes: {e}")


def get_database():
    """Get database instance"""
    return db.db

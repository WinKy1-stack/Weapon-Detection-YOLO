"""
Configuration settings for the FastAPI backend
"""
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load .env file from backend directory
load_dotenv()

class Settings(BaseModel):
    # API Settings
    PROJECT_NAME: str = "Weapon Detection API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars-long")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Vite dev server (alternate port)
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # FastAPI server
    ]
    
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "weapon_detection")
    
    # Redis (for caching and session)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Model Paths
    YOLO_MODEL_PATH: str = "runs/detect/weapons_yolov8_optimized_stable/weights/best.pt"
    FASTERRCNN_MODEL_PATH: str = "runs/models/fasterrcnn_full/best_model.pth"
    
    # Detection Settings
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    # Paths
    UPLOAD_DIR: str = "uploads"
    SNAPSHOT_DIR: str = "runs/alerts_snapshots"


settings = Settings()

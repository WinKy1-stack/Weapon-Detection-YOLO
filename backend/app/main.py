"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api.router import api_router
from app.services.stream_manager import stream_manager

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Weapon Detection API with YOLO and Faster R-CNN",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "results"), exist_ok=True)

# Mount static files for video results
uploads_results_dir = os.path.join(settings.UPLOAD_DIR, "results")
app.mount("/static/results", StaticFiles(directory=uploads_results_dir), name="results")

# Mount uploads directory
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Mount snapshots directory
if os.path.exists(settings.SNAPSHOT_DIR):
    app.mount("/snapshots", StaticFiles(directory=settings.SNAPSHOT_DIR), name="snapshots")

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    from app.core.database import connect_to_mongo
    from app.services.detection_service import DetectionService
    
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} started")
    print(f"📚 Docs available at: http://localhost:8000{settings.API_PREFIX}/docs")
    print(f"📹 Camera streaming ready")
    print(f"📁 Static files mounted at /static/results and /static/uploads")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Preload YOLO model
    try:
        detection_service = DetectionService()
        detection_service.load_yolo_model()
        print(f"✅ Loaded YOLO model from {settings.YOLO_MODEL_PATH}")
    except Exception as e:
        print(f"⚠️ Failed to preload YOLO model: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close connections on shutdown"""
    from app.core.database import close_mongo_connection
    print("🛑 Stopping all camera streams...")
    stream_manager.stop_all()
    await close_mongo_connection()
    print("🛑 Application shutdown")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Weapon Detection API",
        "version": settings.VERSION,
        "docs": f"{settings.API_PREFIX}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "active_cameras": stream_manager.get_active_count()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

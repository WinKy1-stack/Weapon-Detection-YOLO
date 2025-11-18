"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.app.core.config import settings
from backend.app.api.router import api_router

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

# Mount static files
if os.path.exists(settings.SNAPSHOT_DIR):
    app.mount("/snapshots", StaticFiles(directory=settings.SNAPSHOT_DIR), name="snapshots")

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} started (In-Memory Mode)")
    print(f"📚 Docs available at: http://localhost:8000{settings.API_PREFIX}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Close connections on shutdown"""
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
        "version": settings.VERSION
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

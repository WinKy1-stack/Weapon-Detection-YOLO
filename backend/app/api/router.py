"""
API Router - combines all endpoint routers
"""
from fastapi import APIRouter
from backend.app.api.endpoints import auth, detection, alerts_simple

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(detection.router, prefix="/detection", tags=["Detection"])
api_router.include_router(alerts_simple.router, prefix="/alerts", tags=["Alerts"])

"""
API Router - combines all endpoint routers
"""
from fastapi import APIRouter
from app.api.endpoints import auth, detection, alerts, realtime

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(detection.router, prefix="/detection", tags=["Detection"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["Realtime Detection"])

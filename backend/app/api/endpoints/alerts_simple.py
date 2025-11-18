"""
Alerts endpoints - Simplified version for testing
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from backend.app.core.in_memory_db import in_memory_db
from backend.app.core.security import get_current_user
from backend.app.schemas.detection import AlertResponse

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    weapon_class: Optional[str] = None,
    danger_level: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get alerts with filters"""
    filters = {}
    if weapon_class:
        filters["weapon_class"] = weapon_class
    if danger_level:
        filters["danger_level"] = danger_level
    
    alerts = await in_memory_db.get_alerts(limit=limit, skip=skip, filters=filters)
    return [AlertResponse(**alert) for alert in alerts]


@router.get("/stats")
async def get_alert_stats(
    days: int = Query(7, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get alert statistics"""
    alerts = await in_memory_db.get_alerts(limit=1000)
    
    # Filter by date
    start_date = datetime.utcnow() - timedelta(days=days)
    filtered_alerts = [a for a in alerts if a.get("timestamp", datetime.min) >= start_date]
    
    # Weapon distribution
    weapon_dist = {}
    for alert in filtered_alerts:
        weapon = alert.get("weapon_class", "unknown")
        weapon_dist[weapon] = weapon_dist.get(weapon, 0) + 1
    
    weapon_distribution = [{"weapon": k, "count": v} for k, v in weapon_dist.items()]
    
    # Danger distribution
    danger_dist = {}
    for alert in filtered_alerts:
        danger = alert.get("danger_level", "unknown")
        danger_dist[danger] = danger_dist.get(danger, 0) + 1
    
    danger_distribution = [{"level": k, "count": v} for k, v in danger_dist.items()]
    
    # Daily trends
    daily_alerts = {}
    for alert in filtered_alerts:
        date_str = alert.get("timestamp", datetime.now()).strftime("%Y-%m-%d")
        daily_alerts[date_str] = daily_alerts.get(date_str, 0) + 1
    
    daily_trends = [{"date": k, "count": v} for k, v in sorted(daily_alerts.items())]
    
    return {
        "total_alerts": len(filtered_alerts),
        "period_days": days,
        "weapon_distribution": weapon_distribution,
        "danger_distribution": danger_distribution,
        "daily_trends": daily_trends
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific alert by ID"""
    alert = await in_memory_db.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse(**alert)


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an alert"""
    # Simple version without admin check
    deleted = await in_memory_db.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert deleted successfully"}

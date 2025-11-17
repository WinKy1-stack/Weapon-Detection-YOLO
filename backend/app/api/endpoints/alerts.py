"""
Alerts endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from backend.app.core.database import get_database
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
    """
    Get alerts with filters
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        weapon_class: Filter by weapon type
        danger_level: Filter by danger level
        start_date: Filter by start date
        end_date: Filter by end date
    """
    db = get_database()
    
    # Build query
    query = {}
    if weapon_class:
        query["weapon_class"] = weapon_class
    if danger_level:
        query["danger_level"] = danger_level
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    
    # Get alerts
    cursor = db.alerts.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    alerts = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for alert in alerts:
        alert["_id"] = str(alert["_id"])
    
    return [AlertResponse(**alert) for alert in alerts]


@router.get("/stats")
async def get_alert_stats(
    days: int = Query(7, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Get alert statistics
    
    Args:
        days: Number of days to analyze
    """
    db = get_database()
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total alerts
    total_alerts = await db.alerts.count_documents({"timestamp": {"$gte": start_date}})
    
    # Alerts by weapon class
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {"_id": "$weapon_class", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    weapon_stats = await db.alerts.aggregate(pipeline).to_list(length=None)
    
    # Alerts by danger level
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {"_id": "$danger_level", "count": {"$sum": 1}}},
    ]
    danger_stats = await db.alerts.aggregate(pipeline).to_list(length=None)
    
    # Daily alerts
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    daily_alerts = await db.alerts.aggregate(pipeline).to_list(length=None)
    
    return {
        "total_alerts": total_alerts,
        "period_days": days,
        "weapon_distribution": [
            {"weapon": item["_id"], "count": item["count"]} 
            for item in weapon_stats
        ],
        "danger_distribution": [
            {"level": item["_id"], "count": item["count"]} 
            for item in danger_stats
        ],
        "daily_trends": [
            {"date": item["_id"], "count": item["count"]} 
            for item in daily_alerts
        ]
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific alert by ID"""
    db = get_database()
    
    try:
        alert = await db.alerts.find_one({"_id": ObjectId(alert_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid alert ID")
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert["_id"] = str(alert["_id"])
    return AlertResponse(**alert)


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an alert (admin only)"""
    db = get_database()
    
    # Check if user is admin
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.alerts.delete_one({"_id": ObjectId(alert_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid alert ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert deleted successfully"}

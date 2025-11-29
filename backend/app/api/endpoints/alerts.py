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


@router.get("/")
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
    Get alerts with filters (In-Memory version)
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        weapon_class: Filter by weapon type
        danger_level: Filter by danger level
        start_date: Filter by start date
        end_date: Filter by end date
    """
    db = get_database()
    
    # Build MongoDB query
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
    
    # Get total count
    total = await db.alerts.count_documents(query)
    
    # Get alerts with pagination
    cursor = db.alerts.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    alerts = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for alert in alerts:
        alert["_id"] = str(alert["_id"])
    
    return {"alerts": alerts, "total": total}


@router.get("/stats")
async def get_alert_stats(
    days: int = Query(7, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Get alert statistics from MongoDB
    
    Args:
        days: Number of days to analyze
    """
    db = get_database()
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # MongoDB aggregation pipeline
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$facet": {
            "total": [{"$count": "count"}],
            "by_weapon": [
                {"$group": {"_id": "$weapon_class", "count": {"$sum": 1}}},
                {"$project": {"weapon": "$_id", "count": 1, "_id": 0}}
            ],
            "by_danger": [
                {"$group": {"_id": "$danger_level", "count": {"$sum": 1}}},
                {"$project": {"level": "$_id", "count": 1, "_id": 0}}
            ],
            "by_date": [
                {"$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "count": {"$sum": 1}
                }},
                {"$project": {"date": "$_id", "count": 1, "_id": 0}},
                {"$sort": {"date": 1}}
            ]
        }}
    ]
    
    result = await db.alerts.aggregate(pipeline).to_list(length=1)
    
    if not result:
        return {
            "total_alerts": 0,
            "weapon_distribution": [],
            "danger_distribution": [],
            "daily_trend": []
        }
    
    data = result[0]
    total_alerts = data["total"][0]["count"] if data["total"] else 0
    
    # Process danger distribution for quick stats
    high_danger = next((item["count"] for item in data["by_danger"] if item["level"] == "high"), 0)
    medium_danger = next((item["count"] for item in data["by_danger"] if item["level"] == "medium"), 0)
    low_danger = next((item["count"] for item in data["by_danger"] if item["level"] == "low"), 0)
    
    # Today's alerts
    today = datetime.utcnow().date().isoformat()
    today_alerts = next((item["count"] for item in data["by_date"] if item["date"] == today), 0)
    
    return {
        "total_alerts": total_alerts,
        "period_days": days,
        "today_alerts": today_alerts,
        "high_danger": high_danger,
        "medium_danger": medium_danger,
        "low_danger": low_danger,
        "weapon_distribution": data["by_weapon"],
        "danger_distribution": data["by_danger"],
        "daily_trends": data["by_date"]
    }


@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific alert by ID"""
    db = get_database()
    
    alert = await db.alerts.find_one({"_id": ObjectId(alert_id)})
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert["_id"] = str(alert["_id"])
    return alert


@router.post("/create")
async def create_alert(
    weapon_class: str,
    confidence: float,
    status: str,
    danger_level: str,
    distance: Optional[float] = None,
    image_path: Optional[str] = None,
    location: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new alert
    """
    db = get_database()
    
    alert_data = {
        "weapon_class": weapon_class,
        "confidence": confidence,
        "status": status,
        "danger_level": danger_level,
        "distance": distance,
        "image_path": image_path or "",
        "location": location or "Unknown",
        "timestamp": datetime.utcnow(),
        "acknowledged": False
    }
    
    result = await db.alerts.insert_one(alert_data)
    alert_id = str(result.inserted_id)
    
    return {"message": "Alert created", "alert_id": alert_id}


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an alert"""
    db = get_database()
    
    result = await db.alerts.delete_one({"_id": ObjectId(alert_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert deleted successfully"}

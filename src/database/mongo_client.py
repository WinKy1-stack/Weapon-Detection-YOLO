from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["weapon_alert_system"]
alerts = db["alerts"]

def save_alert(data: dict):
    """Lưu dữ liệu cảnh báo vào MongoDB với các trường bổ sung."""
    try:
        # Thêm các trường phụ để dễ truy vấn và phân tích
        enhanced_data = data.copy()
        
        # Phân loại mức độ nguy hiểm
        is_high_danger = "NGUY HIỂM CAO" in data["danger_level"]
        is_medium_danger = "CẢNH BÁO" in data["danger_level"]
        
        enhanced_data.update({
            # Các flag để dễ truy vấn
            "is_high_danger": is_high_danger,
            "danger_category": (
                "HIGH" if is_high_danger
                else "MEDIUM" if is_medium_danger
                else "LOW"
            ),
            "held_by_person": data["status"] == "Held by Person",
            
            # Thời gian để phân tích xu hướng
            "detection_hour": data["timestamp"].hour,
            "detection_date": data["timestamp"].strftime("%Y-%m-%d"),
            "detection_month": data["timestamp"].strftime("%Y-%m"),
            
            # Metadata cho phân tích
            "image_saved": True,
            "alert_sent": True,
            "requires_attention": is_high_danger or is_medium_danger,
        })
        
        # Lưu vào MongoDB
        result = alerts.insert_one(enhanced_data)
        print(f"[MONGO SAVE OK] Alert ID: {result.inserted_id}")
        
        # Nếu là mức nguy hiểm cao, in thông báo đặc biệt
        if enhanced_data["is_high_danger"]:
            print(f"[❗HIGH DANGER❗] {data['weapon_class']} detected! Alert ID: {result.inserted_id}")
            
    except Exception as e:
        print(f"[MONGO SAVE ERROR] {e}")

def get_recent_alerts(limit=20, danger_level=None):
    """Truy xuất cảnh báo gần nhất với bộ lọc tùy chọn."""
    query = {}
    if danger_level == "HIGH":
        query["is_high_danger"] = True
    elif danger_level == "MEDIUM":
        query["danger_category"] = "MEDIUM"
    elif danger_level == "LOW":
        query["danger_category"] = "LOW"
        
    return list(alerts.find(query).sort("timestamp", -1).limit(limit))

def get_high_danger_stats(hours=24):
    """Thống kê các cảnh báo nguy hiểm cao trong N giờ qua."""
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(hours=hours)
    
    pipeline = [
        {"$match": {
            "is_high_danger": True,
            "timestamp": {"$gte": since}
        }},
        {"$group": {
            "_id": "$weapon_class",
            "count": {"$sum": 1},
            "avg_distance": {"$avg": "$distance"},
            "held_by_person_count": {
                "$sum": {"$cond": [{"$eq": ["$status", "Held by Person"]}, 1, 0]}
            }
        }},
        {"$sort": {"count": -1}}
    ]
    
    return list(alerts.aggregate(pipeline))

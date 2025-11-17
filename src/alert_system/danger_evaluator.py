from datetime import datetime
from typing import Tuple

def get_danger_level(weapon_class: str, conf: float, distance: float | None):
    """Xác định mức độ nguy hiểm dựa trên loại vũ khí và khoảng cách."""
    # Mức độ nghiêm trọng của từng loại vũ khí
    weapon_severity = {
        "pistol": 4,    # Súng lục - rất nguy hiểm
        "firearm": 4,   # Súng - rất nguy hiểm
        "grenade": 5,   # Lựu đạn - cực kỳ nguy hiểm
        "knife": 3,     # Dao - nguy hiểm
        "rocket": 5,    # Tên lửa - cực kỳ nguy hiểm
        "fire": 2,      # Lửa - ít nguy hiểm hơn
    }

    severity = weapon_severity.get(weapon_class, 1)
    
    # Tính toán mức độ nguy hiểm dựa trên:
    # - Loại vũ khí
    # - Độ tin cậy của phát hiện
    # - Khoảng cách tới người
    
    # Khoảng cách nguy hiểm (mét)
    dangerous_distance = {
        "pistol": 1.5,
        "firearm": 1.5,
        "grenade": 3.0,
        "knife": 1.0,
        "rocket": 5.0,
        "fire": 2.0
    }.get(weapon_class, 2.0)

    # Hệ số khoảng cách (1.0 = rất gần, 0.0 = xa)
    distance_factor = 1.0
    if distance:
        if distance < dangerous_distance:
            distance_factor = 1.0
        elif distance < dangerous_distance * 2:
            distance_factor = 0.7
        else:
            distance_factor = 0.4
    
    # Tổng hợp điểm nguy hiểm (0-10)
    threat_score = (
        (severity * 2)           # 2-10 điểm từ loại vũ khí
        * distance_factor        # x0.4-1.0 từ khoảng cách
        * (conf ** 0.5)         # x0.7-1.0 từ độ tin cậy
    )

    # Phân loại mức độ nguy hiểm
    if threat_score >= 7:
        return "🚨 NGUY HIỂM CAO"
    elif threat_score >= 5:
        return "⚠️ CẢNH BÁO"
    else:
        return "ℹ️ THEO DÕI"

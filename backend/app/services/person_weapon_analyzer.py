"""
Person-Weapon Relationship Analyzer
Detects both persons and weapons, then determines their relationship
"""
import numpy as np
from typing import List, Dict, Tuple
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)


class PersonWeaponAnalyzer:
    """
    Analyzes relationship between detected persons and weapons
    """
    
    def __init__(self):
        """Initialize with YOLOv8n for person detection"""
        try:
            # Load YOLOv8n for person detection (COCO dataset includes person class)
            self.person_model = YOLO("yolov8n.pt")
            logger.info("✅ Loaded YOLOv8n for person detection")
        except Exception as e:
            logger.error(f"❌ Failed to load person detection model: {e}")
            self.person_model = None
    
    def detect_persons(self, frame: np.ndarray, conf_threshold: float = 0.5) -> List[Dict]:
        """
        Detect persons in frame using YOLOv8n
        
        Args:
            frame: Input image (BGR format)
            conf_threshold: Confidence threshold
            
        Returns:
            List of person detections with bbox
        """
        if self.person_model is None:
            return []
        
        try:
            # Run inference - only detect person (class 0 in COCO)
            results = self.person_model.predict(
                frame,
                conf=conf_threshold,
                classes=[0],  # Only detect person class
                verbose=False,
                imgsz=640
            )[0]
            
            persons = []
            for box in results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf.cpu().numpy())
                
                persons.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": confidence,
                    "center": [(x1 + x2) / 2, (y1 + y2) / 2],
                    "area": (x2 - x1) * (y2 - y1)
                })
            
            return persons
            
        except Exception as e:
            logger.error(f"Person detection error: {e}")
            return []
    
    def calculate_iou(self, box1: List[int], box2: List[int]) -> float:
        """
        Calculate Intersection over Union between two bounding boxes
        
        Args:
            box1: [x1, y1, x2, y2]
            box2: [x1, y1, x2, y2]
            
        Returns:
            float: IoU value (0-1)
        """
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # Calculate intersection area
        x_inter_min = max(x1_min, x2_min)
        y_inter_min = max(y1_min, y2_min)
        x_inter_max = min(x1_max, x2_max)
        y_inter_max = min(y1_max, y2_max)
        
        if x_inter_max < x_inter_min or y_inter_max < y_inter_min:
            return 0.0
        
        inter_area = (x_inter_max - x_inter_min) * (y_inter_max - y_inter_min)
        
        # Calculate union area
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def is_weapon_in_person_area(self, weapon_bbox: List[int], person_bbox: List[int]) -> bool:
        """
        Check if weapon center point is inside person bounding box
        
        Args:
            weapon_bbox: [x1, y1, x2, y2]
            person_bbox: [x1, y1, x2, y2]
            
        Returns:
            bool: True if weapon is inside person area
        """
        wx1, wy1, wx2, wy2 = weapon_bbox
        px1, py1, px2, py2 = person_bbox
        
        # Calculate weapon center
        weapon_center_x = (wx1 + wx2) / 2
        weapon_center_y = (wy1 + wy2) / 2
        
        # Check if center is inside person box (with margin)
        margin = 50  # pixels margin for tolerance
        return (
            px1 - margin <= weapon_center_x <= px2 + margin and
            py1 - margin <= weapon_center_y <= py2 + margin
        )
    
    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def analyze_weapon_person_relationship(
        self, 
        weapon_detections: List[Dict],
        person_detections: List[Dict]
    ) -> List[Dict]:
        """
        Analyze relationship between weapons and persons
        
        Args:
            weapon_detections: List of weapon detections from weapon_detector
            person_detections: List of person detections from detect_persons()
            
        Returns:
            List of weapon detections with added relationship info:
            {
                ...original weapon detection...,
                "status": "held_by_person" | "on_ground" | "carried",
                "distance_to_nearest_person": float,
                "threat_level": "high" | "medium" | "low"
            }
        """
        if not weapon_detections:
            return []
        
        analyzed_weapons = []
        
        for weapon in weapon_detections:
            weapon_bbox = weapon.get('bbox', [])
            if not weapon_bbox or len(weapon_bbox) != 4:
                continue
            
            # Calculate weapon center
            weapon_center = [
                (weapon_bbox[0] + weapon_bbox[2]) / 2,
                (weapon_bbox[1] + weapon_bbox[3]) / 2
            ]
            
            # Find nearest person and relationship
            nearest_distance = float('inf')
            is_held = False
            nearest_person = None
            
            if person_detections:
                for person in person_detections:
                    person_bbox = person['bbox']
                    person_center = person['center']
                    
                    # Calculate distance between weapon and person centers
                    distance = self.calculate_distance(weapon_center, person_center)
                    
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_person = person
                    
                    # Check if weapon is inside person area
                    if self.is_weapon_in_person_area(weapon_bbox, person_bbox):
                        is_held = True
                        nearest_distance = 0
                        break
            
            # Determine status
            if is_held:
                status = "held_by_person"
                threat_level = "high"
            elif nearest_distance < 100:  # pixels
                status = "carried"
                threat_level = "high"
            elif nearest_distance < 300:
                status = "near_person"
                threat_level = "medium"
            else:
                status = "on_ground"
                threat_level = "low"
            
            # Add relationship info to weapon detection
            analyzed_weapon = weapon.copy()
            analyzed_weapon.update({
                "status": status,
                "distance_to_nearest_person": nearest_distance if nearest_distance != float('inf') else None,
                "threat_level": threat_level,
                "person_detected": len(person_detections) > 0
            })
            
            analyzed_weapons.append(analyzed_weapon)
        
        return analyzed_weapons
    
    def get_status_vietnamese(self, status: str) -> str:
        """Convert status to Vietnamese description"""
        status_map = {
            "held_by_person": "Held by Person",
            "carried": "Being Carried",
            "near_person": "Near Person",
            "on_ground": "On Ground / Unattended"
        }
        return status_map.get(status, "Unknown")
    
    def determine_overall_threat(
        self,
        analyzed_weapons: List[Dict],
        person_count: int
    ) -> Tuple[str, str]:
        """
        Determine overall threat level and message
        
        Args:
            analyzed_weapons: Weapons with relationship analysis
            person_count: Number of persons detected
            
        Returns:
            (danger_level, status_message)
        """
        if not analyzed_weapons:
            return "low", "No Weapons Detected"
        
        weapon_count = len(analyzed_weapons)
        held_count = sum(1 for w in analyzed_weapons if w.get('status') == 'held_by_person')
        
        # High threat scenarios
        if held_count > 0:
            if weapon_count >= 3 or held_count >= 2:
                return "high", f"Critical - {held_count} Weapon(s) Held by Person"
            elif person_count >= 2:
                return "high", f"Multiple Armed Persons - {held_count} Weapon(s) Active"
            else:
                return "high", "Held by Person"
        
        # Medium threat
        if weapon_count >= 2:
            return "medium", f"Multiple Weapons Detected - {weapon_count} Items"
        
        # Check if weapons are near persons
        near_person = any(w.get('status') in ['carried', 'near_person'] for w in analyzed_weapons)
        if near_person:
            return "medium", "Weapon Near Person"
        
        # Low threat - weapons on ground
        return "low", "Weapon Detected - No Immediate Threat"


# Global singleton instance
person_weapon_analyzer = PersonWeaponAnalyzer()

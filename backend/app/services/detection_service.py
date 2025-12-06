"""
Detection service for running inference with YOLO and Faster R-CNN
Includes person-weapon pairing logic
"""
import cv2
import numpy as np
import torch
import time
from ultralytics import YOLO
from typing import List, Tuple, Optional, Dict, Any
import os
import sys

# Add project root to path to import src modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, project_root)

from app.core.config import settings
from app.schemas.detection import Detection, BoundingBox, PersonWeaponPair


class DetectionService:
    def __init__(self):
        self.yolo_model = None
        self.person_model = None
        self.fasterrcnn_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pairing_distance_threshold = 150  # pixels
        
    def load_yolo_model(self):
        """Load YOLO model"""
        if self.yolo_model is None:
            model_path = os.path.join(project_root, settings.YOLO_MODEL_PATH)
            if os.path.exists(model_path):
                self.yolo_model = YOLO(model_path)
                # Move to GPU if available
                if self.device == "cuda":
                    self.yolo_model.to(self.device)
                    print(f"✅ Loaded YOLO model from {model_path} on GPU")
                else:
                    print(f"✅ Loaded YOLO model from {model_path} on CPU")
            else:
                raise FileNotFoundError(f"YOLO model not found at {model_path}")
        return self.yolo_model
    
    def load_fasterrcnn_model(self):
        """Load Faster R-CNN model"""
        if self.fasterrcnn_model is None:
            model_path = os.path.join(project_root, settings.FASTERRCNN_MODEL_PATH)
            if os.path.exists(model_path):
                self.fasterrcnn_model = torch.load(model_path, map_location=self.device)
                self.fasterrcnn_model.eval()
                print(f"✅ Loaded Faster R-CNN model from {model_path}")
            else:
                # Use quick test model as fallback
                fallback_path = os.path.join(project_root, "runs/models/fasterrcnn_quick_test.pth")
                if os.path.exists(fallback_path):
                    self.fasterrcnn_model = torch.load(fallback_path, map_location=self.device)
                    self.fasterrcnn_model.eval()
                    print(f"⚠️ Using fallback model from {fallback_path}")
                else:
                    raise FileNotFoundError(f"Faster R-CNN model not found")
        return self.fasterrcnn_model
    
    def detect_with_yolo(self, image: np.ndarray, conf_threshold: float = 0.5) -> Tuple[List[Detection], float]:
        """
        Run YOLO detection on image
        
        Args:
            image: Input image (BGR format)
            conf_threshold: Confidence threshold
            
        Returns:
            Tuple of (detections list, processing time)
        """
        model = self.load_yolo_model()
        
        # OPTIMIZATION: Resize large images for faster inference
        original_h, original_w = image.shape[:2]
        max_size = 640  # YOLO input size
        
        if original_w > max_size or original_h > max_size:
            # Resize maintaining aspect ratio
            scale = max_size / max(original_w, original_h)
            new_w = int(original_w * scale)
            new_h = int(original_h * scale)
            resized_image = cv2.resize(image, (new_w, new_h))
            scale_back_x = original_w / new_w
            scale_back_y = original_h / new_h
        else:
            resized_image = image
            scale_back_x = 1.0
            scale_back_y = 1.0
        
        start_time = time.time()
        results = model(resized_image, conf=conf_threshold, verbose=False, imgsz=640)
        processing_time = time.time() - start_time
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf)
                cls = int(box.cls)
                class_name = result.names[cls]
                
                # Scale coordinates back to original image size
                detections.append(Detection(
                    class_name=class_name,
                    confidence=conf,
                    bbox=BoundingBox(
                        x1=float(x1 * scale_back_x), 
                        y1=float(y1 * scale_back_y), 
                        x2=float(x2 * scale_back_x), 
                        y2=float(y2 * scale_back_y)
                    )
                ))
        
        return detections, processing_time
    
    def detect_with_fasterrcnn(self, image: np.ndarray, conf_threshold: float = 0.5) -> Tuple[List[Detection], float]:
        """
        Run Faster R-CNN detection on image
        
        Args:
            image: Input image (BGR format)
            conf_threshold: Confidence threshold
            
        Returns:
            Tuple of (detections list, processing time)
        """
        model = self.load_fasterrcnn_model()
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to tensor
        image_tensor = torch.from_numpy(image_rgb).permute(2, 0, 1).float() / 255.0
        image_tensor = image_tensor.unsqueeze(0).to(self.device)
        
        start_time = time.time()
        with torch.no_grad():
            predictions = model(image_tensor)
        processing_time = time.time() - start_time
        
        detections = []
        class_names = ["fire", "firearm", "grenade", "knife", "pistol", "rocket"]
        
        pred = predictions[0]
        boxes = pred['boxes'].cpu().numpy()
        scores = pred['scores'].cpu().numpy()
        labels = pred['labels'].cpu().numpy()
        
        for box, score, label in zip(boxes, scores, labels):
            if score >= conf_threshold:
                x1, y1, x2, y2 = box
                class_name = class_names[label - 1] if label - 1 < len(class_names) else f"class_{label}"
                
                detections.append(Detection(
                    class_name=class_name,
                    confidence=float(score),
                    bbox=BoundingBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))
                ))
        
        return detections, processing_time
    
    def load_person_model(self):
        """Load YOLOv8 person detection model"""
        if self.person_model is None:
            # Use yolov8n for person detection (class 0)
            person_model_path = os.path.join(project_root, "yolov8n.pt")
            if os.path.exists(person_model_path):
                self.person_model = YOLO(person_model_path)
                print(f"✅ Loaded person detection model")
            else:
                # Download if not exists
                self.person_model = YOLO("yolov8n.pt")
                print(f"✅ Downloaded and loaded person detection model")
        return self.person_model
    
    def calculate_distance(self, box1: BoundingBox, box2: BoundingBox) -> float:
        """Calculate center distance between two bounding boxes"""
        cx1 = (box1.x1 + box1.x2) / 2
        cy1 = (box1.y1 + box1.y2) / 2
        cx2 = (box2.x1 + box2.x2) / 2
        cy2 = (box2.y1 + box2.y2) / 2
        return np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
    
    def evaluate_danger_level(self, weapon_class: str, confidence: float, has_person: bool, distance: float = None) -> str:
        """
        Evaluate danger level based on weapon type, confidence, and person proximity
        
        Returns: "high", "medium", or "low"
        """
        dangerous_weapons = ["firearm", "pistol", "rifle", "gun"]
        moderate_weapons = ["knife", "grenade"]
        
        if has_person and distance and distance < 100:
            if any(w in weapon_class.lower() for w in dangerous_weapons):
                return "high"
            elif any(w in weapon_class.lower() for w in moderate_weapons):
                return "medium" if confidence > 0.7 else "low"
            else:
                return "medium"
        elif has_person:
            if any(w in weapon_class.lower() for w in dangerous_weapons):
                return "medium" if confidence > 0.6 else "low"
            else:
                return "low"
        else:
            # No person nearby
            return "low"
    
    def detect_persons(self, image: np.ndarray, conf_threshold: float = 0.6) -> List[BoundingBox]:
        """Detect persons in image"""
        model = self.load_person_model()
        
        results = model(image, conf=conf_threshold, classes=[0], verbose=False)  # class 0 = person
        
        persons = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                persons.append(BoundingBox(
                    x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2)
                ))
        
        return persons
    
    def pair_weapons_with_persons(
        self, 
        weapons: List[Detection], 
        persons: List[BoundingBox]
    ) -> List[PersonWeaponPair]:
        """
        Pair weapons with nearest persons
        
        Returns:
            List of PersonWeaponPair objects with pairing information
        """
        pairs = []
        
        for weapon in weapons:
            nearest_person = None
            min_distance = float('inf')
            
            for person in persons:
                distance = self.calculate_distance(weapon.bbox, person)
                if distance < min_distance:
                    min_distance = distance
                    nearest_person = person
            
            has_person = nearest_person is not None and min_distance < self.pairing_distance_threshold
            status = "held_by_person" if has_person else "no_owner"
            
            danger_level = self.evaluate_danger_level(
                weapon.class_name, 
                weapon.confidence, 
                has_person, 
                min_distance if has_person else None
            )
            
            pair = PersonWeaponPair(
                weapon=weapon,
                person_bbox=nearest_person if has_person else None,
                distance=min_distance if has_person else None,
                status=status,
                danger_level=danger_level
            )
            pairs.append(pair)
        
        return pairs
    
    def detect_with_pairing(
        self, 
        image: np.ndarray, 
        model_type: str = "yolo", 
        conf_threshold: float = 0.5
    ) -> Tuple[List[PersonWeaponPair], float, str]:
        """
        Run detection with person-weapon pairing
        
        Args:
            image: Input image
            model_type: "yolo" or "fasterrcnn"
            conf_threshold: Confidence threshold
            
        Returns:
            Tuple of (pairs, processing_time, model_used)
        """
        start_time = time.time()
        
        # Detect weapons
        weapons, weapon_time, model_used = self.detect(image, model_type, conf_threshold)
        
        # Detect persons (ENABLED - Full weapon-person pairing)
        persons = self.detect_persons(image, conf_threshold=0.6)
        
        # Pair weapons with persons
        pairs = self.pair_weapons_with_persons(weapons, persons)
        
        total_time = time.time() - start_time
        
        return pairs, total_time, model_used
    
    def detect(self, image: np.ndarray, model_type: str = "yolo", conf_threshold: float = 0.5) -> Tuple[List[Detection], float, str]:
        """
        Run detection with specified model
        
        Args:
            image: Input image
            model_type: "yolo" or "fasterrcnn"
            conf_threshold: Confidence threshold
            
        Returns:
            Tuple of (detections, processing_time, model_used)
        """
        if model_type.lower() == "yolo":
            detections, proc_time = self.detect_with_yolo(image, conf_threshold)
            return detections, proc_time, "YOLOv8m"
        elif model_type.lower() == "fasterrcnn":
            detections, proc_time = self.detect_with_fasterrcnn(image, conf_threshold)
            return detections, proc_time, "Faster R-CNN"
        else:
            raise ValueError(f"Unknown model type: {model_type}")


# Singleton instance
detection_service = DetectionService()

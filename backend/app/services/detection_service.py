"""
Detection service for running inference with YOLO and Faster R-CNN
"""
import cv2
import numpy as np
import torch
import time
from ultralytics import YOLO
from typing import List, Tuple
import os
import sys

# Add project root to path to import src modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, project_root)

from backend.app.core.config import settings
from backend.app.schemas.detection import Detection, BoundingBox


class DetectionService:
    def __init__(self):
        self.yolo_model = None
        self.fasterrcnn_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_yolo_model(self):
        """Load YOLO model"""
        if self.yolo_model is None:
            model_path = os.path.join(project_root, settings.YOLO_MODEL_PATH)
            if os.path.exists(model_path):
                self.yolo_model = YOLO(model_path)
                print(f"✅ Loaded YOLO model from {model_path}")
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
        
        start_time = time.time()
        results = model(image, conf=conf_threshold, verbose=False)
        processing_time = time.time() - start_time
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf)
                cls = int(box.cls)
                class_name = result.names[cls]
                
                detections.append(Detection(
                    class_name=class_name,
                    confidence=conf,
                    bbox=BoundingBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))
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

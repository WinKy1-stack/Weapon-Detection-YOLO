"""
Weapon Detection Service - YOLO-based weapon detection with visualization
"""
import cv2
import numpy as np
from ultralytics import YOLO
import torch
from typing import List, Dict, Tuple, Optional
import logging
import os
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class WeaponDetector:
    """
    YOLO-based weapon detector with visualization
    """
    
    def __init__(self, model_path: Optional[str] = None, conf_threshold: float = 0.5):
        """
        Initialize weapon detector
        
        Args:
            model_path: Path to YOLO model weights
            conf_threshold: Confidence threshold for detections
        """
        self.conf_threshold = conf_threshold
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Determine model path
        if model_path is None:
            # Use path from settings
            model_path = settings.YOLO_MODEL_PATH
            
            # Try project root if not absolute
            if not os.path.isabs(model_path):
                project_root = Path(__file__).parent.parent.parent.parent
                model_path = os.path.join(project_root, model_path)
        
        self.model_path = model_path
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            if not os.path.exists(self.model_path):
                logger.error(f"❌ Model not found at {self.model_path}")
                logger.info("Using YOLOv8n as fallback (for testing only)")
                self.model = YOLO("yolov8n.pt")
            else:
                self.model = YOLO(self.model_path)
                logger.info(f"✅ Loaded weapon detection model from {self.model_path}")
            
            # Move to GPU if available
            if self.device == "cuda":
                self.model.to(self.device)
                logger.info(f"✅ Model running on GPU")
            else:
                logger.info(f"⚠️ Model running on CPU (slower)")
                
        except Exception as e:
            logger.error(f"❌ Failed to load model: {str(e)}")
            raise
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Run weapon detection on frame
        
        Args:
            frame: Input image (BGR format)
            
        Returns:
            List of detections: [{"label": str, "confidence": float, "bbox": [x1,y1,x2,y2]}]
        """
        if self.model is None:
            logger.warning("Model not loaded")
            return []
        
        try:
            # Run inference
            results = self.model.predict(
                frame, 
                conf=self.conf_threshold, 
                verbose=False,
                imgsz=640
            )[0]
            
            # Parse detections
            detections = []
            
            for box in results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf.cpu().numpy())
                class_id = int(box.cls.cpu().numpy())
                label = results.names[class_id]
                
                detections.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "class_id": class_id
                })
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error: {str(e)}")
            return []
    
    def draw_boxes(
        self, 
        frame: np.ndarray, 
        detections: List[Dict],
        show_confidence: bool = True,
        thickness: int = 3
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: Input image (will be copied, not modified)
            detections: List of detections from detect()
            show_confidence: Whether to show confidence percentage
            thickness: Box line thickness
            
        Returns:
            Annotated frame with bounding boxes
        """
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            label = det['label']
            confidence = det['confidence']
            
            # Color based on confidence (red for high confidence)
            if confidence > 0.8:
                color = (0, 0, 255)  # Red
            elif confidence > 0.6:
                color = (0, 165, 255)  # Orange
            else:
                color = (0, 255, 255)  # Yellow
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            # Prepare label text
            if show_confidence:
                text = f"{label} {confidence:.0%}"
            else:
                text = label
            
            # Calculate label size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            font_thickness = 2
            (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, font_thickness)
            
            # Draw label background
            cv2.rectangle(
                annotated, 
                (x1, y1 - text_h - 10), 
                (x1 + text_w + 10, y1), 
                color, 
                -1
            )
            
            # Draw label text
            cv2.putText(
                annotated, 
                text, 
                (x1 + 5, y1 - 5), 
                font, 
                font_scale, 
                (255, 255, 255),  # White text
                font_thickness
            )
            
            # Draw center point
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            cv2.circle(annotated, (center_x, center_y), 5, color, -1)
        
        # Add detection count overlay
        if len(detections) > 0:
            count_text = f"WEAPONS DETECTED: {len(detections)}"
            cv2.rectangle(annotated, (10, 10), (400, 50), (0, 0, 255), -1)
            cv2.putText(
                annotated, 
                count_text, 
                (20, 38), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.8, 
                (255, 255, 255), 
                2
            )
        
        return annotated
    
    def filter_by_roi(self, detections: List[Dict], roi_box: List[int]) -> List[Dict]:
        """
        Filter detections by Region of Interest (ROI)
        Only keep detections where center point is inside ROI
        
        Args:
            detections: List of detections
            roi_box: ROI bounding box [x, y, w, h]
            
        Returns:
            Filtered detections inside ROI
        """
        if not roi_box or len(roi_box) != 4:
            return detections
        
        x, y, w, h = roi_box
        filtered = []
        
        for det in detections:
            bbox = det['bbox']
            # Calculate detection center point
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # Check if center is inside ROI
            if (x <= center_x <= x + w and y <= center_y <= y + h):
                filtered.append(det)
        
        return filtered
    
    def draw_roi(self, frame: np.ndarray, roi_box: List[int], color=(255, 255, 0), thickness=3) -> np.ndarray:
        """
        Draw ROI rectangle on frame
        
        Args:
            frame: Input image
            roi_box: ROI bounding box [x, y, w, h]
            color: BGR color tuple (default: cyan)
            thickness: Line thickness
            
        Returns:
            Frame with ROI drawn
        """
        if not roi_box or len(roi_box) != 4:
            return frame
        
        annotated = frame.copy()
        x, y, w, h = roi_box
        
        # Draw ROI rectangle
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)
        
        # Draw ROI label
        label = "DANGER ZONE"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        font_thickness = 2
        (text_w, text_h), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        
        # Draw label background
        cv2.rectangle(
            annotated,
            (x, y - text_h - 10),
            (x + text_w + 10, y),
            color,
            -1
        )
        
        # Draw label text
        cv2.putText(
            annotated,
            label,
            (x + 5, y - 5),
            font,
            font_scale,
            (0, 0, 0),  # Black text
            font_thickness
        )
        
        # Draw corner markers
        marker_size = 15
        corners = [
            (x, y), (x + w, y), (x, y + h), (x + w, y + h)
        ]
        for cx, cy in corners:
            cv2.circle(annotated, (cx, cy), marker_size//2, color, -1)
        
        return annotated
    
    def get_detection_summary(self, detections: List[Dict]) -> str:
        """
        Generate text summary of detections
        
        Args:
            detections: List of detections
            
        Returns:
            str: Summary text
        """
        if not detections:
            return "No weapons detected"
        
        # Count by weapon type
        weapon_counts = {}
        for det in detections:
            weapon = det['label']
            weapon_counts[weapon] = weapon_counts.get(weapon, 0) + 1
        
        summary_parts = []
        for weapon, count in weapon_counts.items():
            summary_parts.append(f"{count}x {weapon}")
        
        return f"Detected: {', '.join(summary_parts)}"


# Singleton instance
weapon_detector = WeaponDetector(conf_threshold=0.5)

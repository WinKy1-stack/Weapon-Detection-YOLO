from typing import Optional, List, Tuple
import cv2
import torch
import numpy as np
from pathlib import Path
from datetime import datetime
from ..models.utils import load_model
from ..utils.logging import setup_logger
from config.config import MODEL_CONFIG

logger = setup_logger('detector')

class WeaponDetector:
    def __init__(self, model_path: Optional[str] = None):
        """Initialize weapon detector with model path"""
        self.model_path = model_path or MODEL_CONFIG['best_model']
        self.model = load_model(self.model_path)
        self.conf_threshold = MODEL_CONFIG['conf_threshold']
        logger.info(f"Initialized WeaponDetector with model: {self.model_path}")
    
    def detect_image(self, image_path: str, save_dir: Optional[str] = None) -> Tuple[np.ndarray, List]:
        """Detect weapons in a single image"""
        try:
            # Ensure image exists
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Run detection
            results = self.model.predict(
                source=image_path,
                conf=self.conf_threshold,
                save=bool(save_dir),
                project=save_dir if save_dir else None,
                name=datetime.now().strftime("%Y%m%d_%H%M%S") if save_dir else None
            )
            
            # Get annotated image and detections
            annotated_img = results[0].plot()
            detections = results[0].boxes
            
            logger.info(f"Detected {len(detections)} objects in {image_path}")
            return annotated_img, detections
        
        except Exception as e:
            logger.error(f"Error in detect_image: {str(e)}")
            raise
    
    def detect_video(self, video_path: str, save_dir: Optional[str] = None) -> str:
        """Detect weapons in video"""
        try:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video not found: {video_path}")
            
            save_path = None
            if save_dir:
                Path(save_dir).mkdir(exist_ok=True)
                save_path = str(Path(save_dir) / f"detected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            
            results = self.model.predict(
                source=video_path,
                conf=self.conf_threshold,
                save=True if save_path else False,
                project=Path(save_dir) if save_dir else None,
                name=Path(save_path).stem if save_path else None
            )
            
            logger.info(f"Processed video: {video_path}")
            return save_path if save_path else ""
            
        except Exception as e:
            logger.error(f"Error in detect_video: {str(e)}")
            raise
    
    def realtime_detect(self, camera_id: int = 0) -> None:
        """Real-time weapon detection from camera"""
        try:
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open camera {camera_id}")
            
            logger.info("Starting realtime detection...")
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                results = self.model.predict(frame, conf=self.conf_threshold, verbose=False)
                annotated_frame = results[0].plot()
                
                # Show detection
                cv2.imshow("Weapon Detection", annotated_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            logger.info("Realtime detection stopped")
            
        except Exception as e:
            logger.error(f"Error in realtime_detect: {str(e)}")
            raise
from ultralytics import YOLO
import torch
import os
from typing import Optional, Dict, Any
from ..utils.logging import setup_logger

logger = setup_logger('model_utils')

def load_model(model_path: str, device: Optional[str] = None) -> YOLO:
    """
    Load a YOLO model with error handling
    """
    try:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Set device
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        logger.info(f"Loading model from {model_path} on {device}")
        model = YOLO(model_path)
        
        return model
    
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

def save_model_info(model: YOLO, save_dir: str, metadata: Dict[str, Any]) -> None:
    """
    Save model metadata and information
    """
    try:
        os.makedirs(save_dir, exist_ok=True)
        
        # Save model info
        info_path = os.path.join(save_dir, "model_info.txt")
        with open(info_path, "w") as f:
            f.write(f"Model Architecture: {model.model.name}\n")
            f.write(f"Input Size: {model.model.args['imgsz']}\n")
            f.write("\nMetadata:\n")
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"Saved model info to {info_path}")
    
    except Exception as e:
        logger.error(f"Error saving model info: {str(e)}")
        raise
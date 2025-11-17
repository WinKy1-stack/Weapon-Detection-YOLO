from typing import Optional, Dict
import torch
from pathlib import Path
from ultralytics import YOLO
from ..utils.logging import setup_logger, log_gpu_usage
from ..models.utils import save_model_info
from config.config import TRAIN_CONFIG, DATA_CONFIG

logger = setup_logger('trainer')

class WeaponTrainer:
    def __init__(self, model_name: str = "yolov8m.pt"):
        """Initialize trainer with model name"""
        self.model_name = model_name
        self.model = YOLO(model_name)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Initialized trainer with {model_name} on {self.device}")
        logger.info(log_gpu_usage())
    
    def train(self, 
             custom_config: Optional[Dict] = None,
             experiment_name: str = "weapons_yolov8") -> str:
        """
        Train the model with configuration
        """
        try:
            # Merge custom config with default config
            config = TRAIN_CONFIG.copy()
            if custom_config:
                config.update(custom_config)
            
            logger.info(f"Starting training with config: {config}")
            logger.info(f"Using data config: {DATA_CONFIG['data_yaml']}")
            
            # Train the model
            results = self.model.train(
                data=DATA_CONFIG['data_yaml'],
                epochs=config['epochs'],
                imgsz=512,
                batch=config['batch_size'],
                optimizer=config['optimizer'],
                lr0=config['lr0'],
                lrf=config['lrf'],
                dropout=config['dropout'],
                patience=config['patience'],
                weight_decay=config['weight_decay'],
                device=self.device,
                name=experiment_name
            )
            
            # Save model info
            save_dir = Path(f"runs/detect/{experiment_name}")
            metadata = {
                "training_config": config,
                "data_config": DATA_CONFIG,
                "final_metrics": results.results_dict
            }
            save_model_info(self.model, save_dir, metadata)
            
            best_model_path = save_dir / "weights/best.pt"
            logger.info(f"Training completed. Best model saved at: {best_model_path}")
            
            return str(best_model_path)
        
        except Exception as e:
            logger.error(f"Error in training: {str(e)}")
            raise
    
    def validate(self, model_path: Optional[str] = None):
        """
        Validate the model on validation set
        """
        try:
            if model_path:
                self.model = YOLO(model_path)
            
            logger.info(f"Starting validation on {DATA_CONFIG['val_dir']}")
            metrics = self.model.val(data=DATA_CONFIG['data_yaml'])
            
            logger.info(f"Validation metrics: {metrics.results_dict}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            raise
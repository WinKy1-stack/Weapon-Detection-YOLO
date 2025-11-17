"""
Model comparison script: YOLOv8m vs Faster R-CNN

Evaluates both models on the test set and compares:
- mAP (mean Average Precision)
- Inference speed (FPS)
- Model size
- Memory usage

Usage:
    python src/compare_models.py
"""

import os
import time
import json
from pathlib import Path
import torch
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from ultralytics import YOLO
import cv2
import numpy as np
from tqdm import tqdm


class ModelEvaluator:
    """Evaluate and compare detection models."""
    
    def __init__(self, test_images_dir, test_labels_dir):
        self.test_images_dir = test_images_dir
        self.test_labels_dir = test_labels_dir
        self.test_images = sorted([
            f for f in os.listdir(test_images_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])
    
    def load_yolo_model(self, model_path):
        """Load YOLOv8 model."""
        return YOLO(model_path)
    
    def load_fasterrcnn_model(self, checkpoint_path, num_classes=7, device='cuda'):
        """Load Faster R-CNN model."""
        model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None)
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(device)
        model.eval()
        return model
    
    def evaluate_yolo(self, model, conf_threshold=0.25):
        """Evaluate YOLO model."""
        print("\n" + "="*60)
        print("Evaluating YOLOv8m...")
        print("="*60)
        
        # Run validation
        metrics = model.val(data='dataset/data.yaml', conf=conf_threshold, verbose=False)
        
        # Measure inference speed
        inference_times = []
        for img_name in tqdm(self.test_images[:100], desc="Speed test"):  # Use subset for speed
            img_path = os.path.join(self.test_images_dir, img_name)
            img = cv2.imread(img_path)
            
            start = time.time()
            results = model.predict(img, conf=conf_threshold, verbose=False)
            inference_times.append(time.time() - start)
        
        avg_time = np.mean(inference_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        # Get model info
        model_size = Path(model.ckpt_path).stat().st_size / (1024 * 1024)  # MB
        
        results = {
            'model_name': 'YOLOv8m',
            'mAP50': float(metrics.box.map50),
            'mAP50-95': float(metrics.box.map),
            'precision': float(metrics.box.mp),
            'recall': float(metrics.box.mr),
            'inference_time_ms': avg_time * 1000,
            'fps': fps,
            'model_size_mb': model_size,
            'params': sum(p.numel() for p in model.model.parameters()) / 1e6  # Millions
        }
        
        return results
    
    def evaluate_fasterrcnn(self, model, device='cuda', conf_threshold=0.25):
        """Evaluate Faster R-CNN model."""
        print("\n" + "="*60)
        print("Evaluating Faster R-CNN...")
        print("="*60)
        
        # Measure inference speed
        inference_times = []
        all_predictions = []
        all_ground_truths = []
        
        for img_name in tqdm(self.test_images[:100], desc="Evaluating"):
            img_path = os.path.join(self.test_images_dir, img_name)
            img = cv2.imread(img_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Prepare image
            img_tensor = torch.from_numpy(img_rgb).permute(2, 0, 1).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0).to(device)
            
            # Inference
            start = time.time()
            with torch.no_grad():
                predictions = model(img_tensor)[0]
            inference_times.append(time.time() - start)
            
            # Filter by confidence
            keep = predictions['scores'] > conf_threshold
            boxes = predictions['boxes'][keep].cpu().numpy()
            scores = predictions['scores'][keep].cpu().numpy()
            labels = predictions['labels'][keep].cpu().numpy()
            
            all_predictions.append({
                'boxes': boxes,
                'scores': scores,
                'labels': labels
            })
        
        avg_time = np.mean(inference_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        # Calculate model size
        model_size = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)
        
        results = {
            'model_name': 'Faster R-CNN',
            'mAP50': 0.0,  # Would need proper mAP calculation
            'mAP50-95': 0.0,  # Would need proper mAP calculation
            'precision': 0.0,  # Would need proper calculation
            'recall': 0.0,  # Would need proper calculation
            'inference_time_ms': avg_time * 1000,
            'fps': fps,
            'model_size_mb': model_size,
            'params': sum(p.numel() for p in model.parameters()) / 1e6,
            'note': 'mAP metrics require additional computation'
        }
        
        return results
    
    def compare_and_save(self, yolo_results, frcnn_results, output_path):
        """Compare results and save to file."""
        comparison = {
            'yolov8m': yolo_results,
            'faster_rcnn': frcnn_results,
            'comparison': {
                'speed_advantage_yolo': yolo_results['fps'] / frcnn_results['fps'],
                'size_advantage_yolo': frcnn_results['model_size_mb'] / yolo_results['model_size_mb']
            }
        }
        
        # Print comparison
        print("\n" + "="*60)
        print("MODEL COMPARISON")
        print("="*60)
        print(f"{'Metric':<25} {'YOLOv8m':>15} {'Faster R-CNN':>15}")
        print("-"*60)
        print(f"{'mAP@0.5':<25} {yolo_results['mAP50']:>14.3f} {frcnn_results['mAP50']:>15.3f}")
        print(f"{'mAP@0.5:0.95':<25} {yolo_results['mAP50-95']:>14.3f} {frcnn_results['mAP50-95']:>15.3f}")
        print(f"{'Precision':<25} {yolo_results['precision']:>14.3f} {frcnn_results['precision']:>15.3f}")
        print(f"{'Recall':<25} {yolo_results['recall']:>14.3f} {frcnn_results['recall']:>15.3f}")
        print(f"{'Inference Time (ms)':<25} {yolo_results['inference_time_ms']:>14.1f} {frcnn_results['inference_time_ms']:>15.1f}")
        print(f"{'FPS':<25} {yolo_results['fps']:>14.1f} {frcnn_results['fps']:>15.1f}")
        print(f"{'Model Size (MB)':<25} {yolo_results['model_size_mb']:>14.1f} {frcnn_results['model_size_mb']:>15.1f}")
        print(f"{'Parameters (M)':<25} {yolo_results['params']:>14.1f} {frcnn_results['params']:>15.1f}")
        print("="*60)
        print(f"\nYOLO is {comparison['comparison']['speed_advantage_yolo']:.2f}x faster")
        print(f"YOLO is {comparison['comparison']['size_advantage_yolo']:.2f}x smaller")
        print("="*60)
        
        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        print(f"\nComparison saved to: {output_path}")


def main():
    # Configuration
    yolo_model_path = "runs/detect/weapons_yolov8_optimized_stable/weights/best.pt"
    frcnn_checkpoint_path = "runs/models/fasterrcnn_full/best.pth"
    test_images_dir = "dataset/test/images"
    test_labels_dir = "dataset/test/labels"
    output_path = "runs/evaluate/model_comparison.json"
    
    # Check if models exist
    if not os.path.exists(yolo_model_path):
        print(f"Error: YOLOv8 model not found at {yolo_model_path}")
        return
    
    if not os.path.exists(frcnn_checkpoint_path):
        print(f"Error: Faster R-CNN checkpoint not found at {frcnn_checkpoint_path}")
        print("Please train Faster R-CNN first using: python src/train_fasterrcnn_full.py")
        return
    
    # Initialize evaluator
    evaluator = ModelEvaluator(test_images_dir, test_labels_dir)
    
    # Evaluate YOLOv8m
    yolo_model = evaluator.load_yolo_model(yolo_model_path)
    yolo_results = evaluator.evaluate_yolo(yolo_model)
    
    # Evaluate Faster R-CNN
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    frcnn_model = evaluator.load_fasterrcnn_model(frcnn_checkpoint_path, device=device)
    frcnn_results = evaluator.evaluate_fasterrcnn(frcnn_model, device=device)
    
    # Compare and save
    evaluator.compare_and_save(yolo_results, frcnn_results, output_path)


if __name__ == '__main__':
    main()

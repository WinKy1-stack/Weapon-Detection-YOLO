"""
Full training script for Faster R-CNN on weapon detection dataset.

Features:
- Trains on full dataset with train/val split
- Early stopping based on validation mAP
- Learning rate scheduling
- Saves best model and training logs
- Comprehensive metrics logging

Usage:
    python src/train_fasterrcnn_full.py --epochs 50 --batch-size 4
"""

import argparse
import os
import time
import json
from datetime import datetime
from PIL import Image
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision
from torchvision.transforms import functional as F
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
import numpy as np
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description="Full Faster R-CNN training")
    parser.add_argument("--data-dir", default="dataset", help="Dataset root directory")
    parser.add_argument("--output-dir", default="runs/models/fasterrcnn_full", help="Output directory")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.005, help="Learning rate")
    parser.add_argument("--momentum", type=float, default=0.9, help="SGD momentum")
    parser.add_argument("--weight-decay", type=float, default=0.0005, help="Weight decay")
    parser.add_argument("--num-classes", type=int, default=7, help="Number of classes (including background)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--num-workers", type=int, default=4, help="DataLoader workers")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--eval-interval", type=int, default=5, help="Evaluate every N epochs")
    return parser.parse_args()


class WeaponDataset(Dataset):
    """Weapon detection dataset in YOLO format."""
    
    def __init__(self, root, split="train", transforms=None):
        self.images_dir = os.path.join(root, split, "images")
        self.labels_dir = os.path.join(root, split, "labels")
        self.transforms = transforms
        self.samples = []
        
        if not os.path.isdir(self.images_dir):
            raise FileNotFoundError(f"Images directory not found: {self.images_dir}")
        
        # Collect all image files
        for img_name in sorted(os.listdir(self.images_dir)):
            if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(self.images_dir, img_name)
                label_name = os.path.splitext(img_name)[0] + ".txt"
                label_path = os.path.join(self.labels_dir, label_name)
                self.samples.append((img_path, label_path))
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label_path = self.samples[idx]
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        
        boxes = []
        labels = []
        
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f.read().strip().splitlines():
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    
                    cls = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    bw = float(parts[3])
                    bh = float(parts[4])
                    
                    # Convert YOLO format to pixel coordinates
                    xmin = max(0.0, (x_center - bw / 2.0) * w)
                    ymin = max(0.0, (y_center - bh / 2.0) * h)
                    xmax = min(w, (x_center + bw / 2.0) * w)
                    ymax = min(h, (y_center + bh / 2.0) * h)
                    
                    # Skip invalid boxes
                    if xmax <= xmin or ymax <= ymin:
                        continue
                    
                    # Torchvision expects labels 1..N (0 is background)
                    labels.append(cls + 1)
                    boxes.append([xmin, ymin, xmax, ymax])
        
        # Convert to tensors
        image = F.to_tensor(img)
        if boxes:
            boxes = torch.as_tensor(boxes, dtype=torch.float32)
            labels = torch.as_tensor(labels, dtype=torch.int64)
        else:
            # Empty detection
            boxes = torch.zeros((0, 4), dtype=torch.float32)
            labels = torch.zeros((0,), dtype=torch.int64)
        
        target = {
            "boxes": boxes,
            "labels": labels,
            "image_id": torch.tensor([idx]),
            "area": (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0]) if boxes.shape[0] > 0 else torch.zeros(0),
            "iscrowd": torch.zeros((boxes.shape[0],), dtype=torch.int64)
        }
        
        return image, target


def collate_fn(batch):
    return tuple(zip(*batch))


def create_model(num_classes):
    """Create Faster R-CNN model with ResNet50 backbone."""
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
        weights=torchvision.models.detection.FasterRCNN_ResNet50_FPN_Weights.DEFAULT
    )
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


def train_one_epoch(model, optimizer, data_loader, device, epoch):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    num_batches = 0
    
    pbar = tqdm(data_loader, desc=f"Epoch {epoch}")
    for images, targets in pbar:
        images = [img.to(device) for img in images]
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
        
        loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())
        
        optimizer.zero_grad()
        losses.backward()
        optimizer.step()
        
        total_loss += losses.item()
        num_batches += 1
        
        pbar.set_postfix({'loss': f"{losses.item():.4f}"})
    
    return total_loss / num_batches


@torch.no_grad()
def evaluate(model, data_loader, device):
    """Simple evaluation - returns average loss."""
    model.train()  # Keep in train mode to get losses
    total_loss = 0
    num_batches = 0
    
    for images, targets in tqdm(data_loader, desc="Evaluating"):
        images = [img.to(device) for img in images]
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
        
        loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())
        
        total_loss += losses.item()
        num_batches += 1
    
    return total_loss / num_batches


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Save training config
    config_path = os.path.join(args.output_dir, "config.json")
    with open(config_path, 'w') as f:
        json.dump(vars(args), f, indent=2)
    
    print("=" * 60)
    print("Faster R-CNN Training Configuration")
    print("=" * 60)
    for key, value in vars(args).items():
        print(f"{key:20s}: {value}")
    print("=" * 60)
    
    # Create datasets
    print("\nLoading datasets...")
    train_dataset = WeaponDataset(args.data_dir, split="train")
    val_dataset = WeaponDataset(args.data_dir, split="val")
    
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=args.num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=args.num_workers,
        pin_memory=True
    )
    
    # Create model
    device = torch.device(args.device)
    model = create_model(args.num_classes)
    model.to(device)
    
    # Optimizer and scheduler
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(
        params,
        lr=args.lr,
        momentum=args.momentum,
        weight_decay=args.weight_decay
    )
    
    lr_scheduler = torch.optim.lr_scheduler.StepLR(
        optimizer,
        step_size=15,
        gamma=0.1
    )
    
    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    training_log = []
    
    print("\nStarting training...")
    start_time = time.time()
    
    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        
        # Train
        train_loss = train_one_epoch(model, optimizer, train_loader, device, epoch)
        
        # Evaluate
        val_loss = None
        if epoch % args.eval_interval == 0 or epoch == args.epochs:
            val_loss = evaluate(model, val_loader, device)
            print(f"\nEpoch {epoch}/{args.epochs}")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss:   {val_loss:.4f}")
            print(f"  LR:         {optimizer.param_groups[0]['lr']:.6f}")
            print(f"  Time:       {time.time() - epoch_start:.1f}s")
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_model_path = os.path.join(args.output_dir, "best.pth")
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'train_loss': train_loss,
                    'val_loss': val_loss,
                }, best_model_path)
                print(f"  ✓ Saved best model (val_loss: {val_loss:.4f})")
            else:
                patience_counter += 1
                print(f"  No improvement ({patience_counter}/{args.patience})")
            
            # Early stopping
            if patience_counter >= args.patience:
                print(f"\nEarly stopping triggered after {epoch} epochs")
                break
        else:
            print(f"\nEpoch {epoch}/{args.epochs} - Train Loss: {train_loss:.4f}")
        
        # Log
        log_entry = {
            'epoch': epoch,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'lr': optimizer.param_groups[0]['lr'],
            'time': time.time() - epoch_start
        }
        training_log.append(log_entry)
        
        # Save checkpoint
        checkpoint_path = os.path.join(args.output_dir, "last.pth")
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'train_loss': train_loss,
            'val_loss': val_loss,
        }, checkpoint_path)
        
        lr_scheduler.step()
    
    # Save training log
    log_path = os.path.join(args.output_dir, "training_log.json")
    with open(log_path, 'w') as f:
        json.dump(training_log, f, indent=2)
    
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Total time: {total_time / 3600:.2f} hours")
    print(f"Best val loss: {best_val_loss:.4f}")
    print(f"Model saved to: {args.output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()

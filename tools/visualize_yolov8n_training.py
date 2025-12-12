"""
Script to visualize YOLOv8n training metrics from results.csv
Author: WinKy1-stack
Date: December 8, 2025
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
import os
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_training_data(results_path):
    """Load training results from CSV file"""
    df = pd.read_csv(results_path)
    # Clean column names (remove leading/trailing spaces)
    df.columns = df.columns.str.strip()
    return df

def plot_loss_curves(df, output_dir):
    """Plot training and validation loss curves"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('YOLOv8n Loss Curves', fontsize=16, fontweight='bold', y=1.02)
    
    # Box Loss
    ax = axes[0]
    ax.plot(df['epoch'], df['train/box_loss'], label='Train', linewidth=2.5, marker='o', markersize=3)
    ax.plot(df['epoch'], df['val/box_loss'], label='Val', linewidth=2.5, marker='s', markersize=3)
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('Box Loss', fontweight='bold')
    ax.set_title('Bounding Box Loss', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Class Loss
    ax = axes[1]
    ax.plot(df['epoch'], df['train/cls_loss'], label='Train', linewidth=2.5, marker='o', markersize=3)
    ax.plot(df['epoch'], df['val/cls_loss'], label='Val', linewidth=2.5, marker='s', markersize=3)
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('Class Loss', fontweight='bold')
    ax.set_title('Classification Loss', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # DFL Loss
    ax = axes[2]
    ax.plot(df['epoch'], df['train/dfl_loss'], label='Train', linewidth=2.5, marker='o', markersize=3)
    ax.plot(df['epoch'], df['val/dfl_loss'], label='Val', linewidth=2.5, marker='s', markersize=3)
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('DFL Loss', fontweight='bold')
    ax.set_title('Distribution Focal Loss', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'yolov8n_loss_curves.png'), dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_dir}/yolov8n_loss_curves.png")
    plt.close()

def plot_metrics(df, output_dir):
    """Plot mAP, Precision, and Recall curves"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('YOLOv8n Performance Metrics', fontsize=18, fontweight='bold', y=0.995)
    
    # mAP@50
    ax = axes[0, 0]
    ax.plot(df['epoch'], df['metrics/mAP50(B)'], linewidth=3, marker='D', markersize=5, color='#2ecc71')
    final_map50 = df['metrics/mAP50(B)'].iloc[-1]
    ax.axhline(y=final_map50, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'Final: {final_map50:.4f}')
    ax.set_xlabel('Epoch', fontweight='bold', fontsize=12)
    ax.set_ylabel('mAP@50', fontweight='bold', fontsize=12)
    ax.set_title('Mean Average Precision @ IoU=0.5', fontweight='bold', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    
    # mAP@50-95
    ax = axes[0, 1]
    ax.plot(df['epoch'], df['metrics/mAP50-95(B)'], linewidth=3, marker='D', markersize=5, color='#3498db')
    final_map5095 = df['metrics/mAP50-95(B)'].iloc[-1]
    ax.axhline(y=final_map5095, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'Final: {final_map5095:.4f}')
    ax.set_xlabel('Epoch', fontweight='bold', fontsize=12)
    ax.set_ylabel('mAP@50-95', fontweight='bold', fontsize=12)
    ax.set_title('Mean Average Precision @ IoU=0.5:0.95', fontweight='bold', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    
    # Precision
    ax = axes[1, 0]
    ax.plot(df['epoch'], df['metrics/precision(B)'], linewidth=3, marker='o', markersize=5, color='#e74c3c')
    final_precision = df['metrics/precision(B)'].iloc[-1]
    ax.axhline(y=final_precision, color='darkred', linestyle='--', linewidth=2, alpha=0.7,
               label=f'Final: {final_precision:.4f}')
    ax.set_xlabel('Epoch', fontweight='bold', fontsize=12)
    ax.set_ylabel('Precision', fontweight='bold', fontsize=12)
    ax.set_title('Precision Score', fontweight='bold', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    
    # Recall
    ax = axes[1, 1]
    ax.plot(df['epoch'], df['metrics/recall(B)'], linewidth=3, marker='s', markersize=5, color='#f39c12')
    final_recall = df['metrics/recall(B)'].iloc[-1]
    ax.axhline(y=final_recall, color='darkorange', linestyle='--', linewidth=2, alpha=0.7,
               label=f'Final: {final_recall:.4f}')
    ax.set_xlabel('Epoch', fontweight='bold', fontsize=12)
    ax.set_ylabel('Recall', fontweight='bold', fontsize=12)
    ax.set_title('Recall Score', fontweight='bold', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'yolov8n_metrics.png'), dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_dir}/yolov8n_metrics.png")
    plt.close()

def plot_f1_precision_recall(df, output_dir):
    """Plot F1 Score and Precision-Recall trade-off"""
    # Calculate F1 score
    precision = df['metrics/precision(B)']
    recall = df['metrics/recall(B)']
    f1_score = 2 * (precision * recall) / (precision + recall + 1e-6)
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('YOLOv8n F1 Score & Precision-Recall Analysis', fontsize=16, fontweight='bold', y=1.02)
    
    # F1 Score
    ax = axes[0]
    ax.plot(df['epoch'], f1_score, linewidth=3, marker='D', markersize=5, color='#9b59b6')
    best_f1_idx = f1_score.idxmax()
    best_f1 = f1_score.iloc[best_f1_idx]
    best_epoch = df['epoch'].iloc[best_f1_idx]
    ax.axhline(y=best_f1, color='red', linestyle='--', linewidth=2, alpha=0.7,
               label=f'Best: {best_f1:.4f} @ Epoch {int(best_epoch)}')
    ax.scatter(best_epoch, best_f1, color='red', s=200, zorder=5, edgecolors='black', linewidths=2)
    ax.set_xlabel('Epoch', fontweight='bold', fontsize=12)
    ax.set_ylabel('F1 Score', fontweight='bold', fontsize=12)
    ax.set_title('F1 Score (Harmonic Mean of P & R)', fontweight='bold', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    
    # Precision-Recall Trade-off
    ax = axes[1]
    scatter = ax.scatter(recall, precision, c=df['epoch'], cmap='viridis', 
                        s=80, alpha=0.7, edgecolors='black', linewidths=0.5)
    ax.plot(recall, precision, linewidth=1.5, alpha=0.4, color='gray', linestyle='--')
    
    # Mark start and end points
    ax.scatter(recall.iloc[0], precision.iloc[0], color='green', s=200, 
              zorder=5, marker='o', edgecolors='black', linewidths=2, label='Start')
    ax.scatter(recall.iloc[-1], precision.iloc[-1], color='red', s=200, 
              zorder=5, marker='*', edgecolors='black', linewidths=2, label='End')
    
    ax.set_xlabel('Recall', fontweight='bold', fontsize=12)
    ax.set_ylabel('Precision', fontweight='bold', fontsize=12)
    ax.set_title('Precision vs Recall Trade-off', fontweight='bold', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Epoch', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'yolov8n_f1_pr.png'), dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_dir}/yolov8n_f1_pr.png")
    plt.close()

def plot_learning_rate(df, output_dir):
    """Plot learning rate schedule"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df['epoch'], df['lr/pg0'], linewidth=2.5, marker='o', markersize=4, label='param_group_0')
    ax.set_xlabel('Epoch', fontweight='bold', fontsize=12)
    ax.set_ylabel('Learning Rate', fontweight='bold', fontsize=12)
    ax.set_title('YOLOv8n Learning Rate Schedule', fontweight='bold', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'yolov8n_learning_rate.png'), dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_dir}/yolov8n_learning_rate.png")
    plt.close()

def plot_comprehensive_dashboard(df, output_dir):
    """Create comprehensive training dashboard"""
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    fig.suptitle('YOLOv8n Comprehensive Training Dashboard', fontsize=20, fontweight='bold', y=0.995)
    
    # Calculate F1
    precision = df['metrics/precision(B)']
    recall = df['metrics/recall(B)']
    f1_score = 2 * (precision * recall) / (precision + recall + 1e-6)
    
    # 1. Total Loss (Combined)
    ax1 = fig.add_subplot(gs[0, 0])
    total_train_loss = df['train/box_loss'] + df['train/cls_loss'] + df['train/dfl_loss']
    total_val_loss = df['val/box_loss'] + df['val/cls_loss'] + df['val/dfl_loss']
    ax1.plot(df['epoch'], total_train_loss, label='Train', linewidth=2, marker='o', markersize=2)
    ax1.plot(df['epoch'], total_val_loss, label='Val', linewidth=2, marker='s', markersize=2)
    ax1.set_xlabel('Epoch', fontweight='bold')
    ax1.set_ylabel('Total Loss', fontweight='bold')
    ax1.set_title('Total Training Loss', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. mAP@50
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(df['epoch'], df['metrics/mAP50(B)'], linewidth=2.5, marker='D', markersize=3, color='#2ecc71')
    ax2.set_xlabel('Epoch', fontweight='bold')
    ax2.set_ylabel('mAP@50', fontweight='bold')
    ax2.set_title(f'mAP@50 (Final: {df["metrics/mAP50(B)"].iloc[-1]:.4f})', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1])
    
    # 3. mAP@50-95
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(df['epoch'], df['metrics/mAP50-95(B)'], linewidth=2.5, marker='D', markersize=3, color='#3498db')
    ax3.set_xlabel('Epoch', fontweight='bold')
    ax3.set_ylabel('mAP@50-95', fontweight='bold')
    ax3.set_title(f'mAP@50-95 (Final: {df["metrics/mAP50-95(B)"].iloc[-1]:.4f})', fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim([0, 1])
    
    # 4. Box Loss
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.plot(df['epoch'], df['train/box_loss'], label='Train', linewidth=2)
    ax4.plot(df['epoch'], df['val/box_loss'], label='Val', linewidth=2)
    ax4.set_xlabel('Epoch', fontweight='bold')
    ax4.set_ylabel('Box Loss', fontweight='bold')
    ax4.set_title('Bounding Box Loss', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Class Loss
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.plot(df['epoch'], df['train/cls_loss'], label='Train', linewidth=2)
    ax5.plot(df['epoch'], df['val/cls_loss'], label='Val', linewidth=2)
    ax5.set_xlabel('Epoch', fontweight='bold')
    ax5.set_ylabel('Class Loss', fontweight='bold')
    ax5.set_title('Classification Loss', fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Precision & Recall
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.plot(df['epoch'], precision, label='Precision', linewidth=2, marker='o', markersize=2)
    ax6.plot(df['epoch'], recall, label='Recall', linewidth=2, marker='s', markersize=2)
    ax6.set_xlabel('Epoch', fontweight='bold')
    ax6.set_ylabel('Score', fontweight='bold')
    ax6.set_title('Precision & Recall', fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    ax6.set_ylim([0, 1])
    
    # 7. F1 Score
    ax7 = fig.add_subplot(gs[2, 0])
    ax7.plot(df['epoch'], f1_score, linewidth=2.5, marker='D', markersize=3, color='#9b59b6')
    best_f1 = f1_score.max()
    ax7.axhline(y=best_f1, color='red', linestyle='--', linewidth=1.5, alpha=0.5)
    ax7.set_xlabel('Epoch', fontweight='bold')
    ax7.set_ylabel('F1 Score', fontweight='bold')
    ax7.set_title(f'F1 Score (Best: {best_f1:.4f})', fontweight='bold')
    ax7.grid(True, alpha=0.3)
    ax7.set_ylim([0, 1])
    
    # 8. Learning Rate
    ax8 = fig.add_subplot(gs[2, 1])
    ax8.plot(df['epoch'], df['lr/pg0'], linewidth=2, marker='o', markersize=2, color='#e74c3c')
    ax8.set_xlabel('Epoch', fontweight='bold')
    ax8.set_ylabel('Learning Rate', fontweight='bold')
    ax8.set_title('Learning Rate Schedule', fontweight='bold')
    ax8.grid(True, alpha=0.3)
    ax8.set_yscale('log')
    
    # 9. Summary Table
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')
    
    summary_data = [
        ['Metric', 'Value'],
        ['Final mAP@50', f'{df["metrics/mAP50(B)"].iloc[-1]:.4f}'],
        ['Final mAP@50-95', f'{df["metrics/mAP50-95(B)"].iloc[-1]:.4f}'],
        ['Final Precision', f'{precision.iloc[-1]:.4f}'],
        ['Final Recall', f'{recall.iloc[-1]:.4f}'],
        ['Best F1 Score', f'{f1_score.max():.4f}'],
        ['Best Epoch', f'{f1_score.idxmax() + 1}'],
        ['Total Epochs', f'{len(df)}'],
    ]
    
    table = ax9.table(cellText=summary_data, cellLoc='left', loc='center',
                     colWidths=[0.6, 0.4])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.2)
    
    # Style header
    for i in range(2):
        table[(0, i)].set_facecolor('#3498db')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Alternate row colors
    for i in range(1, len(summary_data)):
        for j in range(2):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ecf0f1')
    
    ax9.set_title('Training Summary', fontweight='bold', pad=20, fontsize=12)
    
    plt.savefig(os.path.join(output_dir, 'yolov8n_dashboard.png'), dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_dir}/yolov8n_dashboard.png")
    plt.close()

def save_metrics_summary(df, output_dir):
    """Save final metrics to JSON"""
    precision = df['metrics/precision(B)']
    recall = df['metrics/recall(B)']
    f1_score = 2 * (precision * recall) / (precision + recall + 1e-6)
    
    metrics = {
        'model': 'YOLOv8n Custom (Weapon Detection)',
        'training_config': {
            'total_epochs': int(len(df)),
            'final_learning_rate': float(df['lr/pg0'].iloc[-1])
        },
        'final_metrics': {
            'mAP50': float(df['metrics/mAP50(B)'].iloc[-1]),
            'mAP50_95': float(df['metrics/mAP50-95(B)'].iloc[-1]),
            'precision': float(precision.iloc[-1]),
            'recall': float(recall.iloc[-1]),
            'f1_score': float(f1_score.iloc[-1]),
            'box_loss': float(df['val/box_loss'].iloc[-1]),
            'cls_loss': float(df['val/cls_loss'].iloc[-1]),
            'dfl_loss': float(df['val/dfl_loss'].iloc[-1])
        },
        'best_metrics': {
            'best_mAP50': float(df['metrics/mAP50(B)'].max()),
            'best_mAP50_epoch': int(df['metrics/mAP50(B)'].idxmax() + 1),
            'best_f1': float(f1_score.max()),
            'best_f1_epoch': int(f1_score.idxmax() + 1)
        }
    }
    
    output_file = os.path.join(output_dir, 'yolov8n_metrics_summary.json')
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✅ Saved: {output_file}")
    return metrics

def main():
    # Paths
    results_path = Path('runs/detect/weapons_yolov8_optimized_stable/results.csv')
    output_dir = Path('runs/detect/yolov8n_visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("📊 Generating YOLOv8n Training Visualizations...")
    print("=" * 70)
    
    # Load data
    print("📂 Loading training data...")
    df = load_training_data(results_path)
    print(f"   ✅ Loaded {len(df)} epochs of training data")
    
    # Generate all plots
    print("\n🎨 Generating visualizations...")
    plot_loss_curves(df, output_dir)
    plot_metrics(df, output_dir)
    plot_f1_precision_recall(df, output_dir)
    plot_learning_rate(df, output_dir)
    plot_comprehensive_dashboard(df, output_dir)
    
    # Save metrics
    print("\n💾 Saving metrics summary...")
    metrics = save_metrics_summary(df, output_dir)
    
    print("\n" + "=" * 70)
    print("✅ All visualizations generated successfully!")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print("\n📊 Generated files:")
    print("   - yolov8n_loss_curves.png (3 loss types)")
    print("   - yolov8n_metrics.png (mAP, Precision, Recall)")
    print("   - yolov8n_f1_pr.png (F1 & P-R trade-off)")
    print("   - yolov8n_learning_rate.png")
    print("   - yolov8n_dashboard.png (comprehensive)")
    print("   - yolov8n_metrics_summary.json")
    
    print("\n📈 Final Performance:")
    print(f"   • mAP@50:    {metrics['final_metrics']['mAP50']:.4f}")
    print(f"   • mAP@50-95: {metrics['final_metrics']['mAP50_95']:.4f}")
    print(f"   • Precision: {metrics['final_metrics']['precision']:.4f}")
    print(f"   • Recall:    {metrics['final_metrics']['recall']:.4f}")
    print(f"   • F1 Score:  {metrics['final_metrics']['f1_score']:.4f}")

if __name__ == "__main__":
    main()

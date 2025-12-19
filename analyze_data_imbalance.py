"""
Script to analyze data imbalance in the weapon detection dataset
and create visualizations
"""
import os
import glob
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import pandas as pd

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Define paths
DATASET_PATH = "C:/Workspace/weapon-detection/dataset"
CLASSES = ['fire', 'firearm', 'grenade', 'knife', 'pistol', 'rocket']

def count_class_instances(split_name):
    """Count instances of each class in a dataset split"""
    label_path = os.path.join(DATASET_PATH, split_name, 'labels')
    
    class_counts = {class_name: 0 for class_name in CLASSES}
    
    # Get all label files
    label_files = glob.glob(os.path.join(label_path, '*.txt'))
    
    for label_file in label_files:
        with open(label_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if parts:
                    class_id = int(parts[0])
                    if 0 <= class_id < len(CLASSES):
                        class_counts[CLASSES[class_id]] += 1
    
    return class_counts

def analyze_dataset():
    """Analyze the entire dataset for class imbalance"""
    print("📊 Analyzing Weapon Detection Dataset...")
    print("=" * 60)
    
    # Count instances in each split
    train_counts = count_class_instances('train')
    val_counts = count_class_instances('val')
    test_counts = count_class_instances('test')
    
    # Calculate totals
    total_counts = {cls: train_counts[cls] + val_counts[cls] + test_counts[cls] 
                    for cls in CLASSES}
    
    # Print statistics
    print("\n📈 CLASS DISTRIBUTION:")
    print("-" * 60)
    print(f"{'Class':<15} {'Train':<10} {'Val':<10} {'Test':<10} {'Total':<10} {'%':<10}")
    print("-" * 60)
    
    total_sum = sum(total_counts.values())
    for cls in CLASSES:
        percentage = (total_counts[cls] / total_sum * 100) if total_sum > 0 else 0
        print(f"{cls:<15} {train_counts[cls]:<10} {val_counts[cls]:<10} "
              f"{test_counts[cls]:<10} {total_counts[cls]:<10} {percentage:.2f}%")
    
    print("-" * 60)
    print(f"{'TOTAL':<15} {sum(train_counts.values()):<10} "
          f"{sum(val_counts.values()):<10} {sum(test_counts.values()):<10} "
          f"{total_sum:<10} 100.00%")
    print("=" * 60)
    
    # Calculate imbalance ratio
    max_class = max(total_counts, key=total_counts.get)
    min_class = min(total_counts, key=total_counts.get)
    imbalance_ratio = total_counts[max_class] / total_counts[min_class] if total_counts[min_class] > 0 else 0
    
    print(f"\n⚠️ IMBALANCE METRICS:")
    print(f"  - Most common class: {max_class} ({total_counts[max_class]} instances)")
    print(f"  - Least common class: {min_class} ({total_counts[min_class]} instances)")
    print(f"  - Imbalance Ratio: {imbalance_ratio:.2f}:1")
    
    return {
        'train': train_counts,
        'val': val_counts,
        'test': test_counts,
        'total': total_counts
    }

def create_visualizations(data):
    """Create various visualizations for data imbalance"""
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Overall Distribution (Pie Chart)
    ax1 = plt.subplot(2, 3, 1)
    colors = plt.cm.Set3(range(len(CLASSES)))
    ax1.pie(data['total'].values(), labels=data['total'].keys(), autopct='%1.1f%%',
            startangle=90, colors=colors)
    ax1.set_title('Overall Class Distribution', fontsize=14, fontweight='bold')
    
    # 2. Total Counts (Bar Chart)
    ax2 = plt.subplot(2, 3, 2)
    bars = ax2.bar(data['total'].keys(), data['total'].values(), color=colors)
    ax2.set_title('Total Instances per Class', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Class')
    ax2.set_ylabel('Number of Instances')
    ax2.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom')
    
    # 3. Train/Val/Test Split Comparison
    ax3 = plt.subplot(2, 3, 3)
    df = pd.DataFrame({
        'Train': list(data['train'].values()),
        'Val': list(data['val'].values()),
        'Test': list(data['test'].values())
    }, index=CLASSES)
    df.plot(kind='bar', ax=ax3, width=0.8)
    ax3.set_title('Distribution Across Splits', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Class')
    ax3.set_ylabel('Number of Instances')
    ax3.tick_params(axis='x', rotation=45)
    ax3.legend(title='Split')
    
    # 4. Imbalance Ratio Visualization
    ax4 = plt.subplot(2, 3, 4)
    max_count = max(data['total'].values())
    ratios = [max_count / count if count > 0 else 0 for count in data['total'].values()]
    bars = ax4.barh(CLASSES, ratios, color=colors)
    ax4.set_title('Imbalance Ratio (Max Class / Each Class)', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Ratio')
    ax4.axvline(x=1, color='red', linestyle='--', linewidth=2, label='Balanced (1:1)')
    ax4.legend()
    
    # Add value labels
    for i, (bar, ratio) in enumerate(zip(bars, ratios)):
        ax4.text(ratio, i, f'{ratio:.2f}:1', va='center', ha='left', fontsize=9)
    
    # 5. Percentage Distribution
    ax5 = plt.subplot(2, 3, 5)
    total_sum = sum(data['total'].values())
    percentages = [(count / total_sum * 100) if total_sum > 0 else 0 
                   for count in data['total'].values()]
    bars = ax5.bar(CLASSES, percentages, color=colors)
    ax5.set_title('Class Distribution (%)', fontsize=14, fontweight='bold')
    ax5.set_xlabel('Class')
    ax5.set_ylabel('Percentage (%)')
    ax5.tick_params(axis='x', rotation=45)
    ax5.axhline(y=100/len(CLASSES), color='red', linestyle='--', linewidth=2,
                label=f'Balanced ({100/len(CLASSES):.1f}%)')
    ax5.legend()
    
    # Add value labels
    for bar, pct in zip(bars, percentages):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                f'{pct:.1f}%',
                ha='center', va='bottom')
    
    # 6. Cumulative Distribution
    ax6 = plt.subplot(2, 3, 6)
    sorted_counts = sorted(data['total'].items(), key=lambda x: x[1], reverse=True)
    sorted_classes = [x[0] for x in sorted_counts]
    sorted_values = [x[1] for x in sorted_counts]
    cumsum = [sum(sorted_values[:i+1]) for i in range(len(sorted_values))]
    cumsum_pct = [(x / total_sum * 100) if total_sum > 0 else 0 for x in cumsum]
    
    ax6.plot(sorted_classes, cumsum_pct, marker='o', linewidth=2, markersize=8, color='darkblue')
    ax6.fill_between(range(len(sorted_classes)), cumsum_pct, alpha=0.3)
    ax6.set_title('Cumulative Distribution', fontsize=14, fontweight='bold')
    ax6.set_xlabel('Class (sorted by frequency)')
    ax6.set_ylabel('Cumulative Percentage (%)')
    ax6.tick_params(axis='x', rotation=45)
    ax6.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (cls, pct) in enumerate(zip(sorted_classes, cumsum_pct)):
        ax6.text(i, pct, f'{pct:.1f}%', ha='center', va='bottom', fontsize=8)
    
    plt.suptitle('🎯 Weapon Detection Dataset - Data Imbalance Analysis', 
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    # Save figure
    output_path = os.path.join(DATASET_PATH, '..', 'data_imbalance_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualization saved to: {output_path}")
    
    plt.show()

if __name__ == "__main__":
    # Analyze dataset
    data = analyze_dataset()
    
    # Create visualizations
    print("\n🎨 Creating visualizations...")
    create_visualizations(data)
    
    print("\n✅ Analysis complete!")

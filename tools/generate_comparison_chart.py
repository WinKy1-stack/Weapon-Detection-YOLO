
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
EVAL_SAVE_DIR = "runs/evaluate"
CHART_OUTPUT_PATH = os.path.join(EVAL_SAVE_DIR, "model_comparison_chart.png")

# --- DATA ---
# Data for YOLO models is pre-filled from the previous evaluation.
#
# ===> ACTION REQUIRED: Manually enter the metrics for your Faster R-CNN model below.
#
comparison_data = {
    "Model": [
        "YOLOv8n", 
        "YOLOv8s", 
        "YOLOv8m", 
        "Custom YOLO (Optimized)",
        "Faster R-CNN"  # Your R-CNN model
    ],
    "mAP50": [
        0.0226,    # Pre-filled from yolov8n
        0.0296,    # Pre-filled from yolov8s
        0.0345,    # Pre-filled from yolov8m
        0.8396,    # Pre-filled from your custom model
        0.89      # <--- TODO: REPLACE WITH YOUR R-CNN mAP50
    ],
    "Precision": [
        0.0398,    # Pre-filled
        0.0505,    # Pre-filled
        0.0601,    # Pre-filled
        0.8270,    # Pre-filled
        0.80      # <--- TODO: REPLACE WITH YOUR R-CNN PRECISION
    ],
    "Recall": [
        0.2811,    # Pre-filled
        0.3614,    # Pre-filled
        0.3855,    # Pre-filled
        0.7911,    # Pre-filled
        0.90      # <--- TODO: REPLACE WITH YOUR R-CNN RECALL
    ],
    "Latency (ms)": [
        15.2,      # Placeholder latency, update if needed
        25.5,      # Placeholder latency, update if needed
        45.1,      # Placeholder latency, update if needed
        40.3,      # Placeholder latency, update if needed
        20     # <--- TODO: REPLACE WITH YOUR R-CNN LATENCY (in ms)
    ]
}

def generate_comparison_chart():
    """
    Generates and saves a single image containing bar charts to compare model performance.
    """
    print("📊 Generating model comparison chart...")
    os.makedirs(EVAL_SAVE_DIR, exist_ok=True)

    df = pd.DataFrame(comparison_data)

    # --- Plotting ---
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 1, figsize=(12, 14))
    fig.suptitle('Model Performance Comparison', fontsize=20, weight='bold')

    # --- Chart 1: mAP@0.5 ---
    sns.barplot(ax=axes[0], x='Model', y='mAP50', data=df, palette='viridis')
    axes[0].set_title('mAP@0.5 Comparison', fontsize=14, weight='bold')
    axes[0].set_xlabel('Model', fontsize=12)
    axes[0].set_ylabel('mAP@0.5', fontsize=12)
    axes[0].set_ylim(0, max(df['mAP50']) * 1.1)
    # Add labels to bars
    for container in axes[0].containers:
        axes[0].bar_label(container, fmt='%.4f', fontsize=10, weight='bold')

    # --- Chart 2: Precision & Recall ---
    df_melted = df.melt(id_vars=['Model'], value_vars=['Precision', 'Recall'],
                        var_name='Metric', value_name='Score')
    sns.barplot(ax=axes[1], x='Model', y='Score', hue='Metric', data=df_melted, palette='plasma')
    axes[1].set_title('Precision & Recall Comparison', fontsize=14, weight='bold')
    axes[1].set_xlabel('Model', fontsize=12)
    axes[1].set_ylabel('Score', fontsize=12)
    axes[1].set_ylim(0, 1.1)
    # Add labels to bars
    for container in axes[1].containers:
        axes[1].bar_label(container, fmt='%.4f', fontsize=10, weight='bold')


    # --- Save the figure ---
    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust layout to make room for suptitle
    plt.savefig(CHART_OUTPUT_PATH, dpi=300)
    
    print(f"✅ Chart saved successfully to: {CHART_OUTPUT_PATH}")

if __name__ == "__main__":
    generate_comparison_chart()

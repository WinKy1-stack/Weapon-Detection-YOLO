
import os
import time
import pandas as pd
from ultralytics import YOLO
from pathlib import Path
import torch

# --- CONFIGURATION ---
DATA_YAML_PATH = "dataset/data.yaml"
EVAL_SAVE_DIR = "runs/evaluate"
COMPARISON_CSV_PATH = os.path.join(EVAL_SAVE_DIR, "model_comparison.csv")
SAMPLE_IMAGE_FOR_LATENCY_TEST = "dataset/test/images/armas--1-_jpg.rf.d80d9d4217152353c353434925d74f79.jpg"

MODELS_TO_COMPARE = {
    "YOLOv8n": "yolov8n.pt",
    "YOLOv8s": "yolov8s.pt",
    "YOLOv8m": "yolov8m.pt",
    "Custom_Optimized": "runs/detect/weapons_yolov8_optimized_stable/weights/best.pt"
}

def evaluate_and_compare_models():
    """
    Evaluates multiple YOLOv8 models on a dataset, measures their performance
    and latency, and saves the comparison to a CSV file.
    """
    # Ensure the evaluation directory exists
    os.makedirs(EVAL_SAVE_DIR, exist_ok=True)

    # Check if sample image exists
    if not Path(SAMPLE_IMAGE_FOR_LATENCY_TEST).exists():
        print(f"⚠️  Warning: Sample image for latency test not found at '{SAMPLE_IMAGE_FOR_LATENCY_TEST}'. Latency will be 0.")
        sample_image = None
    else:
        sample_image = SAMPLE_IMAGE_FOR_LATENCY_TEST

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🚀 Using device: {device}")

    results = []

    for model_name, model_path in MODELS_TO_COMPARE.items():
        print(f"\n--- Evaluating model: {model_name} ({model_path}) ---")

        if not Path(model_path).exists():
            print(f"❌ Error: Model path not found: {model_path}. Skipping.")
            continue

        try:
            # 1. Load Model
            model = YOLO(model_path)
            model.to(device)

            # 2. Run Validation to get metrics
            print("📊 Running validation...")
            metrics = model.val(data=DATA_YAML_PATH, save_json=False, verbose=False)
            
            map50 = metrics.box.map50
            precision = metrics.box.p[0] # Precision for the first class (assuming one)
            recall = metrics.box.r[0] # Recall for the first class

            # 3. Measure Latency
            latency_ms = 0
            if sample_image:
                print("⏱️  Measuring latency...")
                # Warm-up runs
                for _ in range(5):
                    model.predict(sample_image, verbose=False)

                # Timed runs
                start_time = time.time()
                for _ in range(20):
                    model.predict(sample_image, verbose=False)
                end_time = time.time()
                
                latency_ms = ((end_time - start_time) / 20) * 1000  # Average latency in ms

            # 4. Store results
            results.append({
                "Model": model_name,
                "mAP50": map50,
                "Precision": precision,
                "Recall": recall,
                "Latency (ms)": latency_ms,
                "Model Path": model_path
            })
            
            print(f"✅ Done. mAP50: {map50:.4f}, Latency: {latency_ms:.2f} ms")

        except Exception as e:
            print(f"❌ An error occurred while evaluating {model_name}: {e}")

    # 5. Save to CSV
    if results:
        df = pd.DataFrame(results)
        df.to_csv(COMPARISON_CSV_PATH, index=False)
        print(f"\n💾 Comparison results saved to: {COMPARISON_CSV_PATH}")
        print("\n📋 Results:")
        print(df.to_string())
    else:
        print("\nNo models were evaluated.")

if __name__ == "__main__":
    evaluate_and_compare_models()

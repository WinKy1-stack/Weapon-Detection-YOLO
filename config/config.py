import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
RUNS_DIR = os.path.join(BASE_DIR, "runs")

# Model configurations
MODEL_CONFIG = {
    "base_model": "yolov8m.pt",
    # Updated to point to the newly trained/optimized stable model
    "best_model": os.path.join(RUNS_DIR, "detect/weapons_yolov8_optimized_stable/weights/best.pt"),
    "img_size": 512,
    "conf_threshold": 0.5,
}

# Training configurations
TRAIN_CONFIG = {
    "epochs": 50,
    "batch_size": 8,
    "optimizer": "SGD",
    "lr0": 0.001,
    "lrf": 0.01,
    "dropout": 0.2,
    "patience": 10,
    "weight_decay": 0.001,
}

# Data configurations
DATA_CONFIG = {
    "data_yaml": os.path.join(DATASET_DIR, "data.yaml"),
    "train_dir": os.path.join(DATASET_DIR, "train"),
    "val_dir": os.path.join(DATASET_DIR, "val"),
    "test_dir": os.path.join(DATASET_DIR, "test"),
}

# Output configurations
OUTPUT_CONFIG = {
    "detect_dir": os.path.join(RUNS_DIR, "detect"),
    "predict_dir": os.path.join(RUNS_DIR, "predict"),
    "evaluate_dir": os.path.join(RUNS_DIR, "evaluate"),
    "video_dir": os.path.join(RUNS_DIR, "video"),
    "realtime_dir": os.path.join(RUNS_DIR, "realtime_logs"),
}
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'config' package can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.config import MODEL_CONFIG
from ultralytics import YOLO

model_path = MODEL_CONFIG.get('best_model')
print(f"Attempting to load model: {model_path}")
try:
    model = YOLO(model_path)
    print("Model loaded. Model info:")
    try:
        # print some basic info if available
        print(f"Model names: {model.names}")
    except Exception as e:
        print(f"Could not print model.names: {e}")
    sys.exit(0)
except Exception as e:
    print(f"Failed to load model: {e}")
    sys.exit(2)

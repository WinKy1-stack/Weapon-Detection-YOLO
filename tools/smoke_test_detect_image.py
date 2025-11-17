import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.config import MODEL_CONFIG, DATA_CONFIG, OUTPUT_CONFIG
from ultralytics import YOLO
import os

model_path = MODEL_CONFIG.get('best_model')
img_dir = os.path.join(PROJECT_ROOT, DATA_CONFIG['test_dir'], 'images') if isinstance(DATA_CONFIG['test_dir'], str) else DATA_CONFIG['test_dir']
# fallback to known relative path
if not os.path.isdir(img_dir):
    img_dir = os.path.join(PROJECT_ROOT, 'dataset', 'test', 'images')

sample_img = os.path.join(img_dir, 'image_0000.jpg')
print(f"Using model: {model_path}")
print(f"Sample image: {sample_img}")

model = YOLO(model_path)
print('Running prediction...')
results = model.predict(source=sample_img, conf=0.5, save=True, project=os.path.join(PROJECT_ROOT, 'runs', 'predict'), name='smoke_test')
print('Done. Saved to:', results.save_dir if hasattr(results, 'save_dir') else 'unknown')

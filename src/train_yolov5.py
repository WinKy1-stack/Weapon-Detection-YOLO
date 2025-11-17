"""
Train YOLOv5 for Weapon Detection
Author: Ánh Như & ChatGPT-5
Purpose: Train YOLOv5 model on custom weapon dataset for comparison with YOLOv8 and Faster R-CNN.
"""

import os
import sys  # <- Đảm bảo đã import sys ở đây
import torch
import subprocess
from datetime import datetime

# =============================
# CONFIGURATION
# =============================
DATA_PATH = os.path.join("dataset", "data.yaml")
MODEL = "yolov5m.pt"
EPOCHS = 50
IMG_SIZE = 640
BATCH_SIZE = 8
PROJECT = "runs/detect"
NAME = "weapons_yolov5"

# =============================
# CHECK DEVICE
# =============================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Using device: {device.upper()}")

# =============================
# TRAIN YOLOv5 VIA SUBPROCESS
# =============================

# QUAN TRỌNG: Lấy đường dẫn chính xác đến Python của venv
python_executable = sys.executable 

cmd = [
    python_executable,  # <-- SỬA LỖI 1: Dùng Python của venv
    "yolov5/train.py",
    "--data", DATA_PATH,
    "--weights", MODEL,
    "--img", str(IMG_SIZE),
    "--epochs", str(EPOCHS),
    "--batch-size", str(BATCH_SIZE),
    "--project", PROJECT,
    "--name", NAME,
    "--device", "0" if device == "cuda" else "cpu",
    "--exist-ok",
]

print("🔧 Starting YOLOv5 training...")
print(" ".join(cmd))

# SỬA LỖI 2: Thêm try...except và 'check=True' để bắt lỗi
try:
    # check=True sẽ báo lỗi nếu training thất bại
    subprocess.run(cmd, check=True) 
    
    # Chỉ in ra thành công NẾU lệnh trên chạy xong
    print("\n✅ Training complete! Results saved to:")
    print(os.path.join(PROJECT, NAME))

except subprocess.CalledProcessError as e:
    # Báo lỗi nếu subprocess (yolov5/train.py) thất bại
    print(f"\n❌ LỖI: Quá trình huấn luyện thất bại.")
    print(f"Lỗi trả về: {e}")
except FileNotFoundError:
    # Báo lỗi nếu không tìm thấy yolov5/train.py
    print(f"\n❌ LỖI: Không tìm thấy 'yolov5/train.py' hoặc '{python_executable}'")
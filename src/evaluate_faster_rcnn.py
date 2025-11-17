import torch
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.transforms import functional as F
from PIL import Image
import cv2

model_path = "runs/detect/faster_rcnn/faster_rcnn_model.pth"
model = fasterrcnn_resnet50_fpn(weights=None, num_classes=7)  # 6 lớp + background
model.load_state_dict(torch.load(model_path))
model.eval().cuda()

img_path = "dataset/val/images/example.jpg"
img = Image.open(img_path).convert("RGB")
tensor = F.to_tensor(img).unsqueeze(0).cuda()

with torch.no_grad():
    preds = model(tensor)[0]

boxes = preds["boxes"].cpu().numpy()
scores = preds["scores"].cpu().numpy()
classes = preds["labels"].cpu().numpy()

annotated = cv2.imread(img_path)
for (x1, y1, x2, y2), s, c in zip(boxes, scores, classes):
    if s > 0.6:
        cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0,0,255), 2)
        cv2.putText(annotated, f"Weapon_{c-1} ({s:.2f})", (int(x1), int(y1)-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

cv2.imwrite("runs/detect/faster_rcnn/inference_result.jpg", annotated)
print("✅ Saved annotated result to runs/detect/faster_rcnn/inference_result.jpg")

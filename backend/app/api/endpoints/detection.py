"""
Detection endpoints
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import FileResponse
import cv2
import numpy as np
import os
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.security import get_current_user
from backend.app.services.detection_service import detection_service
from backend.app.schemas.detection import DetectionResponse, Detection

router = APIRouter()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/detect/image", response_model=DetectionResponse)
async def detect_image(
    file: UploadFile = File(...),
    confidence: Optional[float] = Form(0.5),
    model_type: Optional[str] = Form("yolo"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload an image and run weapon detection
    
    Args:
        file: Image file (jpg, png, etc.)
        confidence: Confidence threshold (0.0-1.0)
        model_type: "yolo" or "fasterrcnn"
        
    Returns:
        Detection results with bounding boxes
    """
    # Validate file size
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Decode image
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Run detection
    try:
        detections, processing_time, model_used = detection_service.detect(
            image, model_type=model_type, conf_threshold=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    
    # Draw detections on image
    annotated_image = image.copy()
    for det in detections:
        x1, y1, x2, y2 = int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        label = f"{det.class_name} {det.confidence:.2f}"
        cv2.putText(annotated_image, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    # Save annotated image
    filename = f"{current_user['user_id']}_{file.filename}"
    output_path = os.path.join(settings.UPLOAD_DIR, filename)
    cv2.imwrite(output_path, annotated_image)
    
    return DetectionResponse(
        detections=detections,
        processing_time=processing_time,
        image_url=f"/api/v1/detection/image/{filename}",
        model_used=model_used
    )


@router.get("/image/{filename}")
async def get_image(filename: str):
    """Get processed image"""
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)


@router.get("/models")
async def get_available_models():
    """Get list of available detection models"""
    return {
        "models": [
            {
                "id": "yolo",
                "name": "YOLOv8m",
                "description": "Fast and accurate object detection",
                "available": os.path.exists(os.path.join(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")),
                    settings.YOLO_MODEL_PATH
                ))
            },
            {
                "id": "fasterrcnn",
                "name": "Faster R-CNN",
                "description": "High accuracy region-based detection",
                "available": os.path.exists(os.path.join(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")),
                    settings.FASTERRCNN_MODEL_PATH
                )) or os.path.exists(os.path.join(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")),
                    "runs/models/fasterrcnn_quick_test.pth"
                ))
            }
        ]
    }

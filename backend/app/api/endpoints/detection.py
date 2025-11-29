"""
Detection endpoints
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import FileResponse
import cv2
import numpy as np
import os
import time
from typing import Optional
from datetime import datetime

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
    
    # Draw detections on image with clear bounding boxes
    annotated_image = image.copy()
    for det in detections:
        x1, y1, x2, y2 = int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)
        
        # Draw thick red rectangle for weapon
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 0, 255), 3)
        
        # Draw label with background
        label = f"{det.class_name} {det.confidence:.2f}"
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        
        # Background rectangle for label
        cv2.rectangle(annotated_image, (x1, y1 - label_height - 10), (x1 + label_width, y1), (0, 0, 255), -1)
        
        # Text label
        cv2.putText(annotated_image, label, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
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


@router.post("/detect/image-with-pairing")
async def detect_image_with_pairing(
    file: UploadFile = File(...),
    confidence: Optional[float] = Form(0.5),
    model_type: Optional[str] = Form("yolo"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload an image and run weapon detection with person-weapon pairing
    
    Args:
        file: Image file (jpg, png, etc.)
        confidence: Confidence threshold (0.0-1.0)
        model_type: "yolo" or "fasterrcnn"
        
    Returns:
        Detection results with person-weapon pairing
    """
    from backend.app.schemas.detection import PairingDetectionResponse
    
    # Validate file
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Decode image
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Run detection with pairing
    try:
        pairs, processing_time, model_used = detection_service.detect_with_pairing(
            image, model_type=model_type, conf_threshold=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    
    # Draw detections on image with clear annotations
    annotated_image = image.copy()
    
    # Draw persons first (green boxes with thicker lines)
    drawn_persons = set()
    for pair in pairs:
        if pair.person_bbox and pair.status == "held_by_person":
            person_key = (int(pair.person_bbox.x1), int(pair.person_bbox.y1))
            if person_key not in drawn_persons:
                x1, y1, x2, y2 = int(pair.person_bbox.x1), int(pair.person_bbox.y1), int(pair.person_bbox.x2), int(pair.person_bbox.y2)
                
                # Thick green rectangle for person
                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                
                # Label with background
                label = "Person"
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                cv2.rectangle(annotated_image, (x1, y1 - label_h - 10), (x1 + label_w, y1), (0, 255, 0), -1)
                cv2.putText(annotated_image, label, (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                drawn_persons.add(person_key)
    
    # Draw weapons and pairing lines
    for pair in pairs:
        det = pair.weapon
        x1, y1, x2, y2 = int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)
        
        # Color based on danger level (thicker boxes)
        if pair.danger_level == "high":
            color = (0, 0, 255)  # Red
            thickness = 4
        elif pair.danger_level == "medium":
            color = (0, 165, 255)  # Orange
            thickness = 3
        else:
            color = (0, 255, 255)  # Yellow
            thickness = 3
        
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, thickness)
        
        # Draw weapon center
        wcx, wcy = (x1 + x2) // 2, (y1 + y2) // 2
        cv2.circle(annotated_image, (wcx, wcy), 6, color, -1)
        
        # Build label
        label = f"{det.class_name} {det.confidence:.2f}"
        if pair.status == "held_by_person":
            label += f" | {pair.danger_level.upper()}"
            # Draw thick line to person
            if pair.person_bbox:
                pcx = int((pair.person_bbox.x1 + pair.person_bbox.x2) / 2)
                pcy = int((pair.person_bbox.y1 + pair.person_bbox.y2) / 2)
                cv2.line(annotated_image, (wcx, wcy), (pcx, pcy), (255, 255, 0), 3)
        else:
            label += " | KHONG NGUOI"
        
        # Draw label with background
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(annotated_image, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
        cv2.putText(annotated_image, label, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Save annotated image
    filename = f"{current_user['user_id']}_paired_{file.filename}"
    output_path = os.path.join(settings.UPLOAD_DIR, filename)
    cv2.imwrite(output_path, annotated_image)
    
    weapons_with_persons = sum(1 for p in pairs if p.status == "held_by_person")
    
    # Auto-create alerts for high and medium danger detections
    from backend.app.core.database import get_database
    db = get_database()
    for pair in pairs:
        if pair.danger_level in ["high", "medium"]:
            alert_data = {
                "weapon_class": pair.weapon.class_name,
                "confidence": pair.weapon.confidence,
                "status": pair.status,
                "danger_level": pair.danger_level,
                "distance": pair.distance,
                "image_path": f"/api/v1/detection/image/{filename}",
                "location": "Image Upload",
                "timestamp": datetime.utcnow(),
                "acknowledged": False
            }
            try:
                await db.alerts.insert_one(alert_data)
            except Exception as e:
                print(f"Failed to create alert: {e}")
    
    return PairingDetectionResponse(
        pairs=pairs,
        processing_time=processing_time,
        image_url=f"/api/v1/detection/image/{filename}",
        model_used=model_used,
        total_weapons=len(pairs),
        weapons_with_persons=weapons_with_persons
    )


@router.post("/detect/video")
async def detect_video(
    file: UploadFile = File(...),
    confidence: Optional[float] = Form(0.5),
    model_type: Optional[str] = Form("yolo"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a video and run weapon detection frame-by-frame
    
    Args:
        file: Video file (mp4, avi, etc.)
        confidence: Confidence threshold (0.0-1.0)
        model_type: "yolo" or "fasterrcnn"
        
    Returns:
        Processed video with bounding boxes
    """
    # Validate file size
    contents = await file.read()
    max_size = 200 * 1024 * 1024  # 200MB limit
    
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413, 
            detail=f"Video too large (max {max_size // (1024*1024)}MB)"
        )
    
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_id = current_user.get('user_id', 'unknown')
    
    input_filename = f"{user_id}_{timestamp}_input.mp4"
    output_filename = f"{user_id}_{timestamp}_output.mp4"
    
    input_path = os.path.join(settings.UPLOAD_DIR, "videos", input_filename)
    output_path = os.path.join(settings.UPLOAD_DIR, "results", output_filename)
    
    # Save uploaded video
    try:
        with open(input_path, "wb") as f:
            f.write(contents)
        print(f"✅ Saved input video: {input_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")
    
    # Process video
    cap = None
    out = None
    
    try:
        # Open input video
        cap = cv2.VideoCapture(input_path)
        
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Cannot open video file")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"📹 Video info: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        # Initialize video writer with mp4v codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            raise HTTPException(
                status_code=500, 
                detail="Failed to initialize video writer"
            )
        
        # Load detection model
        model = detection_service.load_yolo_model()
        
        # Process frames
        frame_count = 0
        total_detections = 0
        frames_with_weapons = 0
        start_time = time.time()
        
        print("🎬 Starting frame-by-frame processing...")
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break  # End of video
            
            frame_count += 1
            
            # Run weapon detection on this frame
            weapon_results = model.predict(frame, conf=confidence, verbose=False, imgsz=640)[0]
            detections = weapon_results.boxes
            
            # Count detections
            if len(detections) > 0:
                total_detections += len(detections)
                frames_with_weapons += 1
                
                # Draw bounding boxes on frame
                for box in detections:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf_val = float(box.conf)
                    cls = int(box.cls)
                    class_name = weapon_results.names[cls]
                    
                    # Draw red bounding box
                    cv2.rectangle(frame, 
                                (int(x1), int(y1)), (int(x2), int(y2)), 
                                (0, 0, 255), 3)
                    
                    # Add label with class and confidence
                    label = f"{class_name} {conf_val:.0%}"
                    (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                    cv2.rectangle(frame, (int(x1), int(y1) - label_h - 10), 
                                (int(x1) + label_w, int(y1)), (0, 0, 255), -1)
                    cv2.putText(frame, label, (int(x1), int(y1) - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add frame counter overlay
            cv2.putText(
                frame,
                f"Frame: {frame_count}/{total_frames}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            
            # Write annotated frame to output video
            out.write(frame)
            
            # Progress log every 30 frames
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"   Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
        
        # Calculate processing stats
        processing_time = time.time() - start_time
        avg_fps = frame_count / processing_time if processing_time > 0 else 0
        
        print(f"✅ Processing complete!")
        print(f"   Total frames: {frame_count}")
        print(f"   Frames with weapons: {frames_with_weapons}")
        print(f"   Total detections: {total_detections}")
        print(f"   Processing time: {processing_time:.2f}s ({avg_fps:.1f} fps)")
        
        # Cleanup
        cap.release()
        out.release()
        
        # Remove input video to save space
        try:
            os.remove(input_path)
        except:
            pass
        
        # Return result
        return {
            "status": "success",
            "video_url": f"/api/v1/detection/video/result/{output_filename}",
            "stats": {
                "total_frames": frame_count,
                "frames_with_weapons": frames_with_weapons,
                "total_detections": total_detections,
                "processing_time_seconds": round(processing_time, 2),
                "average_fps": round(avg_fps, 1),
                "video_duration_seconds": round(frame_count / fps, 2),
                "resolution": f"{width}x{height}",
                "fps": fps
            },
            "message": f"Processed {frame_count} frames. Found weapons in {frames_with_weapons} frames."
        }
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except PermissionError:
                pass
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except PermissionError:
                pass
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")


@router.get("/video/result/{filename}")
async def get_processed_video(filename: str):
    """
    Download or stream processed video
    
    Args:
        filename: Name of the processed video file
        
    Returns:
        Video file
    """
    file_path = os.path.join(settings.UPLOAD_DIR, "results", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename
    )


@router.delete("/video/result/{filename}")
async def delete_processed_video(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a processed video (cleanup)
    
    Args:
        filename: Name of the video to delete
        
    Returns:
        Success message
    """
    file_path = os.path.join(settings.UPLOAD_DIR, "results", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    try:
        os.remove(file_path)
        return {"message": "Video deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete video: {str(e)}"
        )


@router.get("/video/{filename}")
async def get_video_file(filename: str):
    """Serve processed video file (legacy endpoint)"""
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type="video/mp4")


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

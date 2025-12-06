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

from app.core.config import settings
from app.core.security import get_current_user
from app.services.detection_service import detection_service
from app.services.alert_service import telegram_alert
from app.services.person_weapon_analyzer import person_weapon_analyzer
from app.schemas.detection import DetectionResponse, Detection

router = APIRouter()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/detect/image", response_model=DetectionResponse)
async def detect_image(
    file: UploadFile = File(...),
    confidence: Optional[float] = Form(0.5),
    model_type: Optional[str] = Form("yolo"),
    # current_user: dict = Depends(get_current_user)  # Disabled for testing
):
    # Mock user for testing
    current_user = {'user_id': 'test_user'}
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
    
    # Save alerts to MongoDB for detected weapons
    if len(detections) > 0:
        from app.core.database import get_database
        db = get_database()
        
        # === ANALYZE PERSON-WEAPON RELATIONSHIP ===
        # Detect persons in image
        person_detections = person_weapon_analyzer.detect_persons(image, conf_threshold=0.5)
        person_count = len(person_detections)
        
        # Convert detections to dict format for analyzer
        weapon_dicts = []
        for det in detections:
            weapon_dicts.append({
                'label': det.class_name,
                'confidence': det.confidence,
                'bbox': [int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)]
            })
        
        # Analyze relationship
        analyzed_weapons = person_weapon_analyzer.analyze_weapon_person_relationship(
            weapon_dicts, 
            person_detections
        )
        
        # Determine overall threat
        danger_level, status_msg = person_weapon_analyzer.determine_overall_threat(
            analyzed_weapons,
            person_count
        )
        
        print(f"🔍 Image Analysis: {person_count} person(s), {len(detections)} weapon(s) - Status: {status_msg}")
        
        for det in detections:
            alert_data = {
                "weapon_class": det.class_name,
                "confidence": det.confidence,
                "danger_level": danger_level,
                "image_path": f"/api/v1/detection/image/{filename}",
                "location": "Image Upload Detection",
                "camera_id": f"upload_{current_user['user_id']}",
                "timestamp": datetime.utcnow(),
                "bbox": {
                    "x1": det.bbox.x1,
                    "y1": det.bbox.y1,
                    "x2": det.bbox.x2,
                    "y2": det.bbox.y2
                },
                "acknowledged": False
            }
            try:
                await db.alerts.insert_one(alert_data)
                print(f"✅ Alert saved: {det.class_name} ({danger_level})")
            except Exception as e:
                print(f"❌ Failed to save alert: {e}")
        
        # Send Telegram alert with annotated image (skip cooldown for uploads)
        telegram_alert.send_alert(
            camera_id=f"upload_{current_user['user_id']}",
            image=annotated_image,
            message=status_msg,
            detections=detections,
            skip_cooldown=True
        )
    
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
    # current_user: dict = Depends(get_current_user)  # Disabled for testing
):
    # Mock user for testing
    current_user = {'user_id': 'test_user'}
    """
    Upload an image and run weapon detection with person-weapon pairing
    
    Args:
        file: Image file (jpg, png, etc.)
        confidence: Confidence threshold (0.0-1.0)
        model_type: "yolo" or "fasterrcnn"
        
    Returns:
        Detection results with person-weapon pairing
    """
    from app.schemas.detection import PairingDetectionResponse
    
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
    from app.core.database import get_database
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
    # current_user: dict = Depends(get_current_user)  # Disabled for testing
):
    # Mock user for testing
    current_user = {'user_id': 'test_user'}
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
        
        # Process frames with optimization
        frame_count = 0
        processed_count = 0
        total_detections = 0
        frames_with_weapons = 0
        start_time = time.time()
        best_detection_frame = None  # Store frame with most detections for alert
        max_detections_in_frame = 0
        best_frame_detections = []
        
        # OPTIMIZATION: Skip frames for faster processing
        # Process every Nth frame (2 = 50% faster, 3 = 66% faster)
        skip_frames = 2 if total_frames > 1000 else 1
        
        # AUTO-DETECT GRID: Check if this is a multi-camera grid (2x2, 3x3, etc.)
        # Multi-cam videos usually have aspect ratio ~2:1 or black divider lines
        aspect_ratio = width / height
        is_grid_video = (1.8 < aspect_ratio < 2.2)  # Likely 2x2 grid
        
        grid_cols, grid_rows = (2, 2) if is_grid_video else (1, 1)
        cell_width = width // grid_cols
        cell_height = height // grid_rows
        
        if is_grid_video:
            print(f"📹 Multi-camera grid detected: {grid_cols}x{grid_rows} layout")
            print(f"   Each cell: {cell_width}x{cell_height}")
        
        print(f"🎬 Starting frame processing (skip={skip_frames})...")
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break  # End of video
            
            frame_count += 1
            
            # Skip frames for performance
            if frame_count % skip_frames != 0:
                # Write original frame without detection
                out.write(frame)
                continue
            
            processed_count += 1
            
            # GRID PROCESSING: Detect each cell separately for multi-camera videos
            all_detections = []
            
            if is_grid_video:
                # Process each grid cell independently
                for row in range(grid_rows):
                    for col in range(grid_cols):
                        # Extract cell region
                        x1 = col * cell_width
                        y1 = row * cell_height
                        x2 = x1 + cell_width
                        y2 = y1 + cell_height
                        
                        cell = frame[y1:y2, x1:x2]
                        
                        # Resize cell for detection
                        cell_resized = cv2.resize(cell, (640, 480))
                        
                        # Detect in this cell
                        cell_results = model.predict(cell_resized, conf=confidence, verbose=False, imgsz=640)[0]
                        
                        # Scale detections back to cell coordinates
                        scale_x = cell_width / 640
                        scale_y = cell_height / 480
                        
                        for box in cell_results.boxes:
                            cx1, cy1, cx2, cy2 = box.xyxy[0].cpu().numpy()
                            
                            # Transform to full frame coordinates
                            box.xyxy[0][0] = cx1 * scale_x + x1
                            box.xyxy[0][1] = cy1 * scale_y + y1
                            box.xyxy[0][2] = cx2 * scale_x + x1
                            box.xyxy[0][3] = cy2 * scale_y + y1
                            
                            all_detections.append(box)
                
                # Create pseudo results object
                class PseudoResults:
                    def __init__(self, boxes, names):
                        self.boxes = boxes
                        self.names = names
                
                weapon_results = PseudoResults(all_detections, model.names)
                detections = all_detections
            else:
                # Single frame detection (original logic)
                # Resize for detection (faster inference)
                detect_frame = cv2.resize(frame, (640, 480)) if width > 640 else frame
                scale_x = width / detect_frame.shape[1]
                scale_y = height / detect_frame.shape[0]
                
                # Run weapon detection on resized frame
                weapon_results = model.predict(detect_frame, conf=confidence, verbose=False, imgsz=640)[0]
                detections = weapon_results.boxes
            
            # Count detections
            if len(detections) > 0:
                total_detections += len(detections)
                frames_with_weapons += 1
                
                # Keep best frame for Telegram alert
                if len(detections) > max_detections_in_frame:
                    max_detections_in_frame = len(detections)
                    best_detection_frame = frame.copy()
                    best_frame_detections = []
                    
                    for box in detections:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf_val = float(box.conf)
                        cls = int(box.cls)
                        class_name = weapon_results.names[cls]
                        
                        # Store detection info for Telegram
                        from app.schemas.detection import BBox
                        det_obj = type('Detection', (), {
                            'class_name': class_name,
                            'confidence': conf_val,
                            'bbox': BBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))
                        })()
                        best_frame_detections.append(det_obj)
                
                # Draw bounding boxes on ORIGINAL frame
                for box in detections:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf_val = float(box.conf)
                    cls = int(box.cls)
                    class_name = weapon_results.names[cls]
                    
                    # For grid video, coordinates already transformed
                    # For single video, scale coordinates back
                    if is_grid_video:
                        x1_scaled, y1_scaled = int(x1), int(y1)
                        x2_scaled, y2_scaled = int(x2), int(y2)
                    else:
                        x1_scaled = int(x1 * scale_x)
                        y1_scaled = int(y1 * scale_y)
                        x2_scaled = int(x2 * scale_x)
                        y2_scaled = int(y2 * scale_y)
                    
                    # Draw red bounding box on original frame
                    cv2.rectangle(frame, 
                                (x1_scaled, y1_scaled), (x2_scaled, y2_scaled), 
                                (0, 0, 255), 3)
                    
                    # Add label with class and confidence
                    label = f"{class_name} {conf_val:.0%}"
                    font_scale = 0.7 * (width / 1280)  # Scale font with video size
                    thickness = max(1, int(2 * (width / 1280)))
                    (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                    cv2.rectangle(frame, (x1_scaled, y1_scaled - label_h - 10), 
                                (x1_scaled + label_w, y1_scaled), (0, 0, 255), -1)
                    cv2.putText(frame, label, (x1_scaled, y1_scaled - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
            
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
                fps_current = processed_count / (time.time() - start_time) if processed_count > 0 else 0
                print(f"   Progress: {progress:.1f}% ({frame_count}/{total_frames}) - {fps_current:.1f} fps")
        
        # Calculate processing stats
        processing_time = time.time() - start_time
        avg_fps = processed_count / processing_time if processing_time > 0 else 0
        
        print(f"✅ Processing complete!")
        print(f"   Total frames: {frame_count}")
        print(f"   Processed frames: {processed_count} (skip={skip_frames})")
        print(f"   Frames with weapons: {frames_with_weapons}")
        print(f"   Total detections: {total_detections}")
        print(f"   Processing time: {processing_time:.2f}s ({avg_fps:.1f} fps)")
        print(f"   Speed improvement: {skip_frames}x faster")
        
        # Save alert to MongoDB if weapons detected
        if total_detections > 0:
            from app.core.database import get_database
            db = get_database()
            
            # Determine danger level based on frequency
            detection_rate = frames_with_weapons / frame_count
            if detection_rate > 0.5:
                danger_level = "high"
                status_msg = f"High Risk - Weapons in {detection_rate*100:.0f}% of frames"
            elif detection_rate > 0.2:
                danger_level = "medium"
                status_msg = f"Multiple Detections - {frames_with_weapons} frames affected"
            else:
                danger_level = "low"
                status_msg = f"Low Frequency - {total_detections} detections"
            
            alert_data = {
                "weapon_class": "multiple",
                "confidence": 0.0,  # Average not calculated here
                "danger_level": danger_level,
                "image_path": f"/api/v1/detection/video/result/{output_filename}",
                "location": "Video Upload Detection",
                "camera_id": f"video_{user_id}",
                "timestamp": datetime.utcnow(),
                "video_stats": {
                    "total_frames": frame_count,
                    "frames_with_weapons": frames_with_weapons,
                    "total_detections": total_detections,
                    "detection_rate": round(detection_rate * 100, 2)
                },
                "acknowledged": False
            }
            try:
                await db.alerts.insert_one(alert_data)
                print(f"✅ Video alert saved: {total_detections} detections ({danger_level})")
            except Exception as e:
                print(f"❌ Failed to save video alert: {e}")
            
            # Send Telegram alert with best detection frame
            if best_detection_frame is not None and len(best_frame_detections) > 0:
                # === ANALYZE PERSON-WEAPON IN BEST FRAME ===
                person_detections = person_weapon_analyzer.detect_persons(best_detection_frame, conf_threshold=0.5)
                person_count = len(person_detections)
                
                # Convert detections for analyzer
                weapon_dicts = []
                for det in best_frame_detections:
                    weapon_dicts.append({
                        'label': det.class_name,
                        'confidence': det.confidence,
                        'bbox': [int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)]
                    })
                
                analyzed_weapons = person_weapon_analyzer.analyze_weapon_person_relationship(
                    weapon_dicts,
                    person_detections
                )
                
                # Update status with person analysis
                _, analyzed_status = person_weapon_analyzer.determine_overall_threat(
                    analyzed_weapons,
                    person_count
                )
                
                # Annotate the best frame with persons and weapons
                alert_frame = best_detection_frame.copy()
                
                # Draw persons in green
                for person in person_detections:
                    px1, py1, px2, py2 = person['bbox']
                    cv2.rectangle(alert_frame, (px1, py1), (px2, py2), (0, 255, 0), 2)
                    cv2.putText(alert_frame, f"Person {person['confidence']:.2f}", 
                               (px1, py1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Draw weapons in red
                for i, det in enumerate(best_frame_detections):
                    x1, y1 = int(det.bbox.x1), int(det.bbox.y1)
                    x2, y2 = int(det.bbox.x2), int(det.bbox.y2)
                    
                    cv2.rectangle(alert_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    
                    # Get status from analysis
                    status = analyzed_weapons[i].get('status', 'unknown') if i < len(analyzed_weapons) else 'unknown'
                    status_text = person_weapon_analyzer.get_status_vietnamese(status)
                    
                    label = f"{det.class_name} {det.confidence:.0%}"
                    cv2.putText(alert_frame, label, (x1, y1 - 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(alert_frame, status_text, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                print(f"🎬 Video Analysis: {person_count} person(s) in best frame - {analyzed_status}")
                
                telegram_alert.send_alert(
                    camera_id=f"video_{user_id}",
                    image=alert_frame,
                    message=f"{analyzed_status} (Video)",
                    detections=best_frame_detections,
                    skip_cooldown=True
                )
        
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

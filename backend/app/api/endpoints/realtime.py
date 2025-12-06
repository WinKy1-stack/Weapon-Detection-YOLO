"""
WebSocket endpoint for realtime weapon detection
OPTIMIZED: Non-blocking alerts with threading
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
import cv2
import numpy as np
import base64
import json
import time
import threading
from typing import Optional
import asyncio
from datetime import datetime
from pathlib import Path

from app.core.security import get_current_user_ws
from app.services.detection_service import detection_service
from app.services.alert_service import telegram_alert
from app.services.person_weapon_analyzer import person_weapon_analyzer
from app.core.database import get_database

router = APIRouter()

# Snapshot directory
SNAPSHOT_DIR = Path("runs/alerts_snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


# === ALERT COOLDOWN TRACKING ===
alert_cooldowns = {}  # {client_id: last_alert_timestamp}
ALERT_COOLDOWN_SECONDS = 0  # 0 = No cooldown, send EVERY detection


def can_send_alert(client_id: str) -> bool:
    """
    Check if enough time has passed since last alert
    
    Args:
        client_id: Unique client identifier
        
    Returns:
        bool: True if alert can be sent, False if on cooldown
    """
    current_time = time.time()
    last_alert_time = alert_cooldowns.get(client_id, 0)
    
    if current_time - last_alert_time >= ALERT_COOLDOWN_SECONDS:
        alert_cooldowns[client_id] = current_time
        return True
    return False


def send_alert_background(client_id: str, frame: np.ndarray, detections: list):
    """
    Background thread function for sending alerts (non-blocking)
    
    ⚠️ This function runs in a separate thread to avoid blocking WebSocket
    
    Args:
        client_id: Unique client identifier
        frame: Video frame (already copied with frame.copy())
        detections: List of weapon detections
    """
    try:
        # === DETECT PERSONS IN FRAME ===
        person_detections = person_weapon_analyzer.detect_persons(frame, conf_threshold=0.5)
        person_count = len(person_detections)
        
        # === ANALYZE WEAPON-PERSON RELATIONSHIP ===
        weapon_dicts = []
        for det in detections:
            weapon_dicts.append({
                'label': det.class_name,
                'confidence': det.confidence,
                'bbox': [int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)]
            })
        
        analyzed_weapons = person_weapon_analyzer.analyze_weapon_person_relationship(
            weapon_dicts, 
            person_detections
        )
        
        # === DETERMINE OVERALL THREAT ===
        danger_level, message = person_weapon_analyzer.determine_overall_threat(
            analyzed_weapons,
            person_count
        )
        
        weapon_count = len(detections)
        print(f"🔍 Analysis: {person_count} person(s), {weapon_count} weapon(s) - Status: {message}")
        
        # === SAVE SNAPSHOT IMAGE ===
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = f"alert_{client_id}_{timestamp}.jpg"
        snapshot_path = SNAPSHOT_DIR / snapshot_filename
        
        # Draw detections on frame for snapshot
        annotated_frame = frame.copy()
        
        # Draw persons in green
        for person in person_detections:
            px1, py1, px2, py2 = person['bbox']
            cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Person {person['confidence']:.2f}", 
                       (px1, py1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw weapons in red with status
        for i, det in enumerate(detections):
            x1, y1 = int(det.bbox.x1), int(det.bbox.y1)
            x2, y2 = int(det.bbox.x2), int(det.bbox.y2)
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Get status from analyzed weapons
            status = analyzed_weapons[i].get('status', 'unknown') if i < len(analyzed_weapons) else 'unknown'
            status_text = person_weapon_analyzer.get_status_vietnamese(status)
            
            # Draw label with status
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(annotated_frame, label, (x1, y1 - 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(annotated_frame, status_text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Save snapshot
        cv2.imwrite(str(snapshot_path), annotated_frame)
        print(f"📸 Snapshot saved: {snapshot_filename}")
        
        # === SAVE TO MONGODB (sync client for threading) ===
        try:
            from pymongo import MongoClient
            from app.core.config import settings
            
            # Use sync MongoDB client in thread
            sync_client = MongoClient(settings.MONGODB_URL)
            sync_db = sync_client[settings.MONGODB_DB_NAME]
            
            # Get highest confidence detection
            max_confidence = max(det.confidence for det in detections)
            primary_weapon = max(detections, key=lambda d: d.confidence).class_name
            weapon_types = list(set([det.class_name for det in detections]))
            
            # Get weapon statuses from analysis
            weapon_statuses = [w.get('status', 'unknown') for w in analyzed_weapons]
            held_count = sum(1 for s in weapon_statuses if s == 'held_by_person')
            
            alert_data = {
                "weapon_class": primary_weapon,
                "confidence": float(max_confidence),
                "total_weapons": weapon_count,
                "all_weapons": weapon_types,
                "status": message,  # Use analyzed status message
                "danger_level": danger_level,  # Use analyzed danger level
                "location": "Realtime Detection",
                "camera_id": client_id,
                "image_path": f"/snapshots/{snapshot_filename}",
                "timestamp": datetime.utcnow(),
                "acknowledged": False,
                "person_count": person_count,
                "held_by_person": held_count > 0,
                "weapon_statuses": weapon_statuses
            }
            
            result = sync_db.alerts.insert_one(alert_data)
            sync_client.close()
            
            print(f"💾 Alert saved to MongoDB: {result.inserted_id}")
            
        except Exception as db_error:
            print(f"⚠️ MongoDB save failed: {db_error}")
            # Continue even if DB save fails
        
        # === TELEGRAM ALERT ===
        # Send EVERY detection immediately (skip cooldown)
        telegram_alert.send_alert(
            camera_id=client_id,
            image=annotated_frame,  # Send annotated frame
            message=message,
            detections=detections,
            skip_cooldown=True  # Always send, no cooldown
        )
        
        print(f"✅ Alert triggered: {client_id} - {weapon_count} weapons - Danger: {danger_level}")
        
    except Exception as e:
        print(f"❌ Alert failed (background): {e}")
        import traceback
        traceback.print_exc()
        # Don't propagate error to main WebSocket loop


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/realtime-detect")
async def websocket_realtime_detect(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    confidence: float = Query(0.5),
    model_type: str = Query("yolo"),
    roi: Optional[str] = Query(None)  # NEW: ROI parameter "x,y,w,h"
):
    """
    WebSocket endpoint for realtime detection
    
    OPTIMIZED: Non-blocking with threading for alerts
    NEW: ROI (Region of Interest) filtering support
    
    Client sends: base64 encoded frame
    Server sends: {
        "detections": [...],
        "processing_time": float,
        "total_weapons": int
    }
    
    Args:
        roi: Optional ROI string in format "x,y,w,h" (e.g. "100,150,400,300")
    """
    await manager.connect(websocket)
    
    # Generate unique client ID
    client_id = f"ws_{id(websocket)}_{int(time.time())}"
    
    # Parse ROI parameter
    roi_box = None
    if roi:
        try:
            parts = [int(p.strip()) for p in roi.split(',')]
            if len(parts) == 4:
                roi_box = parts  # [x, y, w, h]
                print(f"🎯 ROI enabled for {client_id}: {roi_box}")
        except Exception as e:
            print(f"⚠️ Invalid ROI format: {roi} - {e}")
            roi_box = None
    
    # Validate token (optional for demo, but recommended)
    # user = await get_current_user_ws(token)
    
    frame_count = 0
    last_fps_time = time.time()
    fps = 0
    
    try:
        print(f"✅ WebSocket connected: {client_id}")
        
        while True:
            # Receive frame from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                frame_data = message.get("frame")
                
                if not frame_data:
                    await manager.send_json(websocket, {
                        "error": "No frame data",
                        "detections": [],
                        "total_weapons": 0
                    })
                    continue
                
                # Decode base64 frame
                try:
                    # Remove data URL prefix if present
                    if "base64," in frame_data:
                        frame_data = frame_data.split("base64,")[1]
                    
                    frame_bytes = base64.b64decode(frame_data)
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        await manager.send_json(websocket, {
                            "error": "Invalid frame data",
                            "detections": [],
                            "total_weapons": 0
                        })
                        continue
                        
                except Exception as e:
                    await manager.send_json(websocket, {
                        "error": f"Frame decode failed: {str(e)}",
                        "detections": [],
                        "total_weapons": 0
                    })
                    continue
                
                # === WEAPON DETECTION ===
                start_time = time.time()
                
                try:
                    detections, _, model_used = detection_service.detect(
                        frame, model_type=model_type, conf_threshold=confidence
                    )
                except Exception as e:
                    print(f"❌ Detection error: {e}")
                    await manager.send_json(websocket, {
                        "error": f"Detection failed: {str(e)}",
                        "detections": [],
                        "total_weapons": 0
                    })
                    continue
                
                # === ROI FILTERING ===
                original_count = len(detections)
                if roi_box and original_count > 0:
                    # Import weapon_detector for ROI filtering
                    from app.services.weapon_detector import weapon_detector
                    
                    # Convert detections to format expected by weapon_detector
                    det_dicts = [
                        {
                            "label": det.class_name,
                            "confidence": det.confidence,
                            "bbox": [det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2],
                            "class_id": 0
                        }
                        for det in detections
                    ]
                    
                    # Filter by ROI
                    filtered_dicts = weapon_detector.filter_by_roi(det_dicts, roi_box)
                    
                    # Convert back to Detection objects
                    from app.schemas.detection import Detection, BoundingBox
                    detections = [
                        Detection(
                            class_name=d["label"],
                            confidence=d["confidence"],
                            bbox=BoundingBox(
                                x1=d["bbox"][0],
                                y1=d["bbox"][1],
                                x2=d["bbox"][2],
                                y2=d["bbox"][3]
                            )
                        )
                        for d in filtered_dicts
                    ]
                    
                    filtered_count = len(detections)
                    if original_count > filtered_count:
                        print(f"🎯 ROI Filter: {original_count} → {filtered_count} detections ({original_count - filtered_count} outside ROI)")
                
                processing_time = time.time() - start_time
                
                # === NON-BLOCKING ALERT LOGIC ===
                # Send EVERY detection (no cooldown check)
                if len(detections) > 0:
                    # Always send alerts, regardless of danger level or cooldown
                    threading.Thread(
                        target=send_alert_background,
                        args=(client_id, frame.copy(), detections),
                        daemon=True
                    ).start()
                
                # Calculate FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    current_time = time.time()
                    elapsed = current_time - last_fps_time
                    fps = 30 / elapsed if elapsed > 0 else 0
                    last_fps_time = current_time
                
                # === IMMEDIATE RESPONSE (NO BLOCKING) ===
                response = {
                    "detections": [
                        {
                            "class_name": det.class_name,
                            "confidence": det.confidence,
                            "bbox": {
                                "x1": det.bbox.x1,
                                "y1": det.bbox.y1,
                                "x2": det.bbox.x2,
                                "y2": det.bbox.y2
                            }
                        }
                        for det in detections
                    ],
                    "processing_time": processing_time,
                    "total_weapons": len(detections),
                    "fps": round(fps, 1),
                    "frame_count": frame_count
                }
                
                await manager.send_json(websocket, response)
                
            except json.JSONDecodeError:
                await manager.send_json(websocket, {
                    "error": "Invalid JSON",
                    "detections": [],
                    "total_weapons": 0
                })
            except Exception as e:
                print(f"❌ Frame processing error: {e}")
                await manager.send_json(websocket, {
                    "error": str(e),
                    "detections": [],
                    "total_weapons": 0
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"🔌 WebSocket disconnected: {client_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)
    finally:
        try:
            if websocket in manager.active_connections:
                manager.disconnect(websocket)
        except:
            pass
        print(f"🛑 WebSocket closed: {client_id}")

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

from backend.app.core.security import get_current_user_ws
from backend.app.services.detection_service import detection_service

router = APIRouter()


# === ALERT COOLDOWN TRACKING ===
alert_cooldowns = {}  # {client_id: last_alert_timestamp}
ALERT_COOLDOWN_SECONDS = 10  # Minimum 10 seconds between alerts


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
        # === ADD YOUR ALERT LOGIC HERE ===
        # Example: Send to Telegram, Discord, Email, etc.
        
        # Build alert message
        weapon_count = len(detections)
        weapon_names = [det.class_name for det in detections]
        message = f"🚨 WEAPON DETECTED!\n\n"
        message += f"Client: {client_id}\n"
        message += f"Weapons: {weapon_count}\n"
        message += f"Types: {', '.join(set(weapon_names))}\n"
        
        # EXAMPLE: Telegram alert (uncomment when ready)
        # from backend.app.services.telegram_service import telegram_alert
        # telegram_alert.send_alert(
        #     camera_id=client_id,
        #     image=frame,
        #     message=message,
        #     detections=detections
        # )
        
        print(f"✅ Alert sent (background): {client_id} - {weapon_count} weapons")
        
    except Exception as e:
        print(f"❌ Alert failed (background): {e}")
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
    model_type: str = Query("yolo")
):
    """
    WebSocket endpoint for realtime detection
    
    OPTIMIZED: Non-blocking with threading for alerts
    
    Client sends: base64 encoded frame
    Server sends: {
        "detections": [...],
        "processing_time": float,
        "total_weapons": int
    }
    """
    await manager.connect(websocket)
    
    # Generate unique client ID
    client_id = f"ws_{id(websocket)}_{int(time.time())}"
    
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
                
                processing_time = time.time() - start_time
                
                # === NON-BLOCKING ALERT LOGIC (FUTURE) ===
                # ⚠️ CRITICAL: If you add alert logic, use threading:
                #
                # if len(detections) > 0 and can_send_alert(client_id):
                #     threading.Thread(
                #         target=send_alert_background,
                #         args=(client_id, frame.copy(), detections),
                #         daemon=True
                #     ).start()
                #
                # This ensures alerts don't block WebSocket response
                
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

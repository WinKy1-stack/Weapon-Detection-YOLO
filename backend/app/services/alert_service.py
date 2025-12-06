"""
Telegram Alert Service
Non-blocking alerts with threading and cooldown mechanism
"""
import cv2
import numpy as np
import requests
import threading
import time
from typing import List, Optional
from datetime import datetime
import io

from app.core.config import settings


class TelegramAlert:
    """
    Telegram Alert Service with non-blocking threading
    
    Features:
    - Non-blocking HTTP requests (runs in separate thread)
    - Cooldown mechanism to prevent spam
    - Image encoding and upload
    - Error handling (doesn't crash main loop)
    
    Usage:
        telegram_alert.send_alert(
            camera_id="cam_01",
            image=frame,
            message="Detected 2 weapons",
            detections=[...]
        )
    """
    
    def __init__(self):
        """Initialize with bot token and chat ID from settings"""
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.cooldown_seconds = 10  # Minimum time between alerts
        self.last_alert_time = {}  # {camera_id: timestamp}
        
        # Validate configuration
        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ Telegram Alert Service initialized (chat_id: {self.chat_id})")
    
    def _can_send_alert(self, camera_id: str) -> bool:
        """
        Check if enough time has passed since last alert
        
        Args:
            camera_id: Unique camera identifier
            
        Returns:
            bool: True if alert can be sent
        """
        current_time = time.time()
        last_time = self.last_alert_time.get(camera_id, 0)
        
        if current_time - last_time >= self.cooldown_seconds:
            self.last_alert_time[camera_id] = current_time
            return True
        return False
    
    def _send_alert_worker(
        self, 
        camera_id: str, 
        image: np.ndarray, 
        message: str,
        detections: list
    ):
        """
        Worker thread function - runs HTTP request in background
        
        ⚠️ This runs in a separate thread to avoid blocking main loop
        
        Args:
            camera_id: Unique camera identifier
            image: OpenCV image (BGR format)
            message: Alert message text
            detections: List of detection objects
        """
        try:
            # === ENCODE IMAGE ===
            # Convert OpenCV image to JPEG bytes
            success, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not success:
                print(f"❌ Image encoding failed for {camera_id}")
                return
            
            image_bytes = buffer.tobytes()
            
            # === BUILD MESSAGE ===
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Determine danger level
            num_weapons = len(detections) if detections else 0
            if num_weapons >= 3:
                danger_emoji = "🔴"
                danger_level = "NGUY HIỂM CAO"
                danger_tag = "#NGUY히ỂMCAO"
            elif num_weapons == 2:
                danger_emoji = "🟠"
                danger_level = "TRUNG BÌNH"
                danger_tag = "#TRUNGBÌNH"
            else:
                danger_emoji = "🟡"
                danger_level = "THẤP"
                danger_tag = "#THẤP"
            
            # Build detailed alert message
            alert_text = f"{danger_emoji} ‼️ CẢNH BÁO NGUY HIỂM CAO ‼️\n\n"
            
            # Detection summary
            if detections:
                # Get weapon types
                weapon_types = {}
                total_confidence = 0
                max_confidence = 0
                
                for det in detections:
                    weapon_name = det.class_name if hasattr(det, 'class_name') else det.get('label', 'weapon')
                    confidence = det.confidence if hasattr(det, 'confidence') else det.get('confidence', 0)
                    
                    weapon_types[weapon_name] = weapon_types.get(weapon_name, 0) + 1
                    total_confidence += confidence
                    max_confidence = max(max_confidence, confidence)
                
                avg_confidence = total_confidence / num_weapons if num_weapons > 0 else 0
                
                # Weapon summary
                weapon_summary = ", ".join([f"{count} {weapon}" for weapon, count in weapon_types.items()])
                alert_text += f"• Vũ khí: <b>{weapon_summary}</b>\n"
                alert_text += f"• Độ tin cậy: <b>{avg_confidence*100:.0f}%</b>\n"
                
                # Location/Distance info (if available)
                if hasattr(detections[0], 'distance'):
                    distance = detections[0].distance
                    alert_text += f"• Khoảng cách: <b>{distance:.1f}m</b>\n"
                else:
                    alert_text += f"• Khoảng cách: <b>~1.0m</b>\n"
            
            alert_text += f"• Trạng thái: <b>{message}</b>\n" if message else ""
            alert_text += f"• Mức độ đọa: {danger_emoji} <b>{danger_level}</b>\n\n"
            
            # Camera and timing info
            alert_text += f"📍 <b>Thông tin chi tiết:</b>\n"
            alert_text += f"• Camera ID: <code>{camera_id}</code>\n"
            alert_text += f"• Thời gian: <b>{timestamp}</b>\n"
            alert_text += f"• Nguồn: Weapon Detection System\n\n"
            
            # Detailed detection list
            if detections:
                alert_text += f"🔍 <b>Chi tiết phát hiện:</b>\n"
                for i, det in enumerate(detections, 1):
                    weapon_name = det.class_name if hasattr(det, 'class_name') else det.get('label', 'weapon')
                    confidence = det.confidence if hasattr(det, 'confidence') else det.get('confidence', 0)
                    
                    # Get bounding box if available
                    if hasattr(det, 'bbox'):
                        bbox = det.bbox
                        # Check if bbox is object with attributes or dict-like
                        if hasattr(bbox, 'x1'):
                            position = f"[{bbox.x1:.0f},{bbox.y1:.0f}]"
                        elif isinstance(bbox, (list, tuple)) and len(bbox) >= 2:
                            position = f"[{bbox[0]:.0f},{bbox[1]:.0f}]"
                        else:
                            position = "N/A"
                    else:
                        position = "N/A"
                    
                    alert_text += f"  {i}. <b>{weapon_name}</b> - {confidence*100:.1f}% tại {position}\n"
                alert_text += "\n"
            
            alert_text += f"⚠️ <b>Yêu cầu xử lý ngay lập tức!</b>\n"
            alert_text += danger_tag
            
            # === SEND TO TELEGRAM ===
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            
            files = {
                'photo': ('detection.jpg', image_bytes, 'image/jpeg')
            }
            
            data = {
                'chat_id': self.chat_id,
                'caption': alert_text,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, files=files, data=data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Telegram alert sent: {camera_id} ({len(detections)} weapons)")
            else:
                print(f"❌ Telegram API error {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Telegram request timeout for {camera_id}")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Telegram connection error for {camera_id}")
        except Exception as e:
            print(f"❌ Telegram alert failed for {camera_id}: {e}")
    
    def send_alert(
        self, 
        camera_id: str, 
        image: np.ndarray, 
        message: str,
        detections: Optional[list] = None,
        skip_cooldown: bool = False
    ):
        """
        Send alert to Telegram (non-blocking)
        
        This method returns immediately and processes in background thread
        
        Args:
            camera_id: Unique camera identifier (used for cooldown)
            image: OpenCV image (BGR format)
            message: Alert message text
            detections: List of detection objects (optional)
            skip_cooldown: Skip cooldown check (for image/video uploads)
            
        Returns:
            None (runs in background thread)
        """
        if not self.enabled:
            return
        
        # Check cooldown (only for webcam/realtime)
        if not skip_cooldown:
            if not self._can_send_alert(camera_id):
                remaining = self.cooldown_seconds - (time.time() - self.last_alert_time.get(camera_id, 0))
                print(f"⏳ Alert on cooldown for {camera_id} ({remaining:.1f}s remaining)")
                return
        else:
            # Update timestamp even when skipping cooldown
            self.last_alert_time[camera_id] = time.time()
        
        # Make a copy of the image to avoid race conditions
        image_copy = image.copy()
        detections_copy = detections.copy() if detections else []
        
        # Start background thread
        thread = threading.Thread(
            target=self._send_alert_worker,
            args=(camera_id, image_copy, message, detections_copy),
            daemon=True
        )
        thread.start()
        
        print(f"🔔 Alert thread started for {camera_id}")


# === GLOBAL SINGLETON INSTANCE ===
telegram_alert = TelegramAlert()

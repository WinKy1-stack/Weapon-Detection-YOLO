"""
Camera Stream Service - Handles individual RTSP/camera streams with auto-reconnection
"""
import cv2
import threading
import time
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CameraStream:
    """
    Manages a single camera stream in a background thread with auto-reconnection
    """
    
    def __init__(self, camera_id: str, rtsp_url: str, reconnect_interval: int = 5):
        """
        Initialize camera stream
        
        Args:
            camera_id: Unique identifier for this camera
            rtsp_url: RTSP URL or camera index (0 for webcam)
            reconnect_interval: Seconds to wait before reconnection attempts
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.reconnect_interval = reconnect_interval
        
        # Thread control
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Frame storage
        self._frame: Optional[np.ndarray] = None
        self._last_frame_time = 0
        
        # Connection state
        self._is_connected = False
        self._connection_attempts = 0
        self._cap: Optional[cv2.VideoCapture] = None
        
        logger.info(f"[{self.camera_id}] CameraStream initialized for {rtsp_url}")
    
    def start(self) -> bool:
        """
        Start the background thread to read frames
        
        Returns:
            bool: True if started successfully
        """
        if self._thread is not None and self._thread.is_alive():
            logger.warning(f"[{self.camera_id}] Stream already running")
            return False
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"[{self.camera_id}] Background thread started")
        return True
    
    def _connect(self) -> bool:
        """
        Attempt to connect to the camera
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Release previous capture if exists
            if self._cap is not None:
                self._cap.release()
            
            # Try to open camera
            # If rtsp_url is a digit string, convert to int for webcam
            source = int(self.rtsp_url) if self.rtsp_url.isdigit() else self.rtsp_url
            self._cap = cv2.VideoCapture(source)
            
            # Set buffer size to 1 to reduce latency
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test if camera opened successfully
            if not self._cap.isOpened():
                logger.error(f"[{self.camera_id}] Failed to open camera")
                return False
            
            # Try to read one frame to verify connection
            ret, frame = self._cap.read()
            if not ret or frame is None:
                logger.error(f"[{self.camera_id}] Camera opened but cannot read frame")
                self._cap.release()
                return False
            
            # Store first frame
            with self._lock:
                self._frame = frame
                self._last_frame_time = time.time()
                self._is_connected = True
                self._connection_attempts = 0
            
            logger.info(f"[{self.camera_id}] ✅ Connected successfully (Resolution: {frame.shape[1]}x{frame.shape[0]})")
            return True
            
        except Exception as e:
            logger.error(f"[{self.camera_id}] Connection error: {str(e)}")
            return False
    
    def _capture_loop(self):
        """
        Main loop that continuously reads frames from camera
        Runs in background thread
        """
        logger.info(f"[{self.camera_id}] Capture loop started")
        
        while not self._stop_event.is_set():
            # If not connected, try to connect
            if not self._is_connected:
                self._connection_attempts += 1
                logger.info(f"[{self.camera_id}] Connection attempt #{self._connection_attempts}")
                
                if self._connect():
                    continue  # Start reading frames
                else:
                    # Wait before retry
                    logger.warning(f"[{self.camera_id}] Reconnecting in {self.reconnect_interval}s...")
                    time.sleep(self.reconnect_interval)
                    continue
            
            # Try to read frame
            try:
                ret, frame = self._cap.read()
                
                if not ret or frame is None:
                    logger.warning(f"[{self.camera_id}] ❌ Lost connection (frame read failed)")
                    with self._lock:
                        self._is_connected = False
                    continue
                
                # Successfully read frame - store it
                with self._lock:
                    self._frame = frame
                    self._last_frame_time = time.time()
                
                # Small sleep to prevent CPU overload (adjust based on camera FPS)
                time.sleep(0.01)  # ~100 FPS max read rate
                
            except Exception as e:
                logger.error(f"[{self.camera_id}] Error reading frame: {str(e)}")
                with self._lock:
                    self._is_connected = False
                time.sleep(1)
        
        # Cleanup when thread stops
        if self._cap is not None:
            self._cap.release()
        logger.info(f"[{self.camera_id}] Capture loop stopped")
    
    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        """
        Get the most recent frame
        
        Returns:
            tuple: (success: bool, frame: np.ndarray or None)
        """
        with self._lock:
            if self._frame is None:
                return False, None
            
            # Check if frame is stale (older than 5 seconds)
            if time.time() - self._last_frame_time > 5:
                logger.warning(f"[{self.camera_id}] Frame is stale")
                return False, None
            
            return True, self._frame.copy()
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame (simplified version)
        
        Returns:
            np.ndarray or None: Latest frame
        """
        ret, frame = self.read()
        return frame if ret else None
    
    def is_active(self) -> bool:
        """
        Check if stream is active and receiving frames
        
        Returns:
            bool: True if connected and receiving recent frames
        """
        with self._lock:
            return (
                self._is_connected and 
                self._frame is not None and 
                time.time() - self._last_frame_time < 3
            )
    
    def stop(self):
        """
        Stop the capture thread and release resources
        """
        logger.info(f"[{self.camera_id}] Stopping stream...")
        self._stop_event.set()
        
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                logger.warning(f"[{self.camera_id}] Thread did not stop gracefully")
        
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
            self._frame = None
            self._is_connected = False
        
        logger.info(f"[{self.camera_id}] ✅ Stream stopped")
    
    def get_info(self) -> dict:
        """
        Get stream information
        
        Returns:
            dict: Stream status and metadata
        """
        with self._lock:
            return {
                "camera_id": self.camera_id,
                "rtsp_url": self.rtsp_url,
                "is_connected": self._is_connected,
                "is_active": self.is_active(),
                "connection_attempts": self._connection_attempts,
                "last_frame_time": self._last_frame_time,
                "frame_age_seconds": time.time() - self._last_frame_time if self._last_frame_time > 0 else None,
            }

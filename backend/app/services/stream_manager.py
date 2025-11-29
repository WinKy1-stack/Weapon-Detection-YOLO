"""
Stream Manager - Singleton service to manage multiple camera streams
"""
from typing import Dict, Optional
import logging
from backend.app.services.camera_stream import CameraStream

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Singleton manager for multiple camera streams
    """
    _instance: Optional['StreamManager'] = None
    _lock = __import__('threading').Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the stream manager (only once)"""
        if self._initialized:
            return
        
        self._streams: Dict[str, CameraStream] = {}
        self._initialized = True
        logger.info("StreamManager initialized")
    
    def add_stream(self, camera_id: str, rtsp_url: str, auto_start: bool = True) -> bool:
        """
        Add a new camera stream
        
        Args:
            camera_id: Unique identifier for the camera
            rtsp_url: RTSP URL or camera index
            auto_start: Automatically start the stream
            
        Returns:
            bool: True if added successfully
        """
        if camera_id in self._streams:
            logger.warning(f"Camera {camera_id} already exists")
            return False
        
        try:
            stream = CameraStream(camera_id, rtsp_url)
            self._streams[camera_id] = stream
            
            if auto_start:
                stream.start()
            
            logger.info(f"✅ Added camera stream: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add stream {camera_id}: {str(e)}")
            return False
    
    def get_stream(self, camera_id: str) -> Optional[CameraStream]:
        """
        Get a camera stream by ID
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            CameraStream or None
        """
        return self._streams.get(camera_id)
    
    def remove_stream(self, camera_id: str) -> bool:
        """
        Remove and stop a camera stream
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            bool: True if removed successfully
        """
        if camera_id not in self._streams:
            logger.warning(f"Camera {camera_id} not found")
            return False
        
        try:
            stream = self._streams[camera_id]
            stream.stop()
            del self._streams[camera_id]
            logger.info(f"✅ Removed camera stream: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove stream {camera_id}: {str(e)}")
            return False
    
    def list_streams(self) -> Dict[str, dict]:
        """
        Get information about all streams
        
        Returns:
            dict: Camera ID -> Stream info
        """
        return {
            camera_id: stream.get_info()
            for camera_id, stream in self._streams.items()
        }
    
    def stop_all(self):
        """Stop all camera streams"""
        logger.info("Stopping all camera streams...")
        for camera_id in list(self._streams.keys()):
            self.remove_stream(camera_id)
        logger.info("✅ All streams stopped")
    
    def get_active_count(self) -> int:
        """
        Get count of active (connected) streams
        
        Returns:
            int: Number of active streams
        """
        return sum(1 for stream in self._streams.values() if stream.is_active())
    
    def __len__(self) -> int:
        """Get total number of managed streams"""
        return len(self._streams)


# Singleton instance
stream_manager = StreamManager()

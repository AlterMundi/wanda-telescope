"""
Mock camera implementation for development and testing.
"""
import numpy as np
import cv2
import logging
from ..base import AbstractCamera

logger = logging.getLogger(__name__)

class MockCamera(AbstractCamera):
    """Mock camera for development and testing."""
    
    def __init__(self):
        super().__init__()
        self.webcam = None
        self._init_webcam()
        logger.info("Mock camera initialized")
    
    def _init_webcam(self):
        """Try to initialize webcam if available."""
        try:
            self.webcam = cv2.VideoCapture(0)
            if self.webcam.isOpened():
                logger.info("Mock camera: Using webcam for preview")
            else:
                self.webcam = None
                logger.warning("Mock camera: Webcam not available, using random data")
        except Exception as e:
            logger.warning(f"Mock camera: Could not initialize webcam: {e}")
            self.webcam = None
    
    def create_preview_configuration(self, main=None):
        return {"type": "preview", "main": main}
    
    def create_still_configuration(self, main=None, raw=None):
        return {"type": "still", "main": main, "raw": raw}
    
    def create_video_configuration(self, main=None):
        return {"type": "video", "main": main}
    
    def configure(self, config):
        logger.debug(f"Mock camera: configure({config})")
    
    def start(self):
        logger.debug("Mock camera: start()")
        self.started = True
    
    def stop(self):
        logger.debug("Mock camera: stop()")
        self.started = False
    
    def capture_array(self, name="main"):
        """Return webcam frame or dummy data."""
        if self.webcam and self.webcam.isOpened():
            ret, frame = self.webcam.read()
            if ret:
                frame = cv2.resize(frame, (1440, 810))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return frame
        
        # Fallback to dummy image
        return np.random.randint(0, 255, (810, 1440, 3), dtype=np.uint8)
    
    def capture_file(self, filename, name=None):
        """Create dummy image file."""
        logger.debug(f"Mock camera: capture_file({filename}, {name})")
        dummy_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        cv2.imwrite(filename, dummy_image)
    
    def set_controls(self, controls):
        logger.debug(f"Mock camera: set_controls({controls})")
    
    def start_recording(self, encoder, filename):
        logger.debug(f"Mock camera: start_recording({encoder}, {filename})")
    
    def stop_recording(self):
        logger.debug("Mock camera: stop_recording()")
    
    def cleanup(self):
        logger.debug("Mock camera: cleanup()")
        if self.webcam:
            self.webcam.release()
            self.webcam = None

# Mock encoder class
class MockH264Encoder:
    def __init__(self, bitrate=None):
        self.bitrate = bitrate
        logger.info(f"Mock H264Encoder initialized with bitrate={bitrate}")
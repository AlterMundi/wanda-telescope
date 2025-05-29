"""
Mock implementation of picamera2 library for development environment.
This allows development on systems without Raspberry Pi camera hardware.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Picamera2:
    """Mock Picamera2 class that mimics the basic interface."""
    
    def __init__(self):
        logger.info("Mock Picamera2 initialized")
        self.started = False
        self.options = {}  # Add options attribute
        
        # Try to initialize webcam
        self.webcam = None
        try:
            import cv2
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
        """Mock preview configuration."""
        return {"type": "preview", "main": main}
        
    def create_still_configuration(self, main=None, raw=None):
        """Mock still configuration."""
        return {"type": "still", "main": main, "raw": raw}
        
    def create_video_configuration(self, main=None):
        """Mock video configuration."""
        return {"type": "video", "main": main}
        
    def configure(self, config):
        """Mock configure method."""
        logger.debug(f"Mock camera: configure({config})")
        
    def start(self):
        """Mock start method."""
        logger.debug("Mock camera: start()")
        self.started = True
        
    def stop(self):
        """Mock stop method."""
        logger.debug("Mock camera: stop()")
        self.started = False
        
    def capture_array(self, name="main"):
        """Mock capture_array - returns webcam frame or dummy image data."""
        logger.debug(f"Mock camera: capture_array({name})")
        
        if self.webcam and self.webcam.isOpened():
            # Try to get frame from webcam
            ret, frame = self.webcam.read()
            if ret:
                # Resize frame to match expected preview size (1440x810)
                import cv2
                frame = cv2.resize(frame, (1440, 810))
                # Convert BGR to RGB (OpenCV uses BGR, but web interface expects RGB)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return frame
        
        # Fallback to dummy image if webcam not available
        return np.random.randint(0, 255, (810, 1440, 3), dtype=np.uint8)
        
    def capture_file(self, filename, name=None):
        """Mock capture_file - creates dummy image file."""
        logger.debug(f"Mock camera: capture_file({filename}, {name})")
        # Create a small dummy image file
        dummy_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        import cv2
        cv2.imwrite(filename, dummy_image)
        
    def set_controls(self, controls):
        """Mock set_controls method."""
        logger.debug(f"Mock camera: set_controls({controls})")
        
    def start_recording(self, encoder, filename):
        """Mock start_recording method."""
        logger.debug(f"Mock camera: start_recording({encoder}, {filename})")
        
    def stop_recording(self):
        """Mock stop_recording method."""
        logger.debug("Mock camera: stop_recording()")
        
    def cleanup(self):
        """Clean up webcam resources."""
        logger.debug("Mock camera: cleanup()")
        if self.webcam:
            self.webcam.release()
            self.webcam = None


class H264Encoder:
    """Mock H264Encoder class."""
    
    def __init__(self, bitrate=None):
        logger.info(f"Mock H264Encoder initialized with bitrate={bitrate}")
        self.bitrate = bitrate
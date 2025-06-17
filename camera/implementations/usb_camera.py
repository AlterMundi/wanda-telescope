"""
USB camera implementation using OpenCV.
"""
import logging
import cv2
import numpy as np
import math
import time
from ..base import AbstractCamera
from ..exceptions import CameraInitializationError, CameraNotConnectedError
from typing import Tuple, Optional, Any

logger = logging.getLogger(__name__)

class USBCamera(AbstractCamera):
    """USB camera implementation using OpenCV."""
    
    def __init__(self):
        """Initialize the USB camera."""
        super().__init__()  # This will set self.started = False
        self.camera = None
        self.is_recording = False
        self.video_writer = None
        self.status = "USB camera initialized"
        self.exposure_us = 100000  # Default exposure time in microseconds
        self.gain = 1.0  # Default gain value
        self.exposure_mode = "auto"  # Default exposure mode
        self.skip_frames = 0  # Number of frames to skip for performance
        self.performance_mode = "normal"  # Performance mode: normal, fast, fastest
        self.use_digital_gain = False  # Whether to use digital gain
        self.digital_gain = 1.0  # Digital gain value
        self.save_raw = False  # Whether to save raw images
        self.recording = False  # Whether currently recording
        self.capture_status = "Ready"  # Current capture status
        self.capture_dir = "captures"  # Directory for saved images
        logger.info("USB camera initialized")
    
    def initialize(self):
        """Initialize the USB camera hardware."""
        logger.info("USB camera: initialize()")
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Failed to open USB camera")
            self.status = "USB camera ready"
        except Exception as e:
            self.status = f"USB camera error: {str(e)}"
            raise
    
    def configure(self, config=None, **kwargs):
        """Configure camera settings.
        
        Args:
            config: Optional configuration dictionary
            **kwargs: Additional configuration parameters
        """
        logger.info(f"USB camera: configure(config={config}, kwargs={kwargs})")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        # Merge config and kwargs
        settings = {}
        if config:
            settings.update(config)
        settings.update(kwargs)
        
        for key, value in settings.items():
            if hasattr(cv2, key.upper()):
                self.camera.set(getattr(cv2, key.upper()), value)
                if key == 'gain':
                    self.gain = value
                elif key == 'exposure':
                    self.exposure_us = value * 1000  # Convert ms to us
    
    def create_preview_configuration(self):
        """Create preview configuration."""
        return {
            'width': 640,
            'height': 480,
            'fps': 30
        }
    
    def create_still_configuration(self):
        """Create still image configuration."""
        return {
            'width': 1920,
            'height': 1080,
            'format': 'jpg'
        }
    
    def create_video_configuration(self):
        """Create video configuration."""
        return {
            'width': 1280,
            'height': 720,
            'fps': 30,
            'format': 'mp4'
        }
    
    def set_controls(self, **kwargs):
        """Set camera controls."""
        logger.info(f"USB camera: set_controls({kwargs})")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        for key, value in kwargs.items():
            if hasattr(cv2, key.upper()):
                self.camera.set(getattr(cv2, key.upper()), value)
                if key == 'gain':
                    self.gain = value
                elif key == 'exposure':
                    self.exposure_us = value * 1000  # Convert ms to us
    
    def start(self):
        """Start the camera."""
        logger.info("USB camera: start()")
        if not self.camera:
            self.initialize()
        self.started = True
        self.status = "USB camera started"
    
    def stop(self):
        """Stop the camera."""
        logger.info("USB camera: stop()")
        if self.is_recording:
            self.stop_recording()
        if self.camera:
            self.camera.release()
            self.camera = None
        self.started = False
        self.status = "USB camera stopped"
    
    def start_recording(self, filename):
        """Start video recording."""
        logger.info(f"USB camera: start_recording({filename})")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        config = self.create_video_configuration()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            filename,
            fourcc,
            config['fps'],
            (config['width'], config['height'])
        )
        self.is_recording = True
        self.recording = True
        self.status = f"Recording to {filename}"
    
    def stop_recording(self):
        """Stop video recording."""
        logger.info("USB camera: stop_recording()")
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        self.is_recording = False
        self.recording = False
        self.status = "Recording stopped"
    
    def capture_array(self):
        """Capture a frame as a numpy array."""
        logger.info("USB camera: capture_array()")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        # Skip frames if needed for performance
        for _ in range(self.skip_frames):
            self.camera.grab()
        
        ret, frame = self.camera.read()
        if not ret:
            raise Exception("Failed to capture frame")
        
        # Flip the frame horizontally to correct mirroring
        frame = cv2.flip(frame, 1)
        
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)
        
        return frame
    
    def capture_file(self, filename):
        """Capture a still image to a file."""
        logger.info(f"USB camera: capture_file({filename})")
        frame = self.capture_array()
        cv2.imwrite(filename, frame)
    
    def cleanup(self):
        """Clean up camera resources."""
        logger.info("USB camera: cleanup()")
        self.stop()
        self.status = "USB camera cleaned up"
    
    def capture_image(self) -> Tuple[bool, Optional[Any]]:
        """Capture an image from the USB camera.
        
        Returns:
            Tuple[bool, Optional[Any]]: Success status and image data if successful
            
        Raises:
            CameraNotConnectedError: If camera is not initialized
        """
        if not self.is_connected:
            raise CameraNotConnectedError("Camera not initialized")
        try:
            # Implementation will go here
            pass
        except Exception as e:
            return False, None
    
    def start_preview(self) -> bool:
        """Start the camera preview."""
        if not self.is_connected:
            return False
        try:
            # Implementation will go here
            return True
        except:
            return False
    
    def stop_preview(self) -> None:
        """Stop the camera preview."""
        if self.is_recording:
            self.stop_recording()
    
    @property
    def is_connected(self) -> bool:
        """Check if camera is connected and initialized."""
        return self.camera is not None and self.camera.isOpened()
    
    def us_to_shutter_string(self, us):
        """Convert microseconds to a human-readable shutter speed string.
        
        Args:
            us: Exposure time in microseconds
            
        Returns:
            str: Human-readable shutter speed (e.g., "1/1000")
        """
        if us >= 1000000:  # 1 second or longer
            return f"{us/1000000:.1f}s"
        else:
            return f"1/{int(1000000/us)}"
    
    def gain_to_iso(self, gain):
        """Convert gain value to ISO equivalent.
        
        Args:
            gain: Camera gain value
            
        Returns:
            int: Approximate ISO value
        """
        # Simple linear mapping from gain to ISO
        # This is an approximation and may need adjustment based on the camera
        return int(gain * 100)
    
    def iso_to_gain(self, iso):
        """Convert ISO value to gain.
        
        Args:
            iso: ISO value
            
        Returns:
            float: Camera gain value
        """
        return iso / 100.0
    
    def slider_to_us(self, slider_value):
        """Convert slider value to microseconds.
        
        Args:
            slider_value: Slider value (0-1000)
            
        Returns:
            int: Exposure time in microseconds
        """
        min_us = 100
        max_us = 200_000_000
        log_range = math.log(max_us / min_us)
        return int(min_us * math.exp(slider_value * log_range / 1000))
    
    def get_exposure_seconds(self):
        """Get the current exposure time in seconds.
        
        Returns:
            float: Exposure time in seconds
        """
        return self.exposure_us / 1000000.0
    
    def get_exposure_us(self):
        """Get the current exposure time in microseconds.
        
        Returns:
            int: Exposure time in microseconds
        """
        return self.exposure_us
    
    def set_exposure_us(self, us):
        """Set the exposure time in microseconds.
        
        Args:
            us: Exposure time in microseconds
        """
        if not self.camera:
            raise Exception("Camera not initialized")
        self.exposure_us = us
        self.camera.set(cv2.CAP_PROP_EXPOSURE, us / 1000)  # Convert us to ms for OpenCV
    
    def set_performance_mode(self, mode):
        """Set the performance mode.
        
        Args:
            mode: Performance mode ('normal', 'fast', 'fastest')
        """
        self.performance_mode = mode
        if mode == 'normal':
            self.skip_frames = 0
        elif mode == 'fast':
            self.skip_frames = 1
        elif mode == 'fastest':
            self.skip_frames = 2
        else:
            logger.warning(f"Unknown performance mode: {mode}, using normal")
            self.skip_frames = 0
    
    def update_camera_settings(self):
        """Update camera settings based on current values."""
        if not self.camera:
            raise Exception("Camera not initialized")
        
        # Update exposure
        self.camera.set(cv2.CAP_PROP_EXPOSURE, self.exposure_us / 1000)
        
        # Update gain
        self.camera.set(cv2.CAP_PROP_GAIN, self.gain)
        
        # Apply digital gain if enabled
        if self.use_digital_gain:
            # Note: OpenCV doesn't have direct digital gain control
            # This would need to be applied during frame processing
            pass
    
    def get_frame(self):
        """Get a frame as JPEG data.
        
        Returns:
            bytes: JPEG-encoded frame data
        """
        try:
            frame = self.capture_array()
            if frame is not None:
                # Apply digital gain if enabled
                if self.use_digital_gain and self.digital_gain > 1.0:
                    frame = cv2.multiply(frame, self.digital_gain)
                
                # Convert to JPEG
                _, jpeg = cv2.imencode('.jpg', frame)
                return jpeg.tobytes()
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
        return None
    
    def capture_still(self):
        """Capture a still image.
        
        Returns:
            bool: True if capture was successful
        """
        try:
            self.capture_status = "Capturing..."
            frame = self.capture_array()
            
            # Apply digital gain if enabled
            if self.use_digital_gain and self.digital_gain > 1.0:
                frame = cv2.multiply(frame, self.digital_gain)
            
            # Save the image
            filename = f"{self.capture_dir}/capture_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            
            self.capture_status = "Capture complete"
            return True
        except Exception as e:
            self.capture_status = f"Capture failed: {str(e)}"
            logger.error(f"Error capturing still: {e}")
            return False
    
    def start_video(self):
        """Start video recording.
        
        Returns:
            bool: True if recording started successfully
        """
        try:
            filename = f"{self.capture_dir}/video_{int(time.time())}.mp4"
            self.start_recording(filename)
            return True
        except Exception as e:
            logger.error(f"Error starting video: {e}")
            return False
    
    def stop_video(self):
        """Stop video recording.
        
        Returns:
            bool: True if recording stopped successfully
        """
        try:
            self.stop_recording()
            return True
        except Exception as e:
            logger.error(f"Error stopping video: {e}")
            return False 
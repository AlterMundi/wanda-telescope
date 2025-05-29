"""
Camera controller for Wanda astrophotography system.
Handles camera initialization, configuration, and capture operations.
"""
import time
import os
import math
import cv2
import numpy as np
import threading
from datetime import datetime
import logging

try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    MOCK_MODE = False
    logging.getLogger(__name__).info("Using real picamera2 library")
except ImportError:
    from dev_tools.mock_picamera2 import Picamera2, H264Encoder
    MOCK_MODE = True
    logging.getLogger(__name__).info("Using mock picamera2 library (development mode)")


from utils.storage import get_capture_dir
import config

logger = logging.getLogger(__name__)

class CameraController:
    """Controller for camera operations including capturing, recording and streaming."""
    
    def __init__(self):
        """Initialize the camera with default settings."""
        self.camera = Picamera2()
        self.encoder = H264Encoder(bitrate=config.VIDEO_BITRATE)
        
        # Apply camera tuning if available
        camera_tuning = config.load_camera_tuning()
        if camera_tuning:
            self.camera.options["tuning"] = camera_tuning
            logger.info("Applied camera tuning")
        
        # Create camera configurations
        self.preview_config = self.camera.create_preview_configuration(
            main={"size": config.PREVIEW_SIZE}
        )
        self.still_config = self.camera.create_still_configuration(
            main={"size": config.STILL_SIZE},
            raw={"size": config.STILL_SIZE}
        )
        self.video_config = self.camera.create_video_configuration(
            main={"size": config.VIDEO_SIZE}
        )
        
        # Camera state
        self.exposure_us = config.DEFAULT_EXPOSURE_US
        self.gain = config.DEFAULT_GAIN
        self.digital_gain = config.DEFAULT_DIGITAL_GAIN
        self.use_digital_gain = config.USE_DIGITAL_GAIN
        self.save_raw = config.SAVE_RAW
        self.recording = False
        self.capture_status = ""
        self.capture_dir = get_capture_dir()
        
        # Digital gain processing
        self.digital_gain_lut = None
        self.skip_frames = 2
        self.frame_count = 0
        
        # Streaming
        self.streaming = True
        self.frame_buffer = None
        self.buffer_lock = threading.Lock()
        
        # Start camera with preview config
        self.camera.configure(self.preview_config)
        self.camera.start()
        self.update_camera_settings()
        
        if self.use_digital_gain:
            self.create_digital_gain_lut()
            
        # Start the preview thread
        self.preview_thread = threading.Thread(target=self._generate_frames_thread, daemon=True)
        self.preview_thread.start()
        logger.info("Camera controller initialized")
        
    def update_camera_settings(self):
        """Apply current camera settings to the hardware."""
        controls = {
            "ExposureTime": self.exposure_us,
            "AnalogueGain": self.gain
        }
        self.camera.set_controls(controls)
        
        # Update digital gain LUT if enabled
        if self.use_digital_gain and self.digital_gain > 1.0:
            self.create_digital_gain_lut()
            
        logger.info(f"Updated camera settings: {controls}")
        
    def create_digital_gain_lut(self):
        """Create lookup table for fast digital gain application."""
        # Parameters for the enhancement curve
        black_level = 0.028  # Pixels below this remain black
        gamma = 0.7        # Power function for mid-tone boost
        
        # Create a 256-element lookup table for 8-bit images
        lut = np.zeros(256, dtype=np.uint8)
        
        # Calculate each entry in the LUT
        for i in range(256):
            # Normalize to 0-1
            pixel = i / 255.0
            
            # Apply black level threshold
            if pixel <= black_level:
                adjusted = 0
            else:
                adjusted = (pixel - black_level) / (1.0 - black_level)
                
                # Apply gamma correction
                adjusted = np.power(adjusted, gamma)
                
                # Apply digital gain
                adjusted = adjusted * self.digital_gain
            
            # Convert back to 0-255 range and clip
            lut[i] = np.clip(adjusted * 255.0, 0, 255).astype(np.uint8)
        
        self.digital_gain_lut = lut
        logger.info(f"Created digital gain LUT with gain={self.digital_gain}")
    
    def _generate_frames_thread(self):
        """Thread function to continuously capture frames for streaming."""
        while self.streaming:
            try:
                frame = self.camera.capture_array("main")
                
                # Apply digital gain if enabled (only for preview)
                # Process only every nth frame to reduce CPU load
                self.frame_count = (self.frame_count + 1) % (self.skip_frames + 1)
                
                if (self.use_digital_gain and 
                    self.digital_gain > 1.0 and 
                    self.digital_gain_lut is not None and 
                    self.frame_count == 0):
                    try:
                        # Apply the lookup table to all three color channels
                        frame = cv2.LUT(frame, self.digital_gain_lut)
                    except Exception as e:
                        logger.error(f"Error applying LUT: {e}")
                
                # Use lower JPEG quality for preview to reduce CPU usage
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
                ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                
                if ret:
                    with self.buffer_lock:
                        self.frame_buffer = buffer.tobytes()
                
                # Adaptive sleep based on CPU load
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in frame generation: {e}")
                time.sleep(0.5)  # Longer sleep on error
    
    def get_frame(self):
        """Get the latest camera frame for streaming."""
        with self.buffer_lock:
            if self.frame_buffer is not None:
                return self.frame_buffer
            return None
    
    def capture_still(self):
        """Capture a still image."""
        if self.recording:
            self.capture_status = "Cannot capture still while recording video."
            return False
        
        try:
            self.capture_status = "Capturing..."
            # Reconfigure camera for still capture
            self.camera.stop()
            self.camera.configure(self.still_config)
            self.camera.start()
            
            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            jpg_filename = os.path.join(self.capture_dir, f"wanda_{timestamp}.jpg")
            
            # Capture the image (this will block for the duration of the exposure)
            self.camera.capture_file(jpg_filename)
            
            # Save RAW file if enabled
            if self.save_raw:
                dng_filename = os.path.join(self.capture_dir, f"wanda_{timestamp}.dng")
                self.camera.capture_file(dng_filename, name="raw")
                self.capture_status = f"Photo saved as {jpg_filename} and RAW as {dng_filename}"
            else:
                self.capture_status = f"Photo saved as {jpg_filename}"
            
            # Return to preview mode
            self.camera.stop()
            self.camera.configure(self.preview_config)
            self.camera.start()
            
            # Reapply camera settings
            self.update_camera_settings()
            
            logger.info(f"Captured still image: {jpg_filename}")
            return True
            
        except Exception as e:
            self.capture_status = f"Error capturing image: {str(e)}"
            logger.error(f"Error capturing still: {e}")
            
            # Ensure camera returns to preview mode
            try:
                self.camera.stop()
                self.camera.configure(self.preview_config)
                self.camera.start()
                self.update_camera_settings()
            except Exception as ex:
                logger.error(f"Error returning to preview mode: {ex}")
                
            return False
    
    def start_video(self):
        """Start video recording."""
        if self.recording:
            self.capture_status = "Already recording."
            return False
        
        try:
            self.capture_status = "Starting video..."
            self.camera.stop()
            self.camera.configure(self.video_config)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = os.path.join(self.capture_dir, f"wanda_video_{timestamp}.h264")
            
            self.camera.start_recording(self.encoder, video_filename)
            self.camera.start()
            self.recording = True
            self.capture_status = f"Recording video to {video_filename}"
            
            logger.info(f"Started video recording: {video_filename}")
            return True
            
        except Exception as e:
            self.capture_status = f"Error starting video: {str(e)}"
            logger.error(f"Error starting video: {e}")
            
            # Ensure camera returns to preview mode on error
            try:
                if self.camera.started:
                    self.camera.stop()
                self.camera.configure(self.preview_config)
                self.camera.start()
                self.update_camera_settings()
            except Exception as ex:
                logger.error(f"Error returning to preview mode: {ex}")
                
            return False
    
    def stop_video(self):
        """Stop video recording."""
        if not self.recording:
            self.capture_status = "Not recording."
            return False
        
        try:
            self.capture_status = "Stopping video..."
            self.camera.stop_recording()
            self.camera.stop()
            self.camera.configure(self.preview_config)
            self.camera.start()
            self.recording = False
            self.capture_status = "Video recording stopped."
            
            # Reapply camera settings
            self.update_camera_settings()
            
            logger.info("Stopped video recording")
            return True
            
        except Exception as e:
            self.capture_status = f"Error stopping video: {str(e)}"
            logger.error(f"Error stopping video: {e}")
            return False
            
    def cleanup(self):
        """Clean up resources when shutting down."""
        logger.info("Cleaning up camera resources")
        self.streaming = False
        if self.preview_thread.is_alive():
            self.preview_thread.join(1.0)
        
        if self.camera.started:
            try:
                if self.recording:
                    self.camera.stop_recording()
                self.camera.stop()
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")
    
    # Utility methods
    @staticmethod
    def gain_to_iso(gain):
        """Convert gain value to ISO equivalent."""
        return int(gain * 100)
    
    @staticmethod
    def iso_to_gain(iso):
        """Convert ISO to gain value."""
        return max(1.0, min(iso / 100.0, 16.0))
    
    @staticmethod
    def us_to_shutter_string(us):
        """Convert microseconds to human-readable shutter speed string."""
        seconds = us / 1_000_000
        if seconds < 1:
            fraction = int(1 / seconds)
            return f"1/{fraction}s"
        return f"{int(seconds)}s"
    
    @staticmethod
    def slider_to_us(slider_value):
        """Convert slider value (0-1000) to exposure time in microseconds."""
        min_us = 100
        max_us = 200_000_000
        slider_max = 1000
        slider_value = max(0, min(slider_value, slider_max))
        log_range = math.log(max_us / min_us)
        us = min_us * math.exp(log_range * (slider_value / slider_max))
        return int(max(min_us, min(us, max_us)))
    
    def get_exposure_seconds(self):
        """Get current exposure time in seconds (for UI countdown)."""
        return math.ceil(self.exposure_us / 1_000_000)
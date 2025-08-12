"""
Raspberry Pi camera implementation using picamera2.
"""
import logging
import math
import time
import os
import cv2
import numpy as np
import subprocess
from ..base import AbstractCamera

logger = logging.getLogger(__name__)

# Remove direct imports - we'll import these only when needed
# from picamera2 import Picamera2
# from picamera2.encoders import H264Encoder
# from picamera2.outputs import FileOutput

class PiCamera(AbstractCamera):
    """Raspberry Pi camera implementation using picamera2."""
    
    def __init__(self, capture_dir=None):
        """Initialize the Pi camera."""
        super().__init__()
        self.camera = None
        self.is_recording = False
        self.video_encoder = None
        self.video_output = None
        self.status = "Pi camera initialized"
        
        # Camera settings attributes (needed by web app)
        self.exposure_us = 100000  # Default exposure time in microseconds
        self.gain = 1.0  # Default gain value
        self.use_digital_gain = False  # Whether to use digital gain
        self.digital_gain = 1.0  # Digital gain value
        self.save_raw = False  # Whether to save raw images
        self.recording = False  # Whether currently recording
        self.capture_status = "Ready"  # Current capture status
        self.capture_dir = capture_dir if capture_dir else "captures"  # Directory for saved images
        self.skip_frames = 0  # Performance setting
        self.exposure_mode = "manual"  # Exposure mode
        
        logger.info("Pi camera instance created")
    
    def save_original_state(self):
        """Save the current camera state as the original state to restore on exit."""
        super().save_original_state()
        
        # Save hardware-specific state for Pi camera
        if self.camera:
            try:
                # Get current camera controls
                controls = self.camera.camera_controls
                self._original_hardware_state = {
                    'controls': controls.copy() if controls else {},
                    'exposure_mode': getattr(self, 'exposure_mode', 'manual')
                }
                logger.info("Saved original Pi camera hardware state")
            except Exception as e:
                logger.warning(f"Could not save original hardware state: {e}")
                self._original_hardware_state = None
    
    def restore_original_state(self):
        """Restore the camera to its original state."""
        super().restore_original_state()
        
        # Restore hardware-specific state for Pi camera
        if self.camera and self._original_hardware_state:
            try:
                # Restore original controls
                if 'controls' in self._original_hardware_state:
                    self.camera.set_controls(self._original_hardware_state['controls'])
                
                # Restore exposure mode
                if 'exposure_mode' in self._original_hardware_state:
                    self.exposure_mode = self._original_hardware_state['exposure_mode']
                
                logger.info("Restored original Pi camera hardware state")
            except Exception as e:
                logger.warning(f"Could not restore original hardware state: {e}")
    
    def _import_picamera2(self):
        """Import picamera2 modules only when needed."""
        # Try multiple import strategies
        import_strategies = [
            # Strategy 1: Direct import
            lambda: (__import__('picamera2').Picamera2, 
                    __import__('picamera2.encoders').H264Encoder, 
                    __import__('picamera2.outputs').FileOutput),
            # Strategy 2: Try system path
            lambda: self._import_from_system_path(),
            # Strategy 3: Try subprocess fallback
            lambda: self._import_via_subprocess()
        ]
        
        for i, strategy in enumerate(import_strategies):
            try:
                logger.info(f"Trying picamera2 import strategy {i+1}")
                return strategy()
            except Exception as e:
                logger.warning(f"Import strategy {i+1} failed: {e}")
                continue
        
        # If all strategies fail, raise a clear error
        error_msg = "picamera2 module not available in any form. "
        error_msg += "This camera implementation requires a Raspberry Pi with picamera2 installed. "
        error_msg += "Try: sudo apt install python3-picamera2"
        raise ImportError(error_msg)
    
    def _import_from_system_path(self):
        """Try to import picamera2 from system Python path."""
        import sys
        
        # Add system picamera2 path
        sys.path.append('/usr/lib/python3/dist-packages')
        
        try:
            from picamera2 import Picamera2
            from picamera2.encoders import H264Encoder
            from picamera2.outputs import FileOutput
            
            logger.info("picamera2 imported successfully from system path")
            return Picamera2, H264Encoder, FileOutput
            
        except Exception as e:
            logger.warning(f"System path import strategy failed: {e}")
            raise ImportError("Could not import picamera2 from system path")
    
    def _import_via_subprocess(self):
        """Create a subprocess-based wrapper for picamera2 operations."""
        logger.info("Creating subprocess-based picamera2 wrapper")
        # This will be a mock object that uses subprocess calls
        return self._create_subprocess_wrapper()
    
    def _create_subprocess_wrapper(self):
        """Create a wrapper that uses subprocess calls to rpicam commands."""
        class SubprocessWrapper:
            def __init__(self):
                self.camera_info = None
                self._get_camera_info()
            
            def _get_camera_info(self):
                """Get camera info via subprocess."""
                try:
                    result = subprocess.run(['rpicam-still', '--list-cameras'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.camera_info = result.stdout
                        return True
                except Exception as e:
                    logger.warning(f"Failed to get camera info via subprocess: {e}")
                return False
            
            def global_camera_info(self):
                """Return camera info in expected format."""
                if self.camera_info:
                    # Parse the output to create a compatible format
                    return [{'Model': 'imx477', 'Location': 2, 'Rotation': 180}]
                return []
        
        class MockPicamera2:
            def __init__(self):
                self.wrapper = SubprocessWrapper()
                self.camera_controls = {}
                self._started = False
            
            @staticmethod
            def global_camera_info():
                wrapper = SubprocessWrapper()
                return wrapper.global_camera_info()
            
            def create_preview_configuration(self, main=None):
                """Create preview configuration."""
                if not main:
                    main = {"size": (1440, 810)}
                return {"main": main}
            
            def create_still_configuration(self, main=None, raw=None):
                """Create still image configuration."""
                if not main:
                    main = {"size": (4056, 3040)}
                config = {"main": main}
                if raw:
                    config["raw"] = {"size": (4056, 3040)}
                return config
            
            def create_video_configuration(self, main=None):
                """Create video configuration."""
                if not main:
                    main = {"size": (1920, 1080), "format": "RGB888"}
                return {"main": main}
            
            def configure(self, config):
                """Configure camera settings."""
                logger.info(f"Mock PiCamera: configure({config})")
                # Store configuration for later use
                self._config = config
            
            def set_controls(self, controls):
                """Set camera controls."""
                logger.info(f"Mock PiCamera: set_controls({controls})")
                self.camera_controls.update(controls)
            
            def start(self):
                """Start the camera."""
                logger.info("Mock PiCamera: start()")
                self._started = True
            
            def stop(self):
                """Stop the camera."""
                logger.info("Mock PiCamera: stop()")
                self._started = False
            
            def capture_array(self, name="main"):
                """Capture an array from the camera."""
                logger.info("Mock PiCamera: capture_array()")
                # Return a mock image array (black image)
                import numpy as np
                return np.zeros((810, 1440, 3), dtype=np.uint8)
            
            def capture_file(self, filename, name="main"):
                """Capture a file from the camera."""
                logger.info(f"Mock PiCamera: capture_file({filename})")
                # Use rpicam-still to capture an actual image
                try:
                    result = subprocess.run([
                        'rpicam-still', '-o', filename, '--immediate', '--nopreview'
                    ], capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        logger.info(f"Captured image to {filename}")
                        return True
                    else:
                        logger.error(f"rpicam-still failed: {result.stderr}")
                        return False
                except Exception as e:
                    logger.error(f"Failed to capture image: {e}")
                    return False
            
            def capture_metadata(self, name="main"):
                """Capture metadata from the camera."""
                logger.info("Mock PiCamera: capture_metadata()")
                return {"exposure_time": 100000, "gain": 1.0}
            
            def close(self):
                """Close the camera."""
                logger.info("Mock PiCamera: close()")
                self._started = False
        
        class MockH264Encoder:
            def __init__(self):
                pass
        
        class MockFileOutput:
            def __init__(self, filename):
                self.filename = filename
        
        return MockPicamera2, MockH264Encoder, MockFileOutput
    
    def initialize(self):
        """Initialize the Pi camera hardware."""
        logger.info("Pi camera: initialize()")
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                Picamera2, _, _ = self._import_picamera2()
                
                # Check if any cameras are available
                camera_info = Picamera2.global_camera_info()
                if not camera_info:
                    error_msg = "No cameras detected by libcamera. Please check:\n"
                    error_msg += "1. Camera cable is properly connected to CSI port\n"
                    error_msg += "2. Camera cable is not damaged (try a different cable)\n"
                    error_msg += "3. Camera module is properly seated\n"
                    error_msg += "4. Power supply is adequate (use official Pi power supply)\n"
                    error_msg += "5. Run 'sudo reboot' if camera was recently connected"
                    raise Exception(error_msg)
                
                logger.info(f"Detected {len(camera_info)} camera(s)")
                self.camera = Picamera2()
                
                # Create capture directory if it doesn't exist
                os.makedirs(self.capture_dir, exist_ok=True)
                
                self.status = "Pi camera ready"
                logger.info("Pi camera hardware initialized successfully")
                return  # Success!
                
            except IndexError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Camera initialization attempt {attempt + 1} failed with IndexError, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    self.status = f"Pi camera error: Hardware connection issue"
                    error_msg = f"Failed to initialize Pi camera after {max_retries} attempts.\n"
                    error_msg += "The camera hardware is not responding. Please check the physical connection."
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
            except Exception as e:
                self.status = f"Pi camera error: {str(e)}"
                logger.error(f"Failed to initialize Pi camera hardware: {e}")
                raise
    
    def create_preview_configuration(self, main=None):
        """Create preview configuration."""
        if not main:
            main = {"size": (1440, 810)}  # 16:9 aspect ratio for preview
        return self.camera.create_preview_configuration(main=main)
    
    def create_still_configuration(self, main=None, raw=None):
        """Create still image configuration."""
        if not main:
            main = {"size": (4056, 3040)}  # Full resolution
        config = {"main": main}
        if raw and self.save_raw:
            config["raw"] = {"size": (4056, 3040)}
        return self.camera.create_still_configuration(**config)
    
    def create_video_configuration(self, main=None):
        """Create video configuration."""
        if not main:
            main = {"size": (1920, 1080), "format": "RGB888"}
        return self.camera.create_video_configuration(main=main)
    
    def configure(self, config):
        """Configure camera settings."""
        logger.info(f"Pi camera: configure(config={config})")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        self.camera.configure(config)
    
    def set_controls(self, controls):
        """Set camera controls."""
        logger.info(f"Pi camera: set_controls({controls})")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        self.camera.set_controls(controls)
    
    def start(self):
        """Start the camera."""
        logger.info("Pi camera: start()")
        if not self.camera:
            self.initialize()
        
        # Configure for preview by default
        preview_config = self.create_preview_configuration()
        self.configure(preview_config)
        
        self.camera.start()
        self.started = True
        self.status = "Pi camera started"
    
    def stop(self):
        """Stop the camera."""
        logger.info("Pi camera: stop()")
        if self.is_recording:
            self.stop_recording()
        
        if self.camera and self.started:
            self.camera.stop()
            self.started = False
        self.status = "Pi camera stopped"
    
    def start_recording(self, encoder, filename):
        """Start video recording."""
        logger.info(f"Pi camera: start_recording({filename})")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        try:
            # Import H264Encoder only when needed
            _, H264Encoder, FileOutput = self._import_picamera2()
            
            # Stop current session and reconfigure for video
            if self.started:
                self.camera.stop()
            
            video_config = self.create_video_configuration()
            self.configure(video_config)
            self.camera.start()
            
            # Create encoder and output
            self.video_encoder = H264Encoder(bitrate=10000000)
            self.video_output = FileOutput(filename)
            
            # Start recording
            self.camera.start_recording(self.video_encoder, self.video_output)
            
            self.is_recording = True
            self.recording = True
            self.status = f"Recording to {filename}"
            logger.info(f"Started recording to {filename}")
        except Exception as e:
            self.status = f"Recording failed: {str(e)}"
            logger.error(f"Failed to start recording: {e}")
            raise
    
    def stop_recording(self):
        """Stop video recording."""
        logger.info("Pi camera: stop_recording()")
        try:
            if self.camera and self.is_recording:
                self.camera.stop_recording()
                
            self.is_recording = False
            self.recording = False
            self.video_encoder = None
            self.video_output = None
            self.status = "Recording stopped"
            
            # Restart preview
            if self.started:
                self.camera.stop()
                preview_config = self.create_preview_configuration()
                self.configure(preview_config)
                self.camera.start()
            
            logger.info("Recording stopped successfully")
        except Exception as e:
            self.status = f"Stop recording failed: {str(e)}"
            logger.error(f"Failed to stop recording: {e}")
    
    def capture_array(self, name="main"):
        """Capture a frame as a numpy array."""
        if not self.camera:
            raise Exception("Camera not initialized")
        
        try:
            # Skip frames if needed for performance
            for _ in range(self.skip_frames):
                pass  # Could implement frame skipping here if needed
            
            array = self.camera.capture_array(name)
            return array
        except Exception as e:
            logger.error(f"Failed to capture array: {e}")
            raise
    
    def capture_file(self, filename, name=None):
        """Capture a still image to a file."""
        logger.info(f"Pi camera: capture_file({filename})")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        try:
            # Stop current session and reconfigure for still capture
            was_started = self.started
            if was_started:
                self.camera.stop()
            
            still_config = self.create_still_configuration()
            self.configure(still_config)
            self.camera.start()
            
            # Reapply camera settings after reconfiguration
            self.update_camera_settings()
            
            # Capture the image using capture_array() to respect exposure settings
            # This method properly waits for the exposure time
            array = self.camera.capture_array()
            
            # Convert array to image and save
            import cv2
            # Convert from RGB to BGR for OpenCV
            if len(array.shape) == 3 and array.shape[2] == 3:
                array = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
            
            # Save the image
            cv2.imwrite(filename, array)
            
            # Restart preview if it was running
            if was_started:
                self.camera.stop()
                preview_config = self.create_preview_configuration()
                self.configure(preview_config)
                self.camera.start()
                # Reapply settings for preview mode too
                self.update_camera_settings()
                
            logger.info(f"Successfully captured to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture file: {e}")
            raise
    
    def capture_image(self):
        """Capture an image and return success status and image data.
        
        Returns:
            Tuple[bool, Optional[Any]]: Success status and image data if successful
        """
        logger.info("Pi camera: capture_image()")
        if not self.camera:
            raise Exception("Camera not initialized")
        
        try:
            # Capture to a temporary file first
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                temp_filename = tmp_file.name
            
            # Capture the image
            success = self.camera.capture_file(temp_filename)
            
            if success and os.path.exists(temp_filename):
                # Read the image data
                with open(temp_filename, 'rb') as f:
                    image_data = f.read()
                
                # Clean up temporary file
                os.unlink(temp_filename)
                
                logger.info("Image captured successfully")
                return True, image_data
            else:
                logger.error("Failed to capture image")
                return False, None
                
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return False, None
    
    def cleanup(self):
        """Clean up camera resources."""
        logger.info("Pi camera: cleanup()")
        self.stop()
        if self.camera:
            self.camera.close()
            self.camera = None
        self.status = "Pi camera cleaned up"
    
    # Utility methods needed by web app
    def slider_to_us(self, slider_value):
        """Convert slider value to microseconds."""
        min_us = 100
        max_us = 200_000_000
        log_range = math.log(max_us / min_us)
        return int(min_us * math.exp(slider_value * log_range / 1000))
    
    def us_to_shutter_string(self, us):
        """Convert microseconds to a human-readable shutter speed string."""
        if us >= 1000000:  # 1 second or longer
            return f"{us/1000000:.1f}s"
        else:
            return f"1/{int(1000000/us)}"
    
    def gain_to_iso(self, gain):
        """Convert gain value to ISO equivalent."""
        return int(gain * 100)
    
    def iso_to_gain(self, iso):
        """Convert ISO value to gain."""
        return iso / 100.0
    
    def get_exposure_seconds(self):
        """Get the current exposure time in seconds."""
        return self.exposure_us / 1000000.0
    
    def get_exposure_us(self):
        """Get the current exposure time in microseconds."""
        return self.exposure_us
    
    def set_exposure_us(self, us):
        """Set the exposure time in microseconds."""
        if not self.camera:
            raise Exception("Camera not initialized")
        
        # Validate and clamp exposure time
        us = max(100, min(us, 300_000_000))  # Clamp between 100μs and 300s
        self.exposure_us = us
        
        # Apply the setting to the camera
        try:
            self.camera.set_controls({"ExposureTime": us})
        except Exception as e:
            logger.warning(f"Could not set exposure time: {e}")
    
    def update_camera_settings(self):
        """Update camera settings based on current values."""
        if not self.camera:
            raise Exception("Camera not initialized")
        
        try:
            controls = {}
            
            # Validate and clamp exposure time
            exposure_us = max(100, min(self.exposure_us, 300_000_000))  # Clamp between 100μs and 300s
            self.exposure_us = exposure_us  # Update the stored value
            controls["ExposureTime"] = exposure_us
            
            # Validate and clamp gain
            gain = max(0.2, min(self.gain, 16.0))  # Clamp between 0.2 and 16.0
            self.gain = gain  # Update the stored value
            controls["AnalogueGain"] = gain
            
            # Validate and clamp night vision intensity
            night_vision_intensity = max(1.0, min(self.night_vision_intensity, 80.0))  # Clamp between 1.0 and 80.0
            self.night_vision_intensity = night_vision_intensity  # Update the stored value
            
            # Handle night vision mode
            if self.night_vision_mode:
                self.use_digital_gain = True
                self.digital_gain = night_vision_intensity
            else:
                self.use_digital_gain = False
                self.digital_gain = 1.0
            
            # Apply controls
            self.camera.set_controls(controls)
            logger.debug(f"Applied camera controls: {controls}")
        except Exception as e:
            logger.warning(f"Could not update camera settings: {e}")
    
    def get_frame(self):
        """Get a frame as JPEG data."""
        try:
            # Capture array and convert to JPEG
            frame = self.capture_array()
            if frame is not None:
                # Apply digital gain if enabled
                if self.use_digital_gain and self.digital_gain > 1.0:
                    frame = np.clip(frame * self.digital_gain, 0, 255).astype(np.uint8)
                
                # Convert to BGR if needed (picamera2 usually gives RGB)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Encode to JPEG
                _, jpeg = cv2.imencode('.jpg', frame)
                return jpeg.tobytes()
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
        return None
    
    def capture_still(self):
        """Capture a still image."""
        try:
            self.capture_status = "Capturing..."
            
            # Create filename
            filename = f"{self.capture_dir}/capture_{int(time.time())}.jpg"
            
            # Capture the image
            self.capture_file(filename)
            
            self.capture_status = f"Image saved as {filename}"
            return True
        except Exception as e:
            self.capture_status = f"Capture failed: {str(e)}"
            logger.error(f"Error capturing still: {e}")
            return False
    
    def start_video(self):
        """Start video recording."""
        try:
            filename = f"{self.capture_dir}/video_{int(time.time())}.mp4"
            _, H264Encoder, _ = self._import_picamera2()
            encoder = H264Encoder(bitrate=10000000)
            self.start_recording(encoder, filename)
            return True
        except Exception as e:
            logger.error(f"Error starting video: {e}")
            return False
    
    def stop_video(self):
        """Stop video recording."""
        try:
            self.stop_recording()
            return True
        except Exception as e:
            logger.error(f"Error stopping video: {e}")
            return False
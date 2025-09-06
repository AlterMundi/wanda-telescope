"""
Raspberry Pi camera implementation using picamera2.
"""
import logging
import math
import time
import os
import cv2
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from ..base import AbstractCamera

logger = logging.getLogger(__name__)

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

                logger.info("Restored original Pi camera hardware state")
            except Exception as e:
                logger.warning(f"Could not restore original hardware state: {e}")
            finally:
                # Always try to restore exposure mode, even if controls failed
                if 'exposure_mode' in self._original_hardware_state:
                    self.exposure_mode = self._original_hardware_state['exposure_mode']
    
    def initialize(self):
        """Initialize the Pi camera hardware with optimized configuration."""
        logger.info("Pi camera: initialize()")
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
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

                # Create still config with buffers for efficiency
                config = self.camera.create_still_configuration(buffer_count=2)
                self.camera.configure(config)

                # Disable auto modes and set frame limits initially
                self.camera.set_controls({
                    "AeEnable": False,
                    "FrameDurationLimits": (100, 230_000_000)  # Up to 230s for IMX477
                })

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
            main = {"size": (1440, 1080)}  # 4:3 aspect ratio for preview
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
    
    def _validate_and_clamp_gain(self, gain):
        """Validate and clamp gain value against sensor limits.
        
        Args:
            gain: The gain value to validate
            
        Returns:
            float: The clamped gain value within sensor limits
        """
        try:
            gain_limits = self.camera.camera_controls['AnalogueGain']
            if isinstance(gain_limits, tuple) and len(gain_limits) >= 2:
                gain_min, gain_max = gain_limits[0], gain_limits[1]
            elif hasattr(gain_limits, 'min') and hasattr(gain_limits, 'max'):
                gain_min, gain_max = gain_limits.min, gain_limits.max
            else:
                # Fallback to reasonable defaults
                gain_min, gain_max = 1.0, 16.0
            
            return max(gain_min, min(gain, gain_max))
        except (KeyError, AttributeError):
            # If we can't get gain limits, return the provided gain
            return gain
    
    def get_exposure_seconds(self):
        """Get the current exposure time in seconds."""
        return self.exposure_us / 1000000.0
    
    def get_exposure_us(self):
        """Get the current exposure time in microseconds."""
        return self.exposure_us
    
    def set_exposure_us(self, us, gain=None):
        """Set exposure time in µs and analogue gain for low-light."""
        if not self.camera:
            raise Exception("Camera not initialized")

        # Query sensor limits - handle both tuple and object formats
        exp_limits = self.camera.camera_controls['ExposureTime']
        if isinstance(exp_limits, tuple) and len(exp_limits) == 2:
            exp_min, exp_max = exp_limits
        elif hasattr(exp_limits, 'min') and hasattr(exp_limits, 'max'):
            exp_min, exp_max = exp_limits.min, exp_limits.max
        else:
            # Fallback to reasonable defaults
            exp_min, exp_max = 31, 230_000_000

        us = max(exp_min, min(us, exp_max))

        self.exposure_us = us

        # Use provided gain or current gain
        if gain is None:
            gain = self.gain
        else:
            self.gain = gain

        # Validate and clamp gain against sensor limits
        gain = self._validate_and_clamp_gain(gain)
        self.gain = gain  # Update stored value

        try:
            self.camera.set_controls({
                "ExposureTime": us,
                "AnalogueGain": gain
            })
            logger.info(f"Set exposure to {us/1e6:.1f}s and gain to {gain}")
        except Exception as e:
            logger.warning(f"Could not set exposure/gain: {e}")
    
    def update_camera_settings(self):
        """Update camera settings based on current values with sensor limits."""
        if not self.camera:
            raise Exception("Camera not initialized")

        try:
            controls = {}

            # Validate and clamp exposure time using sensor limits
            try:
                exp_limits = self.camera.camera_controls['ExposureTime']
                if isinstance(exp_limits, tuple) and len(exp_limits) == 2:
                    exp_min, exp_max = exp_limits
                elif hasattr(exp_limits, 'min') and hasattr(exp_limits, 'max'):
                    exp_min, exp_max = exp_limits.min, exp_limits.max
                else:
                    exp_min, exp_max = 31, 230_000_000

                exposure_us = max(exp_min, min(self.exposure_us, exp_max))
                self.exposure_us = exposure_us  # Update the stored value
                controls["ExposureTime"] = exposure_us
            except (KeyError, AttributeError):
                # Fallback to basic exposure setting
                controls["ExposureTime"] = self.exposure_us

            # Validate and clamp gain using sensor limits
            gain = self._validate_and_clamp_gain(self.gain)
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

    def capture_with_verification(self, filename):
        """Capture and verify exposure settings are applied correctly."""
        try:
            # Capture with flush to ensure fresh data
            request = self.camera.capture_request(flush=True)
            image = request.make_array("main")
            metadata = request.get_metadata()

            # Verify exposure settings
            actual_us = metadata['ExposureTime']
            if abs(actual_us - self.exposure_us) > 1000:  # 1ms tolerance
                logger.warning(f"Exposure mismatch: requested {self.exposure_us}µs, actual {actual_us}µs")

            # Convert array to image and save
            # Convert from RGB to BGR for OpenCV
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Save the image
            cv2.imwrite(filename, image)

            # Clean up
            request.release()

            logger.info(f"Successfully captured with verification to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to capture with verification: {e}")
            raise
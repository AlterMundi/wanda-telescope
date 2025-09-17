"""
Abstract base class defining the camera interface.
"""
from abc import ABC, abstractmethod
import config

class AbstractCamera(ABC):
    """Abstract camera interface that all implementations must follow."""
    
    def __init__(self):
        self.started = False
        self.options = {}
        # Common attributes that app.py expects - use centralized config values
        self.exposure_us = config.DEFAULT_EXPOSURE_US  # Default exposure time in microseconds
        self.gain = config.DEFAULT_GAIN  # Default gain value
        self.use_digital_gain = config.USE_DIGITAL_GAIN  # Whether to use digital gain (legacy)
        self.digital_gain = config.DEFAULT_DIGITAL_GAIN  # Digital gain value (legacy)
        self.night_vision_mode = False  # Whether to use night vision mode
        self.night_vision_intensity = 1.0  # Night vision intensity value
        self.save_raw = config.SAVE_RAW  # Whether to save raw images
        self.recording = False  # Whether currently recording
        self.capture_status = "Ready"  # Current capture status
        self.capture_dir = "captures"  # Directory for saved images
        self.skip_frames = 0  # Performance setting
        
        # Original state tracking for restoration
        self._original_state = None
    
    @abstractmethod
    def initialize(self):
        pass
    
    @abstractmethod
    def create_preview_configuration(self, main=None):
        pass
    
    @abstractmethod
    def create_still_configuration(self, main=None, raw=None):
        pass
    
    @abstractmethod
    def create_video_configuration(self, main=None):
        pass
    
    @abstractmethod
    def configure(self, config):
        pass
    
    @abstractmethod
    def start(self):
        pass
    
    @abstractmethod
    def stop(self):
        pass
    
    @abstractmethod
    def capture_array(self, name="main"):
        pass
    
    @abstractmethod
    def capture_file(self, filename, name=None):
        pass
    
    @abstractmethod
    def set_controls(self, controls):
        pass
    
    @abstractmethod
    def start_recording(self, encoder, filename):
        pass
    
    @abstractmethod
    def stop_recording(self):
        pass
    
    @abstractmethod
    def cleanup(self):
        pass
    
    # Additional methods that app.py expects
    def update_camera_settings(self):
        """Update camera settings based on current attributes."""
        pass
    
    def start_video(self):
        """Start video recording."""
        return self.start_recording(None, None)
    
    def stop_video(self):
        """Stop video recording."""
        return self.stop_recording()
    
    def get_frame(self):
        """Get a frame as JPEG data."""
        pass
    
    def capture_still(self):
        """Capture a still image."""
        pass
    
    def save_original_state(self):
        """Save the current camera state as the original state to restore on exit."""
        self._original_state = {
            'exposure_us': self.exposure_us,
            'gain': self.gain,
            'use_digital_gain': self.use_digital_gain,
            'digital_gain': self.digital_gain,
            'night_vision_mode': self.night_vision_mode,
            'night_vision_intensity': self.night_vision_intensity,
            'save_raw': self.save_raw,
            'skip_frames': self.skip_frames
        }
    
    def restore_original_state(self):
        """Restore the camera to its original state."""
        if self._original_state is not None:
            self.exposure_us = self._original_state['exposure_us']
            self.gain = self._original_state['gain']
            self.use_digital_gain = self._original_state['use_digital_gain']
            self.digital_gain = self._original_state['digital_gain']
            self.night_vision_mode = self._original_state['night_vision_mode']
            self.night_vision_intensity = self._original_state['night_vision_intensity']
            self.save_raw = self._original_state['save_raw']
            self.skip_frames = self._original_state['skip_frames']
            
            # Apply the restored settings to the camera hardware
            self.update_camera_settings()
    
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
    
    def slider_to_us(self, slider_value):
        """Convert slider value to microseconds."""
        import math
        min_us = 100
        max_us = 200_000_000
        log_range = math.log(max_us / min_us)
        return int(min_us * math.exp(slider_value * log_range / 1000))
    
    def get_exposure_seconds(self):
        """Get the current exposure time in seconds."""
        return self.exposure_us / 1000000.0
    
    def get_exposure_us(self):
        """Get the current exposure time in microseconds."""
        return self.exposure_us
    
    def set_exposure_us(self, us):
        """Set the exposure time in microseconds."""
        self.exposure_us = us
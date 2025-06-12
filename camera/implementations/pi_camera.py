"""
Raspberry Pi camera implementation using picamera2.
"""
import logging
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from ..base import AbstractCamera

logger = logging.getLogger(__name__)

class PiCamera(AbstractCamera):
    """Raspberry Pi camera implementation."""
    
    def __init__(self):
        super().__init__()
        self._picamera2 = Picamera2()
        logger.info("Raspberry Pi camera initialized")
    
    def create_preview_configuration(self, main=None):
        return self._picamera2.create_preview_configuration(main=main)
    
    def create_still_configuration(self, main=None, raw=None):
        return self._picamera2.create_still_configuration(main=main, raw=raw)
    
    def create_video_configuration(self, main=None):
        return self._picamera2.create_video_configuration(main=main)
    
    def configure(self, config):
        self._picamera2.configure(config)
    
    def start(self):
        self._picamera2.start()
        self.started = True
    
    def stop(self):
        self._picamera2.stop()
        self.started = False
    
    def capture_array(self, name="main"):
        return self._picamera2.capture_array(name)
    
    def capture_file(self, filename, name=None):
        self._picamera2.capture_file(filename, name=name)
    
    def set_controls(self, controls):
        self._picamera2.set_controls(controls)
    
    def start_recording(self, encoder, filename):
        self._picamera2.start_recording(encoder, filename)
    
    def stop_recording(self):
        self._picamera2.stop_recording()
    
    def cleanup(self):
        if self.started:
            try:
                self.stop()
            except Exception as e:
                logger.error(f"Error stopping Pi camera: {e}")
    
    @property
    def options(self):
        return self._picamera2.options
    
    @options.setter
    def options(self, value):
        self._picamera2.options = value
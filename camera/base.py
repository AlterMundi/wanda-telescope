"""
Abstract base class defining the camera interface.
"""
from abc import ABC, abstractmethod

class AbstractCamera(ABC):
    """Abstract camera interface that all implementations must follow."""
    
    def __init__(self):
        self.started = False
        self.options = {}
    
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
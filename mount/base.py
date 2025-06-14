"""
Abstract base class for mount implementations.
"""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class AbstractMount(ABC):
    """Abstract base class for mount implementations."""
    
    def __init__(self):
        """Initialize the mount."""
        self.tracking = False
        self.direction = "NONE"
        self.speed = 0
        self.status = "Initialized"  # Add status attribute
        self.motor_pins = {
            'ra': {'step': 17, 'dir': 18},
            'dec': {'step': 22, 'dir': 23}
        }
        logger.info("Mount initialized")
    
    @abstractmethod
    def initialize(self):
        """Initialize the mount hardware."""
        pass
    
    @abstractmethod
    def start_tracking(self):
        """Start tracking."""
        pass
    
    @abstractmethod
    def stop_tracking(self):
        """Stop tracking."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up mount resources."""
        pass 
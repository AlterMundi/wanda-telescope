"""
Mock mount implementation for development and testing.
"""
import logging
from ..base import AbstractMount

logger = logging.getLogger(__name__)

class MockMount(AbstractMount):
    """Mock mount implementation for development and testing."""
    
    def __init__(self):
        """Initialize the mock mount."""
        super().__init__()
        self.tracking = False
        self.direction = True  # True for clockwise
        self.speed = 1.0  # Default speed in seconds
        self.status = "Mock mount initialized"
        self.motor_pins = [17, 18, 27, 22]  # Mock GPIO pins
        self.step_sequence = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        self.current_step = 0
        logger.info("Mock mount initialized")
    
    def initialize(self):
        """Initialize the mock mount hardware."""
        logger.info("Mock mount: initialize()")
        self.status = "Mock mount ready"
    
    def start_tracking(self):
        """Start tracking with the mock mount."""
        logger.info("Mock mount: start_tracking()")
        self.tracking = True
        self.status = "Mock mount tracking"
    
    def stop_tracking(self):
        """Stop tracking with the mock mount."""
        logger.info("Mock mount: stop_tracking()")
        self.tracking = False
        self.status = "Mock mount stopped"
    
    def cleanup(self):
        """Clean up mock mount resources."""
        logger.info("Mock mount: cleanup()")
        self.tracking = False
        self.status = "Mock mount cleaned up" 
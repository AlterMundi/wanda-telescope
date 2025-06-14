"""
Mount controller module for managing telescope mount operations.
"""
import logging
import time
from .factory import MountFactory

logger = logging.getLogger(__name__)

class MountController:
    """Controller class for managing telescope mount operations."""
    
    def __init__(self):
        """Initialize the mount controller."""
        self.mount = MountFactory.create_mount()
        self.mount.initialize()
        self.status = self.mount.status  # Initialize status from mount
        self.tracking = self.mount.tracking  # Initialize tracking state from mount
        self.direction = self.mount.direction  # Initialize direction from mount
        self.speed = self.mount.speed  # Initialize speed from mount
        logger.info("Mount controller initialized")
    
    def start_tracking(self):
        """Start mount tracking."""
        logger.info("Mount controller: start_tracking()")
        self.mount.start_tracking()
        self.status = self.mount.status
        self.tracking = self.mount.tracking
        return True
    
    def stop_tracking(self):
        """Stop mount tracking."""
        logger.info("Mount controller: stop_tracking()")
        self.mount.stop_tracking()
        self.status = self.mount.status
        self.tracking = self.mount.tracking
        return True
    
    def cleanup(self):
        """Clean up mount resources."""
        logger.info("Mount controller: cleanup()")
        self.mount.cleanup()
        self.status = self.mount.status
        self.tracking = self.mount.tracking

    def setup_gpio(self):
        """Configure GPIO pins for the stepper motor."""
        logger.info(f"Setting up mount GPIO pins: {self.mount.motor_pins}")
        GPIO.setmode(GPIO.BCM)
        for pin in self.mount.motor_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)  # Initialize all pins to LOW
        logger.info("Mount GPIO setup complete")
    
    def step_motor(self, clockwise=True):
        """Move the stepper motor one step in the specified direction."""
        # Apply the current sequence to the motor
        logger.debug(f"Step {self.mount.current_step}: Applying sequence {self.mount.step_sequence[self.mount.current_step]}")
        for i in range(len(self.mount.motor_pins)):
            GPIO.output(self.mount.motor_pins[i], self.mount.step_sequence[self.mount.current_step][i])
        
        # Update to the next step based on direction
        if clockwise:
            self.mount.current_step = (self.mount.current_step + 1) % len(self.mount.step_sequence)
        else:
            self.mount.current_step = (self.mount.current_step - 1) % len(self.mount.step_sequence)
    
    def tracking_thread_func(self):
        """Thread function for continuous mount tracking."""
        logger.info(f"Mount tracking thread started: direction={self.mount.direction}, speed={self.mount.speed}s")
        steps_completed = 0
        
        while self.mount.tracking:
            logger.debug(f"Taking step {steps_completed+1}, direction={'clockwise' if self.mount.direction else 'counterclockwise'}")
            # Take one step in the specified direction
            self.step_motor(self.mount.direction)
            steps_completed += 1
            
            # Optional status update (every 10 steps)
            if steps_completed % 10 == 0:
                logger.info(f"Completed {steps_completed} steps")
                self.mount.status = f"Tracking: {steps_completed} steps completed"
            
            # Wait before the next step
            time.sleep(self.mount.speed)
        
        logger.info("Mount tracking thread terminated")
    
    def update_settings(self, speed=None, direction=None):
        """Update the mount settings."""
        if speed is not None:
            self.mount.speed = max(0.1, min(speed, 10.0))
            
        if direction is not None:
            self.mount.direction = direction
            
        logger.info(f"Updated mount settings: speed={self.mount.speed}s, direction={'clockwise' if self.mount.direction else 'counterclockwise'}")
        
        # Update status message if tracking
        if self.mount.tracking:
            self.mount.status = f"Mount tracking at {self.mount.speed}s per step, direction: {'clockwise' if self.mount.direction else 'counterclockwise'}"
    
    def turn_off_pins(self):
        """Turn off all motor pins."""
        logger.info("Turning off all motor pins")
        for pin in self.mount.motor_pins:
            GPIO.output(pin, 0)
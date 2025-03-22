"""
Mount controller for Wanda astrophotography system.
Handles equatorial mount initialization and movement control.
"""
import time
import threading
import logging
import RPi.GPIO as GPIO
import config

logger = logging.getLogger(__name__)

class MountController:
    """Controller for the equatorial mount tracking operations."""
    
    def __init__(self):
        """Initialize the mount with default settings."""
        self.motor_pins = config.MOTOR_PINS
        self.step_sequence = config.STEP_SEQUENCE
        self.current_step = 0
        self.tracking = False
        self.direction = True  # True for clockwise, False for counterclockwise
        self.speed = config.DEFAULT_SIDEREAL_DELAY
        self.status = "Mount not tracking"
        self.tracking_thread = None
        
        # Set up GPIO
        self.setup_gpio()
        logger.info("Mount controller initialized")
        
    def setup_gpio(self):
        """Configure GPIO pins for the stepper motor."""
        logger.info(f"Setting up mount GPIO pins: {self.motor_pins}")
        GPIO.setmode(GPIO.BCM)
        for pin in self.motor_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)  # Initialize all pins to LOW
        logger.info("Mount GPIO setup complete")
    
    def step_motor(self, clockwise=True):
        """Move the stepper motor one step in the specified direction."""
        # Apply the current sequence to the motor
        logger.debug(f"Step {self.current_step}: Applying sequence {self.step_sequence[self.current_step]}")
        for i in range(len(self.motor_pins)):
            GPIO.output(self.motor_pins[i], self.step_sequence[self.current_step][i])
        
        # Update to the next step based on direction
        if clockwise:
            self.current_step = (self.current_step + 1) % len(self.step_sequence)
        else:
            self.current_step = (self.current_step - 1) % len(self.step_sequence)
    
    def tracking_thread_func(self):
        """Thread function for continuous mount tracking."""
        logger.info(f"Mount tracking thread started: direction={self.direction}, speed={self.speed}s")
        steps_completed = 0
        
        while self.tracking:
            logger.debug(f"Taking step {steps_completed+1}, direction={'clockwise' if self.direction else 'counterclockwise'}")
            # Take one step in the specified direction
            self.step_motor(self.direction)
            steps_completed += 1
            
            # Optional status update (every 10 steps)
            if steps_completed % 10 == 0:
                logger.info(f"Completed {steps_completed} steps")
                self.status = f"Tracking: {steps_completed} steps completed"
            
            # Wait before the next step
            time.sleep(self.speed)
        
        logger.info("Mount tracking thread terminated")
    
    def start_tracking(self):
        """Start the mount tracking at the configured speed and direction."""
        if self.tracking:
            logger.info("Mount already tracking - ignoring request")
            self.status = "Mount already tracking."
            return False
        
        logger.info(f"Starting tracking with settings: speed={self.speed}s, direction={'clockwise' if self.direction else 'counterclockwise'}")
        self.status = "Starting tracking..."
        self.tracking = True
        
        # Start the tracking thread
        self.tracking_thread = threading.Thread(target=self.tracking_thread_func, daemon=True)
        self.tracking_thread.start()
        logger.info(f"Mount tracking thread started: {self.tracking_thread.name}")
        
        self.status = f"Mount tracking at {self.speed}s per step, direction: {'clockwise' if self.direction else 'counterclockwise'}"
        return True
    
    def stop_tracking(self):
        """Stop the mount tracking."""
        if not self.tracking:
            logger.info("Mount was not tracking - ignoring request")
            self.status = "Mount not tracking."
            return False
        
        logger.info("Stopping mount tracking")
        self.status = "Stopping tracking..."
        self.tracking = False
        
        # Wait for the thread to finish
        if self.tracking_thread and self.tracking_thread.is_alive():
            logger.info(f"Waiting for tracking thread {self.tracking_thread.name} to finish")
            self.tracking_thread.join(2.0)  # Wait up to 2 seconds
        
        # Turn off all motor pins
        self.turn_off_pins()
        
        self.status = "Mount tracking stopped."
        logger.info("Mount tracking has been stopped")
        return True
    
    def update_settings(self, speed=None, direction=None):
        """Update the mount settings."""
        if speed is not None:
            self.speed = max(0.1, min(speed, 10.0))
            
        if direction is not None:
            self.direction = direction
            
        logger.info(f"Updated mount settings: speed={self.speed}s, direction={'clockwise' if self.direction else 'counterclockwise'}")
        
        # Update status message if tracking
        if self.tracking:
            self.status = f"Mount tracking at {self.speed}s per step, direction: {'clockwise' if self.direction else 'counterclockwise'}"
    
    def turn_off_pins(self):
        """Turn off all motor pins."""
        logger.info("Turning off all motor pins")
        for pin in self.motor_pins:
            GPIO.output(pin, 0)
    
    def cleanup(self):
        """Clean up GPIO resources when shutting down."""
        logger.info("Cleaning up mount resources")
        
        # Stop tracking if active
        if self.tracking:
            logger.info("Stopping active mount tracking...")
            self.tracking = False
            if self.tracking_thread and self.tracking_thread.is_alive():
                self.tracking_thread.join(2.0)
        
        # Turn off all motor pins
        self.turn_off_pins()
        
        # Clean up GPIO
        logger.info("Cleaning up GPIO...")
        GPIO.cleanup()
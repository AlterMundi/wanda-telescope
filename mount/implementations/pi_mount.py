"""
Raspberry Pi mount implementation using RPi.GPIO.
"""
import logging
import time
import threading
import RPi.GPIO as GPIO
from ..base import AbstractMount

logger = logging.getLogger(__name__)

class PiMount(AbstractMount):
    """Raspberry Pi mount implementation using GPIO."""
    
    def __init__(self):
        """Initialize the Pi mount."""
        self.tracking = False
        self.direction = True  # True for clockwise
        self.speed = 1.0  # Default speed in seconds
        self.status = "Pi mount initialized"
        self.motor_pins = [17, 18, 27, 22]  # GPIO pins for stepper motor
        self.step_sequence = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        self.current_step = 0
        self.tracking_thread = None
        logger.info("Pi mount initialized")
    
    def initialize(self):
        """Initialize the Pi mount hardware."""
        logger.info("Pi mount: initialize()")
        GPIO.setmode(GPIO.BCM)
        for pin in self.motor_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)
        self.status = "Pi mount ready"
    
    def start_tracking(self):
        """Start tracking with the Pi mount."""
        if self.tracking:
            logger.info("Pi mount already tracking")
            return False
            
        logger.info("Pi mount: start_tracking()")
        self.tracking = True
        self.tracking_thread = threading.Thread(target=self._tracking_thread, daemon=True)
        self.tracking_thread.start()
        self.status = f"Pi mount tracking at {self.speed}s per step"
        return True
    
    def stop_tracking(self):
        """Stop tracking with the Pi mount."""
        if not self.tracking:
            logger.info("Pi mount not tracking")
            return False
            
        logger.info("Pi mount: stop_tracking()")
        self.tracking = False
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.tracking_thread.join(2.0)
        self._turn_off_pins()
        self.status = "Pi mount stopped"
        return True
    
    def cleanup(self):
        """Clean up Pi mount resources."""
        logger.info("Pi mount: cleanup()")
        self.stop_tracking()
        GPIO.cleanup()
        self.status = "Pi mount cleaned up"
    
    def _tracking_thread(self):
        """Thread function for continuous mount tracking."""
        logger.info(f"Pi mount tracking thread started: direction={self.direction}, speed={self.speed}s")
        steps_completed = 0
        
        while self.tracking:
            self._step_motor(self.direction)
            steps_completed += 1
            if steps_completed % 10 == 0:
                logger.info(f"Completed {steps_completed} steps")
            time.sleep(self.speed)
        
        logger.info("Pi mount tracking thread terminated")
    
    def _step_motor(self, clockwise):
        """Move the stepper motor one step."""
        for i in range(len(self.motor_pins)):
            GPIO.output(self.motor_pins[i], self.step_sequence[self.current_step][i])
        
        if clockwise:
            self.current_step = (self.current_step + 1) % len(self.step_sequence)
        else:
            self.current_step = (self.current_step - 1) % len(self.step_sequence)
    
    def _turn_off_pins(self):
        """Turn off all motor pins."""
        for pin in self.motor_pins:
            GPIO.output(pin, 0) 
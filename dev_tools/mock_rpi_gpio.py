"""
Mock implementation of RPi.GPIO library for development environment.
This allows development on systems without Raspberry Pi GPIO hardware.
"""
import logging

logger = logging.getLogger(__name__)

# GPIO constants
BCM = "BCM"
OUT = "OUT"
HIGH = 1
LOW = 0

def setmode(mode):
    """Mock GPIO.setmode()"""
    logger.debug(f"Mock GPIO: setmode({mode})")

def setup(pin, mode):
    """Mock GPIO.setup()"""
    logger.debug(f"Mock GPIO: setup(pin={pin}, mode={mode})")

def output(pin, value):
    """Mock GPIO.output()"""
    logger.debug(f"Mock GPIO: output(pin={pin}, value={value})")

def cleanup(pins=None):
    """Mock GPIO.cleanup()"""
    if pins:
        logger.debug(f"Mock GPIO: cleanup(pins={pins})")
    else:
        logger.debug("Mock GPIO: cleanup(all)")

# For compatibility with "import RPi.GPIO as GPIO"
class MockGPIO:
    BCM = BCM
    OUT = OUT
    HIGH = HIGH  
    LOW = LOW
    
    setmode = staticmethod(setmode)
    setup = staticmethod(setup)
    output = staticmethod(output)
    cleanup = staticmethod(cleanup)
"""
Configuration settings for Wanda astrophotography system.
"""
import os
import json

# Camera settings
CAMERA_TUNING_FILE = "/usr/share/libcamera/ipa/raspberrypi/imx477.json"
DEFAULT_EXPOSURE_US = 10000
DEFAULT_GAIN = 1.0
DEFAULT_DIGITAL_GAIN = 1.0
USE_DIGITAL_GAIN = False
SAVE_RAW = False

# Image/Video configurations
PREVIEW_SIZE = (1440, 1080)  # 4:3 aspect ratio for preview
STILL_SIZE = (4056, 2282)   # 16:9 aspect ratio for stills (closest to max resolution)
VIDEO_SIZE = (1920, 1080)   # Full HD 16:9 for video
VIDEO_BITRATE = 10000000    # 10 Mbps video bitrate

# Mount configuration
MOTOR_PINS = [23, 24, 25, 8]  # GPIO pins for stepper motor control
STEP_SEQUENCE = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]
DEFAULT_SIDEREAL_DELAY = 3.523  # Default tracking speed (sidereal rate)

# Storage settings
USB_BASE = "/media/astro1"
HOME_BASE = "/home/astro1/wanda_captures"
CAPTURE_SUBDIR = "wanda_captures"

# Web server settings
HOST = '0.0.0.0'
PORT = 5000

def load_camera_tuning():
    """Load camera tuning file if available."""
    if os.path.exists(CAMERA_TUNING_FILE):
        try:
            with open(CAMERA_TUNING_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading tuning file: {e}")
    return None
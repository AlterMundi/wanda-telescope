"""
Camera factory module for creating camera instances.
"""
import logging
import subprocess
import os
from typing import Optional, Type

try:
    import cv2
except ImportError:
    cv2 = None

from .base import AbstractCamera
from .implementations.mock_camera import MockCamera
from .implementations.usb_camera import USBCamera
from .implementations.pi_camera import PiCamera

logger = logging.getLogger(__name__)

class CameraFactory:
    """Factory class for creating camera instances."""
    
    @staticmethod
    def _check_rpicam_camera():
        """Check for Raspberry Pi camera using rpicam-still command."""
        try:
            result = subprocess.run(['rpicam-still', '--list-cameras'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'imx477' in result.stdout.lower():
                logger.info("Raspberry Pi camera detected via rpicam-still")
                return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
        return False
    
    @staticmethod
    def create_camera() -> AbstractCamera:
        """Create a camera instance based on available hardware.
        
        Returns:
            AbstractCamera: A camera instance
            
        Raises:
            Exception: If camera initialization fails
        """
        try:
            # First try to detect Raspberry Pi camera
            try:
                import picamera2
                logger.info("Raspberry Pi camera detected")
                return PiCamera()
            except (ImportError, ModuleNotFoundError):
                logger.info("Raspberry Pi camera not available via picamera2")
                
                # Fallback: try using rpicam-still command
                if CameraFactory._check_rpicam_camera():
                    try:
                        logger.info("Raspberry Pi camera detected via rpicam-still, attempting PiCamera initialization")
                        return PiCamera()
                    except Exception as e:
                        logger.warning(f"PiCamera initialization failed despite camera detection: {e}")
            
            # Then try to detect USB camera
            try:
                if cv2 is None:
                    raise ImportError("cv2 not available")
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, _ = cap.read()
                    cap.release()
                    if ret:
                        logger.info("USB camera detected")
                        return USBCamera()
            except Exception as e:
                logger.warning(f"USB camera detection failed: {str(e)}")
            
            # If no real camera is available, use mock camera
            logger.info("No real camera detected, using mock camera")
            return MockCamera()
            
        except Exception as e:
            raise Exception(f"Failed to initialize camera: {str(e)}")
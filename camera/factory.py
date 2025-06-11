from typing import Optional, Type

from .base import AbstractCamera
from .detection import get_preferred_camera
from .exceptions import CameraNotFoundError, CameraInitializationError

class CameraFactory:
    """Factory class for creating camera instances."""
    
    @staticmethod
    def create_camera(camera_type: Optional[str] = None) -> AbstractCamera:
        """Create and return a camera instance based on type or auto-detection.
        
        Args:
            camera_type: Optional type of camera to create. If None, auto-detect.
            
        Returns:
            AbstractCamera: An instance of the appropriate camera implementation
            
        Raises:
            CameraNotFoundError: If no suitable camera is found
            CameraInitializationError: If camera initialization fails
        """
        # If no specific type requested, auto-detect
        if camera_type is None:
            detected = get_preferred_camera()
            camera_type = detected['type']
        
        # Import the appropriate implementation
        try:
            if camera_type == 'pi_camera':
                from .implementations.pi_camera import PiCamera
                return PiCamera()
            elif camera_type == 'usb_camera':
                from .implementations.usb_camera import USBCamera
                return USBCamera()
            else:
                # Fall back to mock camera for development/testing
                from .implementations.mock_camera import MockCamera
                return MockCamera()
        except ImportError as e:
            raise CameraInitializationError(f"Failed to import camera module: {str(e)}")
        except Exception as e:
            raise CameraInitializationError(f"Failed to initialize camera: {str(e)}")
            
    @staticmethod
    def list_available_cameras():
        """List all available cameras in the system."""
        from .detection import get_available_cameras
        return get_available_cameras() 
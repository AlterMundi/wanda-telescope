import pytest
from unittest.mock import Mock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from camera.implementations.usb_camera import USBCamera

class TestUSBCamera:
    def test_usb_camera_initialization(self):
        """Test USB camera initializes correctly."""
        camera = USBCamera()
        assert hasattr(camera, "camera")
        assert hasattr(camera, "exposure_us")

    def test_configure(self):
        """Test configuring the camera."""
        with patch('camera.implementations.usb_camera.cv2') as mock_cv2:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cv2.VideoCapture.return_value = mock_cap
            
            camera = USBCamera()
            camera.initialize()  # Initialize first
            camera.configure({"test": "value"})  # Should not raise exception
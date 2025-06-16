import pytest
from unittest.mock import Mock, patch, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

class TestPiCamera:
    def test_pi_camera_with_mocked_hardware(self, mock_picamera2):
        """Test Pi camera with mocked picamera2."""
        from camera.implementations.pi_camera import PiCamera
        camera = PiCamera()
        assert hasattr(camera, "camera")
        assert hasattr(camera, "exposure_us")

    def test_create_configurations(self, mock_picamera2):
        """Test creating camera configurations."""
        from camera.implementations.pi_camera import PiCamera
        
        # Mock the Picamera2 instance
        mock_cam_instance = Mock()
        mock_picamera2.Picamera2.return_value = mock_cam_instance
        
        camera = PiCamera()
        camera.camera = mock_cam_instance  # Set the camera instance
        
        # Mock the configuration methods
        mock_cam_instance.create_preview_configuration.return_value = {"type": "preview"}
        mock_cam_instance.create_still_configuration.return_value = {"type": "still"}
        
        preview_config = camera.create_preview_configuration()
        assert isinstance(preview_config, dict)
        
        still_config = camera.create_still_configuration()
        assert isinstance(still_config, dict)
"""Unit tests for camera factory functionality."""
import pytest
from unittest.mock import patch, Mock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from camera.factory import CameraFactory
from camera.implementations.mock_camera import MockCamera

class TestCameraFactory:
    def test_create_camera_returns_mock_when_no_hardware(self):
        """Test that factory returns mock camera when no hardware is available."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = False
            with patch.dict("sys.modules", {"picamera2": None}):
                camera = CameraFactory.create_camera()
                assert isinstance(camera, MockCamera)

    def test_list_available_cameras(self):
        """Test listing available cameras."""
        cameras = CameraFactory.list_available_cameras()
        assert isinstance(cameras, list)

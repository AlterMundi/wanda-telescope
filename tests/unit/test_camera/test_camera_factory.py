"""Unit tests for camera factory functionality."""
import pytest
from unittest.mock import patch, Mock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from camera.factory import CameraFactory
from camera.implementations.mock_camera import MockCamera
from camera.implementations.usb_camera import USBCamera
from camera.exceptions import CameraInitializationError

class TestCameraFactory:
    def test_create_camera_returns_mock_when_no_hardware(self):
        """Test that factory returns mock camera when no hardware is available."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = False
            with patch.dict("sys.modules", {"picamera2": None}):
                camera = CameraFactory.create_camera()
                assert isinstance(camera, MockCamera)

    def test_create_camera_returns_pi_camera_when_available(self):
        """Test that factory returns PiCamera when picamera2 is available."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = False
            with patch("camera.implementations.pi_camera.PiCamera") as mock_pi_camera_class:
                mock_pi_camera = Mock()
                mock_pi_camera_class.return_value = mock_pi_camera
                with patch.dict("sys.modules", {"picamera2": Mock()}):
                    camera = CameraFactory.create_camera()
                    assert isinstance(camera, Mock)
                    mock_pi_camera_class.assert_called_once()

    def test_create_camera_returns_usb_camera_when_available(self):
        """Test that factory returns USBCamera when USB camera is available."""
        with patch("camera.factory.cv2") as mock_cv2:
            # Mock USB camera detection
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.read.return_value = (True, Mock())  # (ret, frame)
            mock_cv2.VideoCapture.return_value = mock_cap
            
            # Mock PiCamera import failure
            with patch.dict("sys.modules", {"picamera2": None}):
                camera = CameraFactory.create_camera()
                assert isinstance(camera, USBCamera)

    def test_create_camera_handles_usb_camera_detection_failure(self):
        """Test that factory handles USB camera detection failure gracefully."""
        with patch("camera.factory.cv2") as mock_cv2:
            # Mock USB camera detection failure
            mock_cv2.VideoCapture.side_effect = Exception("USB camera error")
            
            # Mock PiCamera import failure
            with patch.dict("sys.modules", {"picamera2": None}):
                camera = CameraFactory.create_camera()
                assert isinstance(camera, MockCamera)

    def test_create_camera_handles_usb_camera_not_opened(self):
        """Test that factory handles USB camera not opened."""
        with patch("camera.factory.cv2") as mock_cv2:
            # Mock USB camera not opened
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            mock_cv2.VideoCapture.return_value = mock_cap
            
            # Mock PiCamera import failure
            with patch.dict("sys.modules", {"picamera2": None}):
                camera = CameraFactory.create_camera()
                assert isinstance(camera, MockCamera)

    def test_create_camera_handles_usb_camera_read_failure(self):
        """Test that factory handles USB camera read failure."""
        with patch("camera.factory.cv2") as mock_cv2:
            # Mock USB camera read failure
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cap.read.return_value = (False, None)  # (ret, frame)
            mock_cv2.VideoCapture.return_value = mock_cap
            
            # Mock PiCamera import failure
            with patch.dict("sys.modules", {"picamera2": None}):
                camera = CameraFactory.create_camera()
                assert isinstance(camera, MockCamera)

    def test_create_camera_handles_general_exception(self):
        """Test that factory handles general exceptions during initialization."""
        with patch("camera.factory.cv2") as mock_cv2:
            # Mock USB camera detection failure
            mock_cv2.VideoCapture.side_effect = Exception("USB camera error")
            
            # Mock PiCamera constructor to raise an exception when instantiated
            with patch("camera.implementations.pi_camera.PiCamera", side_effect=Exception("PiCamera initialization error")):
                with patch.dict("sys.modules", {"picamera2": Mock()}):
                    with pytest.raises(CameraInitializationError) as exc_info:
                        CameraFactory.create_camera()
                    assert "Failed to initialize camera" in str(exc_info.value)

    def test_list_available_cameras(self):
        """Test listing available cameras."""
        cameras = CameraFactory.list_available_cameras()
        assert isinstance(cameras, list)

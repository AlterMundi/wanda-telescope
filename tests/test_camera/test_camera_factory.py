import pytest
from unittest.mock import patch, Mock
import sys, os, subprocess

# Mock cv2 before any camera imports to avoid import issues
sys.modules['cv2'] = Mock()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from camera.factory import CameraFactory
from camera.implementations.mock_camera import MockCamera
from camera.implementations.usb_camera import USBCamera
from camera.implementations.pi_camera import PiCamera

class TestCameraFactory:
    def test_check_rpicam_camera(self):
        """Test that check_rpicam_camera returns True when Raspberry Pi camera is detected."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "imx477"
            assert CameraFactory._check_rpicam_camera() == True

    def test_check_rpicam_camera_returns_false_when_no_camera_detected(self):
        """Test that check_rpicam_camera returns False when no Raspberry Pi camera is detected."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            assert CameraFactory._check_rpicam_camera() == False

    def test_check_rpicam_camera_handles_subprocess_exceptions(self):
        """Test that check_rpicam_camera returns False when subprocess raises exceptions."""
        # Test TimeoutExpired exception
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(['rpicam-still'], 10)
            assert CameraFactory._check_rpicam_camera() == False

        # Test SubprocessError exception
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("Command failed")
            assert CameraFactory._check_rpicam_camera() == False

        # Test FileNotFoundError exception
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("rpicam-still not found")
            assert CameraFactory._check_rpicam_camera() == False

    def test_create_camera_returns_pi_camera_when_available(self):
        """Test that create_camera returns PiCamera when Raspberry Pi camera is available."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = False
            with patch("camera.factory.PiCamera") as mock_pi_camera_class:
                mock_pi_camera = Mock()
                mock_pi_camera_class.return_value = mock_pi_camera
                with patch.dict("sys.modules", {"picamera2": Mock()}):
                    camera = CameraFactory.create_camera()
                    assert isinstance(camera, Mock)
                    mock_pi_camera_class.assert_called_once()

    def test_create_camera_returns_usb_camera_when_available(self):
        """Test that create_camera returns USBCamera when USB camera is available."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = True
            mock_cv2.VideoCapture.return_value.read.return_value = (True, None)
            with patch("camera.factory.USBCamera") as mock_usb_camera_class:
                mock_usb_camera = Mock()
                mock_usb_camera_class.return_value = mock_usb_camera
                with patch("camera.factory.CameraFactory._check_rpicam_camera", return_value=False):
                    with patch.dict("sys.modules", {}, clear=True):
                        # Clear picamera2 from sys.modules to simulate ImportError
                        if "picamera2" in sys.modules:
                            del sys.modules["picamera2"]
                        camera = CameraFactory.create_camera()
                        assert isinstance(camera, Mock)
                        mock_usb_camera_class.assert_called_once()

    def test_create_camera_handles_usb_camera_detection_exceptions(self):
        """Test that create_camera handles exceptions during USB camera detection and falls back to MockCamera."""
        with patch("camera.factory.cv2") as mock_cv2:
            # Make cv2 operations raise exceptions
            mock_cv2.VideoCapture.side_effect = Exception("USB camera access failed")
            with patch("camera.factory.MockCamera") as mock_mock_camera_class:
                mock_mock_camera = Mock()
                mock_mock_camera_class.return_value = mock_mock_camera
                with patch("camera.factory.CameraFactory._check_rpicam_camera", return_value=False):
                    with patch.dict("sys.modules", {}, clear=True):
                        # Clear picamera2 from sys.modules to simulate ImportError
                        if "picamera2" in sys.modules:
                            del sys.modules["picamera2"]
                        camera = CameraFactory.create_camera()
                        assert isinstance(camera, Mock)
                        mock_mock_camera_class.assert_called_once()

    def test_create_camera_returns_pi_camera_via_rpicam_fallback(self):
        """Test that create_camera returns PiCamera via rpicam-still fallback when picamera2 import fails but rpicam detects camera."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = False
            with patch("camera.factory.PiCamera") as mock_pi_camera_class:
                mock_pi_camera = Mock()
                mock_pi_camera_class.return_value = mock_pi_camera
                with patch("camera.factory.CameraFactory._check_rpicam_camera", return_value=True):
                    with patch.dict("sys.modules", {}, clear=True):
                        # Clear picamera2 from sys.modules to simulate ImportError
                        if "picamera2" in sys.modules:
                            del sys.modules["picamera2"]
                        camera = CameraFactory.create_camera()
                        assert isinstance(camera, Mock)
                        mock_pi_camera_class.assert_called_once()

    def test_create_camera_handles_pi_camera_init_failure_in_rpicam_fallback(self):
        """Test that create_camera handles PiCamera initialization failure in rpicam fallback and continues to USB detection."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = True
            mock_cv2.VideoCapture.return_value.read.return_value = (True, None)
            with patch("camera.factory.PiCamera") as mock_pi_camera_class:
                mock_pi_camera_class.side_effect = Exception("PiCamera initialization failed")
                with patch("camera.factory.USBCamera") as mock_usb_camera_class:
                    mock_usb_camera = Mock()
                    mock_usb_camera_class.return_value = mock_usb_camera
                    with patch("camera.factory.CameraFactory._check_rpicam_camera", return_value=True):
                        with patch.dict("sys.modules", {}, clear=True):
                            # Clear picamera2 from sys.modules to simulate ImportError
                            if "picamera2" in sys.modules:
                                del sys.modules["picamera2"]
                            camera = CameraFactory.create_camera()
                            assert isinstance(camera, Mock)
                            mock_pi_camera_class.assert_called_once()
                            mock_usb_camera_class.assert_called_once()

    def test_create_camera_returns_mock_camera_when_no_camera_available(self):
        """Test that create_camera returns MockCamera when no camera is available."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = False
            with patch("camera.factory.MockCamera") as mock_mock_camera_class:
                mock_mock_camera = Mock()
                mock_mock_camera_class.return_value = mock_mock_camera
                with patch("camera.factory.CameraFactory._check_rpicam_camera", return_value=False):
                    with patch.dict("sys.modules", {}, clear=True):
                        # Clear picamera2 from sys.modules to simulate ImportError
                        if "picamera2" in sys.modules:
                            del sys.modules["picamera2"]
                        camera = CameraFactory.create_camera()
                        assert isinstance(camera, Mock)
                        mock_mock_camera_class.assert_called_once()

    def test_create_camera_handles_unexpected_exceptions(self):
        """Test that create_camera re-raises unexpected exceptions with custom message."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = False
            with patch("camera.factory.MockCamera") as mock_mock_camera_class:
                # Make MockCamera raise an unexpected exception
                mock_mock_camera_class.side_effect = RuntimeError("Unexpected camera error")
                with patch("camera.factory.CameraFactory._check_rpicam_camera", return_value=False):
                    with patch.dict("sys.modules", {}, clear=True):
                        # Clear picamera2 from sys.modules to simulate ImportError
                        if "picamera2" in sys.modules:
                            del sys.modules["picamera2"]
                        with pytest.raises(Exception) as exc_info:
                            CameraFactory.create_camera()
                        assert "Failed to initialize camera" in str(exc_info.value)
                        assert "Unexpected camera error" in str(exc_info.value)
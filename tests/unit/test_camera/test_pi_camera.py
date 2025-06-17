import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import numpy as np
import cv2
import time

@pytest.fixture
def mock_picamera2():
    """Mock the picamera2 module."""
    mock_picamera2 = Mock()
    mock_h264_encoder = Mock()
    mock_file_output = Mock()
    
    with patch('camera.implementations.pi_camera.PiCamera._import_picamera2') as mock_import:
        mock_import.return_value = (mock_picamera2, mock_h264_encoder, mock_file_output)
        yield mock_picamera2

@pytest.fixture
def pi_camera(mock_picamera2):
    """Create a PiCamera instance with mocked dependencies."""
    from camera.implementations.pi_camera import PiCamera
    camera = PiCamera()
    camera.initialize()
    return camera

class TestPiCamera:
    def test_pi_camera_with_mocked_hardware(self, pi_camera):
        """Test Pi camera with mocked picamera2."""
        assert hasattr(pi_camera, "camera")
        assert hasattr(pi_camera, "exposure_us")
        assert pi_camera.exposure_us == 100000
        assert pi_camera.gain == 1.0
        assert pi_camera.use_digital_gain is False
        assert pi_camera.digital_gain == 1.0
        assert pi_camera.save_raw is False
        assert pi_camera.recording is False
        assert pi_camera.capture_status == "Ready"
        assert pi_camera.capture_dir == "captures"
        assert pi_camera.skip_frames == 0
        assert pi_camera.exposure_mode == "manual"

    def test_initialize_error(self, mock_picamera2):
        """Test camera initialization error handling."""
        from camera.implementations.pi_camera import PiCamera
        camera = PiCamera()
        
        # Set the side effect on the mock_picamera2 instance
        mock_picamera2.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            camera.initialize()

    def test_create_configurations(self, pi_camera):
        """Test creating camera configurations."""
        # Mock the camera instance
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        # Mock the configuration methods
        mock_cam_instance.create_preview_configuration.return_value = {"type": "preview"}
        mock_cam_instance.create_still_configuration.return_value = {"type": "still"}
        mock_cam_instance.create_video_configuration.return_value = {"type": "video"}
        
        preview_config = pi_camera.create_preview_configuration()
        assert isinstance(preview_config, dict)
        assert preview_config["type"] == "preview"
        
        still_config = pi_camera.create_still_configuration()
        assert isinstance(still_config, dict)
        assert still_config["type"] == "still"
        
        video_config = pi_camera.create_video_configuration()
        assert isinstance(video_config, dict)
        assert video_config["type"] == "video"

    def test_configure_and_controls(self, pi_camera):
        """Test camera configuration and controls."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        config = {"size": (1920, 1080)}
        pi_camera.configure(config)
        mock_cam_instance.configure.assert_called_once_with(config)
        
        controls = {"ExposureTime": 100000}
        pi_camera.set_controls(controls)
        mock_cam_instance.set_controls.assert_called_once_with(controls)

    def test_configure_error(self, pi_camera):
        """Test camera configuration error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.configure.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        with pytest.raises(Exception):
            pi_camera.configure({"size": (1920, 1080)})

    def test_start_stop(self, pi_camera):
        """Test camera start and stop."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        pi_camera.start()
        assert pi_camera.started is True
        mock_cam_instance.start.assert_called_once()
        
        pi_camera.stop()
        assert pi_camera.started is False
        mock_cam_instance.stop.assert_called_once()

    def test_start_error(self, pi_camera):
        """Test camera start error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.start.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        with pytest.raises(Exception):
            pi_camera.start()

    def test_recording(self, pi_camera):
        """Test video recording functionality."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        # Test start recording
        filename = "test_video.mp4"
        pi_camera.start_recording(None, filename)
        assert pi_camera.is_recording is True
        assert pi_camera.recording is True
        mock_cam_instance.start_recording.assert_called_once()
        
        # Test stop recording
        pi_camera.stop_recording()
        assert pi_camera.is_recording is False
        assert pi_camera.recording is False
        mock_cam_instance.stop_recording.assert_called_once()

    def test_start_recording_error(self, pi_camera):
        """Test start recording error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.start_recording.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        with pytest.raises(Exception):
            pi_camera.start_recording(None, "test.mp4")

    def test_capture_array(self, pi_camera):
        """Test capturing frame as array."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        # Mock the capture_array method
        mock_array = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_cam_instance.capture_array.return_value = mock_array
        
        result = pi_camera.capture_array()
        assert isinstance(result, np.ndarray)
        assert result.shape == (1080, 1920, 3)

    def test_capture_array_error(self, pi_camera):
        """Test capture array error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.capture_array.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        with pytest.raises(Exception):
            pi_camera.capture_array()

    def test_capture_file(self, pi_camera):
        """Test capturing frame to file."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        filename = "test_image.jpg"
        pi_camera.capture_file(filename)
        mock_cam_instance.capture_file.assert_called_once()

    def test_capture_file_error(self, pi_camera):
        """Test capture file error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.capture_file.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        with pytest.raises(Exception):
            pi_camera.capture_file("test.jpg")

    def test_exposure_conversion(self, pi_camera):
        """Test exposure time conversion methods."""
        # Test slider to microseconds conversion
        us = pi_camera.slider_to_us(50)
        assert isinstance(us, int)
        
        # Test microseconds to shutter string
        shutter_str = pi_camera.us_to_shutter_string(100000)
        assert isinstance(shutter_str, str)
        
        # Test gain to ISO conversion
        iso = pi_camera.gain_to_iso(1.0)
        assert isinstance(iso, int)
        
        # Test ISO to gain conversion
        gain = pi_camera.iso_to_gain(100)
        assert isinstance(gain, float)

    def test_exposure_settings(self, pi_camera):
        """Test exposure settings methods."""
        # Test get exposure seconds
        seconds = pi_camera.get_exposure_seconds()
        assert isinstance(seconds, float)
        
        # Test get exposure microseconds
        us = pi_camera.get_exposure_us()
        assert isinstance(us, int)
        
        # Test set exposure microseconds
        pi_camera.set_exposure_us(100000)
        assert pi_camera.exposure_us == 100000

    def test_set_exposure_error(self, pi_camera):
        """Test set exposure error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.set_controls.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        # Should not raise exception, just log warning
        pi_camera.set_exposure_us(100000)
        assert pi_camera.exposure_us == 100000

    def test_camera_settings_update(self, pi_camera):
        """Test camera settings update."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        pi_camera.update_camera_settings()
        mock_cam_instance.set_controls.assert_called_once()

    def test_camera_settings_update_error(self, pi_camera):
        """Test camera settings update error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.set_controls.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        # Should not raise exception, just log warning
        pi_camera.update_camera_settings()

    def test_get_frame(self, pi_camera):
        """Test getting a frame."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        # Create a test image
        test_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        # Mock the capture_array method to return the test image
        mock_cam_instance.capture_array.return_value = test_image
        
        # Get the frame
        frame = pi_camera.get_frame()
        
        # The frame should be JPEG bytes
        assert isinstance(frame, bytes)
        assert frame.startswith(b'\xff\xd8')  # JPEG header

    def test_get_frame_with_digital_gain(self, pi_camera):
        """Test getting a frame with digital gain."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        # Create a test image
        test_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        test_image.fill(100)  # Fill with a non-zero value
        
        # Mock the capture_array method to return the test image
        mock_cam_instance.capture_array.return_value = test_image
        
        # Enable digital gain
        pi_camera.use_digital_gain = True
        pi_camera.digital_gain = 2.0
        
        # Get the frame
        frame = pi_camera.get_frame()
        
        # The frame should be JPEG bytes
        assert isinstance(frame, bytes)
        assert frame.startswith(b'\xff\xd8')  # JPEG header

    def test_get_frame_error(self, pi_camera):
        """Test get frame error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.capture_array.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        frame = pi_camera.get_frame()
        assert frame is None

    def test_capture_still(self, pi_camera):
        """Test capturing a still image."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        # Mock the capture_file method
        mock_cam_instance.capture_file = Mock()
        
        # Capture the still
        result = pi_camera.capture_still()
        
        # Should return True on success
        assert result is True
        assert "Image saved as" in pi_camera.capture_status

    def test_capture_still_error(self, pi_camera):
        """Test capture still error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.capture_file.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        result = pi_camera.capture_still()
        assert result is False
        assert "Capture failed" in pi_camera.capture_status

    def test_start_video(self, pi_camera):
        """Test starting video recording."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        result = pi_camera.start_video()
        assert result is True
        assert pi_camera.is_recording is True

    def test_start_video_error(self, pi_camera):
        """Test start video error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.start_recording.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        result = pi_camera.start_video()
        assert result is False

    def test_stop_video(self, pi_camera):
        """Test stopping video recording."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        # Start recording first
        pi_camera.is_recording = True
        pi_camera.recording = True
        
        result = pi_camera.stop_video()
        assert result is True
        assert pi_camera.is_recording is False
        assert pi_camera.recording is False

    def test_stop_video_error(self, pi_camera):
        """Test stop video error handling."""
        mock_cam_instance = Mock()
        mock_cam_instance.stop_recording.side_effect = Exception("Test error")
        pi_camera.camera = mock_cam_instance
        
        # Start recording first
        pi_camera.is_recording = True
        pi_camera.recording = True
        
        # Mock the stop_recording method to raise an exception
        with patch.object(pi_camera, 'stop_recording', side_effect=Exception("Test error")):
            result = pi_camera.stop_video()
            assert result is False

    def test_cleanup(self, pi_camera):
        """Test camera cleanup."""
        mock_cam_instance = Mock()
        pi_camera.camera = mock_cam_instance
        
        pi_camera.cleanup()
        mock_cam_instance.close.assert_called_once()
"""Unit tests for camera capture directory handling."""
import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, Mock
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from camera.implementations.mock_camera import MockCamera
from camera.implementations.pi_camera import PiCamera
from camera.implementations.usb_camera import USBCamera


class TestCaptureDirectory:
    def test_mock_camera_uses_custom_capture_dir(self, test_capture_dir):
        """Test that mock camera uses the provided capture directory."""
        camera = MockCamera(capture_dir=test_capture_dir)
        
        # Verify the capture directory is set correctly
        assert camera.capture_dir == test_capture_dir
        
        # Initialize and capture a still image
        camera.initialize()
        result = camera.capture_still()
        
        # Verify capture was successful
        assert result is True
        
        # Check that the image was saved in the test directory
        files = os.listdir(test_capture_dir)
        assert len(files) == 1
        assert files[0].startswith("capture_")
        assert files[0].endswith(".jpg")

    def test_pi_camera_uses_custom_capture_dir(self, test_capture_dir):
        """Test that Pi camera uses the provided capture directory."""
        with patch('camera.implementations.pi_camera.PiCamera._import_picamera2') as mock_import:
            mock_picamera2 = Mock()
            mock_h264_encoder = Mock()
            mock_file_output = Mock()
            mock_import.return_value = (mock_picamera2, mock_h264_encoder, mock_file_output)
            
            camera = PiCamera(capture_dir=test_capture_dir)
            
            # Verify the capture directory is set correctly
            assert camera.capture_dir == test_capture_dir

    def test_usb_camera_uses_custom_capture_dir(self, test_capture_dir):
        """Test that USB camera uses the provided capture directory."""
        with patch('camera.implementations.usb_camera.cv2.VideoCapture') as mock_cv2:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_cv2.return_value = mock_cap
            
            camera = USBCamera(capture_dir=test_capture_dir)
            
            # Verify the capture directory is set correctly
            assert camera.capture_dir == test_capture_dir

    def test_capture_directory_is_isolated(self, test_capture_dir):
        """Test that test captures don't interfere with main project."""
        # Create a mock camera with test directory
        camera = MockCamera(capture_dir=test_capture_dir)
        camera.initialize()
        
        # Capture an image
        camera.capture_still()
        
        # Verify the image is in the test directory, not the main captures directory
        test_files = os.listdir(test_capture_dir)
        assert len(test_files) == 1
        
        # Check that main captures directory doesn't exist or is empty
        main_captures_dir = "captures"
        if os.path.exists(main_captures_dir):
            main_files = os.listdir(main_captures_dir)
            # Main directory should not contain our test file
            assert test_files[0] not in main_files

    def test_multiple_cameras_use_different_directories(self):
        """Test that multiple cameras can use different capture directories."""
        # Create two separate test directories
        temp_dir1 = tempfile.mkdtemp(prefix="test_captures_1_")
        temp_dir2 = tempfile.mkdtemp(prefix="test_captures_2_")
        
        try:
            camera1 = MockCamera(capture_dir=temp_dir1)
            camera2 = MockCamera(capture_dir=temp_dir2)
            
            # Initialize both cameras
            camera1.initialize()
            camera2.initialize()
            
            # Capture images with both cameras
            camera1.capture_still()
            import time
            time.sleep(1.0)  # Longer delay to ensure different timestamps
            camera2.capture_still()
            
            # Verify each camera saved to its own directory
            files1 = os.listdir(temp_dir1)
            files2 = os.listdir(temp_dir2)
            
            assert len(files1) == 1
            assert len(files2) == 1
            
            # Verify files are in their respective directories
            assert os.path.exists(os.path.join(temp_dir1, files1[0]))
            assert os.path.exists(os.path.join(temp_dir2, files2[0]))
            
            # Verify the files are different (different timestamps)
            assert files1[0] != files2[0], f"Files should have different names: {files1[0]} vs {files2[0]}"
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir1, ignore_errors=True)
            shutil.rmtree(temp_dir2, ignore_errors=True)


class TestMockCameraComprehensive:
    """Comprehensive tests for MockCamera to improve coverage."""
    
    def test_mock_camera_initialization_with_default_capture_dir(self):
        """Test MockCamera initialization with default capture directory."""
        camera = MockCamera()
        assert camera.capture_dir == "captures"
        assert camera.exposure_us == 100000
        assert camera.gain == 1.0
        assert camera.use_digital_gain is False
        assert camera.digital_gain == 1.0
        assert camera.save_raw is False
        assert camera.recording is False
        assert camera.capture_status == "Ready"
        assert camera.skip_frames == 0
        assert camera.exposure_mode == "manual"

    def test_mock_camera_webcam_initialization_success(self):
        """Test MockCamera webcam initialization when webcam is available."""
        with patch('camera.implementations.mock_camera.cv2.VideoCapture') as mock_cv2:
            mock_webcam = Mock()
            mock_webcam.isOpened.return_value = True
            mock_cv2.return_value = mock_webcam
            
            camera = MockCamera()
            assert camera.webcam is not None

    def test_mock_camera_webcam_initialization_failure(self):
        """Test MockCamera webcam initialization when webcam fails."""
        with patch('camera.implementations.mock_camera.cv2.VideoCapture') as mock_cv2:
            mock_cv2.side_effect = Exception("Webcam error")
            
            camera = MockCamera()
            assert camera.webcam is None

    def test_mock_camera_webcam_not_opened(self):
        """Test MockCamera when webcam is not opened."""
        with patch('camera.implementations.mock_camera.cv2.VideoCapture') as mock_cv2:
            mock_webcam = Mock()
            mock_webcam.isOpened.return_value = False
            mock_cv2.return_value = mock_webcam
            
            camera = MockCamera()
            assert camera.webcam is None

    def test_mock_camera_initialize_success(self, test_capture_dir):
        """Test MockCamera initialize method success."""
        camera = MockCamera(capture_dir=test_capture_dir)
        camera.initialize()
        assert camera.status == "Mock camera ready"
        assert os.path.exists(test_capture_dir)

    def test_mock_camera_initialize_failure(self):
        """Test MockCamera initialize method failure."""
        camera = MockCamera(capture_dir="/invalid/path/that/cannot/be/created")
        with pytest.raises(Exception):
            camera.initialize()
        assert "Mock camera error" in camera.status

    def test_mock_camera_configuration_methods(self):
        """Test MockCamera configuration methods."""
        camera = MockCamera()
        
        # Test configuration creation methods
        preview_config = camera.create_preview_configuration()
        assert preview_config["type"] == "preview"
        
        still_config = camera.create_still_configuration()
        assert still_config["type"] == "still"
        
        video_config = camera.create_video_configuration()
        assert video_config["type"] == "video"

    def test_mock_camera_start_stop(self):
        """Test MockCamera start and stop methods."""
        camera = MockCamera()
        
        assert camera.started is False
        camera.start()
        assert camera.started is True
        camera.stop()
        assert camera.started is False

    def test_mock_camera_capture_array_with_webcam(self):
        """Test MockCamera capture_array with webcam available."""
        with patch('camera.implementations.mock_camera.cv2.VideoCapture') as mock_cv2:
            mock_webcam = Mock()
            mock_webcam.isOpened.return_value = True
            # Create a proper numpy array for the frame
            import numpy as np
            mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            mock_webcam.read.return_value = (True, mock_frame)
            mock_cv2.return_value = mock_webcam
            
            camera = MockCamera()
            result = camera.capture_array()
            assert result is not None

    def test_mock_camera_capture_array_without_webcam(self):
        """Test MockCamera capture_array without webcam."""
        with patch('camera.implementations.mock_camera.cv2.VideoCapture') as mock_cv2:
            mock_webcam = Mock()
            mock_webcam.isOpened.return_value = False
            mock_cv2.return_value = mock_webcam
            
            camera = MockCamera()
            result = camera.capture_array()
            assert result is not None

    def test_mock_camera_capture_file(self, test_capture_dir):
        """Test MockCamera capture_file method."""
        camera = MockCamera(capture_dir=test_capture_dir)
        camera.initialize()
        
        filename = os.path.join(test_capture_dir, "test_capture.jpg")
        camera.capture_file(filename)
        assert os.path.exists(filename)

    def test_mock_camera_recording_methods(self):
        """Test MockCamera recording methods."""
        camera = MockCamera()
        
        assert camera.recording is False
        camera.start_recording(None, "test.mp4")
        assert camera.recording is True
        camera.stop_recording()
        assert camera.recording is False

    def test_mock_camera_cleanup(self):
        """Test MockCamera cleanup method."""
        with patch('camera.implementations.mock_camera.cv2.VideoCapture') as mock_cv2:
            mock_webcam = Mock()
            mock_webcam.isOpened.return_value = True
            mock_cv2.return_value = mock_webcam
            
            camera = MockCamera()
            assert camera.webcam is not None
            camera.cleanup()
            assert camera.webcam is None

    def test_mock_camera_utility_methods(self):
        """Test MockCamera utility methods."""
        camera = MockCamera()
        
        # Test exposure conversion methods
        shutter_str = camera.us_to_shutter_string(2000000)  # 2 seconds
        assert "2.0s" in shutter_str
        
        shutter_str = camera.us_to_shutter_string(500000)  # 1/2 second
        assert "1/2" in shutter_str
        
        # Test gain conversion methods
        iso = camera.gain_to_iso(2.0)
        assert iso == 200
        
        gain = camera.iso_to_gain(200)
        assert gain == 2.0
        
        # Test slider conversion
        us = camera.slider_to_us(500)
        assert isinstance(us, int)
        assert us > 0
        
        # Test exposure getters/setters
        camera.set_exposure_us(50000)
        assert camera.get_exposure_us() == 50000
        assert camera.get_exposure_seconds() == 0.05

    def test_mock_camera_get_frame_success(self):
        """Test MockCamera get_frame method success."""
        camera = MockCamera()
        frame_data = camera.get_frame()
        assert frame_data is not None
        assert isinstance(frame_data, bytes)

    def test_mock_camera_get_frame_with_digital_gain(self):
        """Test MockCamera get_frame method with digital gain enabled."""
        camera = MockCamera()
        camera.use_digital_gain = True
        camera.digital_gain = 2.0
        
        frame_data = camera.get_frame()
        assert frame_data is not None
        assert isinstance(frame_data, bytes)

    def test_mock_camera_get_frame_failure(self):
        """Test MockCamera get_frame method failure."""
        with patch('camera.implementations.mock_camera.cv2.imencode') as mock_imencode:
            mock_imencode.side_effect = Exception("Encoding error")
            
            camera = MockCamera()
            frame_data = camera.get_frame()
            assert frame_data is None

    def test_mock_camera_capture_still_failure(self, test_capture_dir):
        """Test MockCamera capture_still method failure."""
        camera = MockCamera(capture_dir=test_capture_dir)
        camera.initialize()
        
        # Mock cv2.imwrite to raise an exception
        with patch('camera.implementations.mock_camera.cv2.imwrite') as mock_imwrite:
            mock_imwrite.side_effect = Exception("Write error")
            
            result = camera.capture_still()
            assert result is False
            assert "Capture failed" in camera.capture_status

    def test_mock_h264_encoder(self):
        """Test MockH264Encoder class."""
        from camera.implementations.mock_camera import MockH264Encoder
        
        encoder = MockH264Encoder(bitrate=1000000)
        assert encoder.bitrate == 1000000
        
        encoder = MockH264Encoder()
        assert encoder.bitrate is None 
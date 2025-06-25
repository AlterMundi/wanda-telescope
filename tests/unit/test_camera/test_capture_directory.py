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
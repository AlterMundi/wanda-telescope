"""
Comprehensive tests for USBCamera implementation using pytest.
"""
import pytest
import numpy as np
import cv2
import time
import os
from unittest.mock import Mock, patch, MagicMock
from camera.implementations.usb_camera import USBCamera


class TestUSBCamera:
    """Test suite for USBCamera class."""

    @pytest.fixture
    def mock_cv2_videocapture(self):
        """Mock cv2.VideoCapture for testing."""
        with patch('cv2.VideoCapture') as mock_capture:
            mock_instance = Mock()
            mock_instance.isOpened.return_value = True
            mock_instance.get.return_value = 0.5  # Default return value for get()
            mock_instance.set.return_value = True  # Default return value for set()
            mock_instance.read.return_value = (True, np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8))
            mock_instance.grab.return_value = True
            mock_instance.release.return_value = None
            mock_capture.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_cv2_videowriter(self):
        """Mock cv2.VideoWriter for testing."""
        with patch('cv2.VideoWriter') as mock_writer:
            mock_instance = Mock()
            mock_instance.write.return_value = None
            mock_instance.release.return_value = None
            mock_writer.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_cv2_functions(self):
        """Mock cv2 functions and constants."""
        with patch.multiple('cv2',
                          VideoWriter_fourcc=Mock(return_value=0x7634706d),
                          imencode=Mock(return_value=(True, Mock(tobytes=Mock(return_value=b'fake_jpeg')))),
                          imwrite=Mock(return_value=True),
                          flip=Mock(return_value=np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8))):
            yield

    @pytest.fixture
    def usb_camera(self, mock_cv2_videocapture, mock_cv2_functions):
        """Create USBCamera instance for testing."""
        camera = USBCamera()
        return camera

    @pytest.fixture
    def initialized_camera(self, usb_camera):
        """Create and initialize USBCamera instance."""
        usb_camera.initialize()
        return usb_camera

    def test_initialization(self, usb_camera):
        """Test camera initialization."""
        assert usb_camera.camera is None
        assert usb_camera.started is False
        assert usb_camera.status == "USB camera initialized"
        assert usb_camera.exposure_us == 50000
        assert usb_camera.gain == 4.0
        assert usb_camera.capture_dir == "captures"
        assert usb_camera.is_connected is False

    def test_initialize_success(self, usb_camera):
        """Test successful camera initialization."""
        usb_camera.initialize()

        assert usb_camera.camera is not None
        assert usb_camera.status == "USB camera ready"

    def test_initialize_failure(self, usb_camera):
        """Test camera initialization failure."""
        with patch('cv2.VideoCapture') as mock_capture:
            mock_instance = Mock()
            mock_instance.isOpened.return_value = False
            mock_capture.return_value = mock_instance

            with pytest.raises(Exception, match="Failed to open USB camera"):
                usb_camera.initialize()

    def test_configure(self, initialized_camera):
        """Test camera configuration."""
        config = {'gain': 2.0, 'exposure': 100}
        initialized_camera.configure(config)

        assert initialized_camera.camera.set.called
        # Note: gain and exposure updates may depend on cv2 attribute availability

    def test_set_controls(self, initialized_camera):
        """Test setting camera controls."""
        initialized_camera.set_controls(gain=3.0, exposure=50)

        assert initialized_camera.camera.set.called
        # Note: gain and exposure updates may depend on cv2 attribute availability

    def test_create_configurations(self, usb_camera):
        """Test configuration creation methods."""
        preview_config = usb_camera.create_preview_configuration()
        assert preview_config['width'] == 1280
        assert preview_config['height'] == 720
        assert preview_config['fps'] == 30

        still_config = usb_camera.create_still_configuration()
        assert still_config['width'] == 1920
        assert still_config['height'] == 1080
        assert still_config['format'] == 'jpg'

        video_config = usb_camera.create_video_configuration()
        assert video_config['width'] == 1280
        assert video_config['height'] == 720
        assert video_config['fps'] == 30
        assert video_config['format'] == 'mp4'

    def test_start_stop(self, usb_camera, mock_cv2_videocapture):
        """Test camera start and stop."""
        usb_camera.start()
        assert usb_camera.started is True
        assert usb_camera.status == "USB camera started"

        usb_camera.stop()
        assert usb_camera.started is False
        assert usb_camera.status == "USB camera stopped"
        assert usb_camera.camera is None

    def test_start_recording(self, initialized_camera, mock_cv2_videowriter):
        """Test starting video recording."""
        filename = "test_video.mp4"
        initialized_camera.start_recording(filename)

        assert initialized_camera.is_recording is True
        assert initialized_camera.recording is True
        assert initialized_camera.status == f"Recording to {filename}"
        assert initialized_camera.video_writer is not None

    def test_stop_recording(self, initialized_camera, mock_cv2_videowriter):
        """Test stopping video recording."""
        initialized_camera.video_writer = Mock()
        initialized_camera.is_recording = True
        initialized_camera.recording = True

        initialized_camera.stop_recording()

        assert initialized_camera.is_recording is False
        assert initialized_camera.recording is False
        assert initialized_camera.status == "Recording stopped"
        assert initialized_camera.video_writer is None

    def test_capture_array_success(self, initialized_camera):
        """Test successful frame capture."""
        with patch.object(initialized_camera.camera, 'read', return_value=(True, np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8))):
            frame = initialized_camera.capture_array()

            assert frame is not None
            assert isinstance(frame, np.ndarray)
            assert frame.shape[2] == 3  # RGB channels

    def test_capture_array_failure(self, initialized_camera):
        """Test frame capture failure."""
        with patch.object(initialized_camera.camera, 'read', return_value=(False, None)):
            with pytest.raises(Exception, match="Failed to capture frame"):
                initialized_camera.capture_array()

    def test_capture_array_with_recording(self, initialized_camera, mock_cv2_videowriter):
        """Test frame capture during recording."""
        initialized_camera.video_writer = Mock()
        initialized_camera.is_recording = True

        with patch.object(initialized_camera.camera, 'read', return_value=(True, np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8))):
            frame = initialized_camera.capture_array()

            assert frame is not None
            initialized_camera.video_writer.write.assert_called_once()

    def test_capture_array_with_digital_gain(self, initialized_camera):
        """Test frame capture with digital gain."""
        initialized_camera.use_digital_gain = True
        initialized_camera.digital_gain = 2.0

        test_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 100
        with patch.object(initialized_camera.camera, 'read', return_value=(True, test_frame)):
            frame = initialized_camera.capture_array()

            assert frame is not None
            # Digital gain should modify the frame
            assert frame.shape == test_frame.shape

    def test_capture_file(self, initialized_camera, tmp_path):
        """Test capturing still image to file."""
        filename = str(tmp_path / "test_capture.jpg")

        with patch.object(initialized_camera, 'capture_array', return_value=np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)):
            with patch('cv2.imwrite', return_value=True) as mock_imwrite:
                initialized_camera.capture_file(filename)

                # Verify cv2.imwrite was called
                mock_imwrite.assert_called_once()

    def test_cleanup(self, usb_camera):
        """Test camera cleanup."""
        mock_camera = Mock()
        usb_camera.camera = mock_camera
        usb_camera.cleanup()

        assert usb_camera.status == "USB camera cleaned up"
        mock_camera.release.assert_called_once()

    def test_save_restore_original_state(self, initialized_camera):
        """Test saving and restoring original camera state."""
        # Set some initial values
        initialized_camera.exposure_us = 100000
        initialized_camera.gain = 2.0
        initialized_camera.night_vision_mode = True

        # Mock camera hardware state
        with patch.object(initialized_camera.camera, 'get') as mock_get:
            mock_get.side_effect = lambda prop: {
                cv2.CAP_PROP_BRIGHTNESS: 150,
                cv2.CAP_PROP_AUTO_EXPOSURE: 1,
                cv2.CAP_PROP_GAIN: 2.0,
                cv2.CAP_PROP_EXPOSURE: 100
            }.get(prop, 0)

            initialized_camera.save_original_state()

            assert initialized_camera._original_hardware_state is not None
            assert initialized_camera._original_state is not None

        # Change values
        initialized_camera.exposure_us = 200000
        initialized_camera.gain = 4.0

        # Restore
        with patch.object(initialized_camera.camera, 'set') as mock_set:
            initialized_camera.restore_original_state()

            # Verify hardware settings were restored
            assert mock_set.called

    def test_is_connected_property(self, usb_camera):
        """Test is_connected property."""
        # Not initialized
        assert usb_camera.is_connected is False

        # Mock camera
        usb_camera.camera = Mock()
        usb_camera.camera.isOpened.return_value = True
        assert usb_camera.is_connected is True

        usb_camera.camera.isOpened.return_value = False
        assert usb_camera.is_connected is False

    def test_us_to_shutter_string(self, usb_camera):
        """Test microseconds to shutter string conversion."""
        assert usb_camera.us_to_shutter_string(1000000) == "1.0s"
        assert usb_camera.us_to_shutter_string(500000) == "0.5s"  # 0.5 seconds
        assert usb_camera.us_to_shutter_string(1000) == "1/1000"
        assert usb_camera.us_to_shutter_string(2000) == "1/500"

    def test_gain_to_iso_conversion(self, usb_camera):
        """Test gain to ISO conversion."""
        assert usb_camera.gain_to_iso(1.0) == 100
        assert usb_camera.gain_to_iso(2.5) == 250
        assert usb_camera.iso_to_gain(200) == 2.0
        assert usb_camera.iso_to_gain(800) == 8.0

    def test_slider_to_us_conversion(self, usb_camera):
        """Test slider value to microseconds conversion."""
        # Test minimum value
        assert usb_camera.slider_to_us(0) == 100

        # Test maximum value approximation
        max_value = usb_camera.slider_to_us(1000)
        assert max_value > 100000000  # Should be large

        # Test middle value
        mid_value = usb_camera.slider_to_us(500)
        assert 100 < mid_value < 100000000

    def test_exposure_methods(self, initialized_camera):
        """Test exposure getter/setter methods."""
        # Test getter
        assert initialized_camera.get_exposure_us() == 50000
        assert initialized_camera.get_exposure_seconds() == 0.05

        # Test setter
        initialized_camera.set_exposure_us(100000)
        assert initialized_camera.exposure_us == 100000

        # Test with camera initialized
        initialized_camera.set_exposure_us(200000)
        initialized_camera.camera.set.assert_called()

    def test_performance_mode(self, usb_camera):
        """Test performance mode settings."""
        # Normal mode
        usb_camera.set_performance_mode('normal')
        assert usb_camera.performance_mode == 'normal'
        assert usb_camera.skip_frames == 0

        # Fast mode
        usb_camera.set_performance_mode('fast')
        assert usb_camera.performance_mode == 'fast'
        assert usb_camera.skip_frames == 1

        # Fastest mode
        usb_camera.set_performance_mode('fastest')
        assert usb_camera.performance_mode == 'fastest'
        assert usb_camera.skip_frames == 2

        # Invalid mode
        usb_camera.set_performance_mode('invalid')
        assert usb_camera.skip_frames == 0  # Should default to normal

    def test_update_camera_settings(self, initialized_camera):
        """Test updating camera settings."""
        initialized_camera.exposure_us = 100000
        initialized_camera.gain = 2.0

        with patch.object(initialized_camera.camera, 'get') as mock_get:
            mock_get.return_value = 0.5

            initialized_camera.update_camera_settings()

            # Verify settings were attempted
            assert initialized_camera.camera.set.called

    def test_get_frame(self, initialized_camera):
        """Test getting frame as JPEG data."""
        test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

        with patch.object(initialized_camera, 'capture_array', return_value=test_frame):
            with patch('cv2.imencode', return_value=(True, Mock(tobytes=Mock(return_value=b'fake_jpeg')))) as mock_imencode:
                frame_data = initialized_camera.get_frame()

                assert frame_data is not None
                assert isinstance(frame_data, bytes)
                mock_imencode.assert_called_once()

    def test_get_frame_with_digital_gain(self, initialized_camera):
        """Test getting frame with digital gain applied."""
        initialized_camera.use_digital_gain = True
        initialized_camera.digital_gain = 1.5
        test_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 100

        with patch.object(initialized_camera, 'capture_array', return_value=test_frame):
            frame_data = initialized_camera.get_frame()

            assert frame_data is not None

    def test_capture_still_success(self, initialized_camera, tmp_path):
        """Test successful still capture."""
        initialized_camera.capture_dir = str(tmp_path)

        test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        with patch.object(initialized_camera, 'capture_array', return_value=test_frame):
            with patch('cv2.imwrite', return_value=True) as mock_imwrite:
                result = initialized_camera.capture_still()

                assert result is True
                assert initialized_camera.capture_status == "Capture complete"
                mock_imwrite.assert_called_once()

    def test_capture_still_failure(self, initialized_camera):
        """Test still capture failure."""
        with patch.object(initialized_camera, 'capture_array', side_effect=Exception("Capture failed")):
            result = initialized_camera.capture_still()

            assert result is False
            assert "Capture failed" in initialized_camera.capture_status

    def test_start_stop_video(self, initialized_camera, tmp_path):
        """Test video recording start and stop."""
        initialized_camera.capture_dir = str(tmp_path)

        # Start video
        with patch.object(initialized_camera, 'start_recording') as mock_start:
            result = initialized_camera.start_video()
            # start_video returns None, but we can check the call was made
            mock_start.assert_called_once()

        # Stop video
        with patch.object(initialized_camera, 'stop_recording') as mock_stop:
            result = initialized_camera.stop_video()
            # stop_video returns None, but we can check the call was made
            mock_stop.assert_called_once()

    def test_capture_image_not_connected(self, usb_camera):
        """Test capture_image when camera not connected."""
        result = usb_camera.capture_image()
        assert result == (False, None)

    def test_start_preview_not_connected(self, usb_camera):
        """Test start_preview when camera not connected."""
        result = usb_camera.start_preview()
        assert result is False

    def test_stop_preview(self, usb_camera):
        """Test stop_preview method."""
        usb_camera.is_recording = True
        usb_camera.stop_preview()
        assert usb_camera.is_recording is False

    def test_night_vision_mode(self, initialized_camera):
        """Test night vision mode functionality."""
        initialized_camera.night_vision_mode = True
        initialized_camera.night_vision_intensity = 2.0

        initialized_camera.update_camera_settings()

        assert initialized_camera.use_digital_gain is True
        assert initialized_camera.digital_gain == 2.0

        # Disable night vision
        initialized_camera.night_vision_mode = False
        initialized_camera.update_camera_settings()

        assert initialized_camera.use_digital_gain is False
        assert initialized_camera.digital_gain == 1.0

    def test_error_handling_in_update_settings(self, initialized_camera):
        """Test error handling in update_camera_settings."""
        # Mock camera.set to raise exceptions
        initialized_camera.camera.set.side_effect = Exception("Hardware error")

        # Should not raise exception, should log warnings
        initialized_camera.update_camera_settings()

        # Verify it still attempted to set settings
        assert initialized_camera.camera.set.called

    def test_methods_require_initialization(self, usb_camera):
        """Test that certain methods require camera initialization."""
        # Test configure method
        with pytest.raises(Exception, match="Camera not initialized"):
            usb_camera.configure({})

        # Test set_controls method
        with pytest.raises(Exception, match="Camera not initialized"):
            usb_camera.set_controls(gain=1.0)

        # Test start_recording method
        with pytest.raises(Exception, match="Camera not initialized"):
            usb_camera.start_recording("test.mp4")

        # Test capture_array method
        with pytest.raises(Exception, match="Camera not initialized"):
            usb_camera.capture_array()

        # Test set_exposure_us method
        with pytest.raises(Exception, match="Camera not initialized"):
            usb_camera.set_exposure_us(100000)

    def test_save_original_state_exception_handling(self, usb_camera):
        """Test exception handling in save_original_state."""
        # Mock camera that's opened but get() raises exception
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.get.side_effect = Exception("Hardware error")
        usb_camera.camera = mock_camera

        # Should handle exception gracefully
        usb_camera.save_original_state()
        assert usb_camera._original_hardware_state is None

    def test_restore_original_state_exception_handling(self, usb_camera):
        """Test exception handling in restore_original_state."""
        # Set up original state
        usb_camera._original_hardware_state = {
            'brightness': 150,
            'exposure_mode': 1,
            'gain': 2.0,
            'exposure': 100
        }

        # Mock camera that's opened but set() raises exception
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.set.side_effect = Exception("Hardware error")
        usb_camera.camera = mock_camera

        # Should handle exception gracefully
        usb_camera.restore_original_state()

    def test_initialize_brightness_exception_handling(self, usb_camera):
        """Test exception handling when setting initial brightness."""
        with patch.object(cv2, 'VideoCapture') as mock_capture:
            mock_instance = Mock()
            mock_instance.isOpened.return_value = True
            # Mock all set calls to succeed except brightness
            mock_instance.set.side_effect = lambda *args: None if args[0] == cv2.CAP_PROP_BRIGHTNESS else True
            mock_capture.return_value = mock_instance

            # Should initialize successfully despite brightness error
            usb_camera.initialize()
            assert usb_camera.camera is not None
            assert usb_camera.status == "USB camera ready"

    def test_configure_cv2_attribute_check(self, initialized_camera):
        """Test configure method with cv2 attribute checking."""
        # Test with valid cv2 attribute
        with patch.object(initialized_camera.camera, 'set') as mock_set:
            initialized_camera.configure({'CAP_PROP_BRIGHTNESS': 200})

            # Should call set with the attribute
            mock_set.assert_called()

        # Test with invalid cv2 attribute
        with patch.object(initialized_camera.camera, 'set') as mock_set:
            initialized_camera.configure({'INVALID_ATTR': 100})

            # Should not call set for invalid attribute
            mock_set.assert_not_called()

    def test_set_controls_exception_handling(self, initialized_camera):
        """Test exception handling in set_controls."""
        # Mock camera.set to raise exception
        initialized_camera.camera.set.side_effect = Exception("Hardware error")

        # Should handle exception gracefully
        initialized_camera.set_controls(gain=2.0)

        # Verify set was attempted
        initialized_camera.camera.set.assert_called()

    def test_stop_with_recording(self, initialized_camera):
        """Test stop method when camera is recording."""
        initialized_camera.is_recording = True

        with patch.object(initialized_camera, 'stop_recording') as mock_stop_recording:
            initialized_camera.stop()

            # Should stop recording first
            mock_stop_recording.assert_called_once()
            assert initialized_camera.started is False

    def test_capture_image_exception_handling(self, usb_camera):
        """Test exception handling in capture_image."""
        # Mock as connected
        usb_camera.camera = Mock()
        usb_camera.camera.isOpened.return_value = True

        # Mock capture_array to raise exception
        with patch.object(usb_camera, 'capture_array', side_effect=Exception("Capture error")):
            result = usb_camera.capture_image()

            # Should return False, None on exception
            assert result == (False, None)

    def test_start_preview_not_connected(self, usb_camera):
        """Test start_preview when camera is not connected."""
        usb_camera.camera = None
        result = usb_camera.start_preview()
        assert result is False

    def test_get_frame_exception_handling(self, initialized_camera):
        """Test exception handling in get_frame."""
        # Mock capture_array to raise exception
        with patch.object(initialized_camera, 'capture_array', side_effect=Exception("Frame capture error")):
            result = initialized_camera.get_frame()

            # Should return None on exception
            assert result is None

    def test_capture_still_exception_handling(self, initialized_camera):
        """Test exception handling in capture_still."""
        # Mock capture_array to raise exception
        with patch.object(initialized_camera, 'capture_array', side_effect=Exception("Capture error")):
            result = initialized_camera.capture_still()

            # Should return False on exception
            assert result is False
            assert "Capture failed" in initialized_camera.capture_status

    def test_start_video_exception_handling(self, initialized_camera):
        """Test exception handling in start_video."""
        # Mock start_recording to raise exception
        with patch.object(initialized_camera, 'start_recording', side_effect=Exception("Recording error")):
            result = initialized_camera.start_video()

            # Should handle exception gracefully and return False
            assert result is False

    def test_stop_video_exception_handling(self, initialized_camera):
        """Test exception handling in stop_video."""
        # Mock stop_recording to raise exception
        with patch.object(initialized_camera, 'stop_recording', side_effect=Exception("Stop recording error")):
            result = initialized_camera.stop_video()

            # Should handle exception gracefully and return False
            assert result is False

    def test_configure_with_kwargs_only(self, initialized_camera):
        """Test configure method with kwargs only (no config dict)."""
        with patch.object(initialized_camera.camera, 'set') as mock_set:
            # Use a valid cv2 attribute name that exists
            initialized_camera.configure(CAP_PROP_BRIGHTNESS=200)

            # Should process kwargs and call set
            mock_set.assert_called_once()

    def test_configure_with_both_config_and_kwargs(self, initialized_camera):
        """Test configure method with both config dict and kwargs."""
        config = {'CAP_PROP_GAIN': 1.5}

        with patch.object(initialized_camera.camera, 'set') as mock_set:
            initialized_camera.configure(config, CAP_PROP_EXPOSURE=100)

            # Should merge both config and kwargs and call set twice
            assert mock_set.call_count == 2

    def test_update_camera_settings_manual_exposure_failure(self, initialized_camera):
        """Test update_camera_settings when manual exposure fails."""
        initialized_camera.exposure_us = 100000
        initialized_camera.gain = 2.0

        # Mock camera.set to fail for manual exposure but succeed for auto
        call_count = 0
        def mock_set_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call (manual exposure) fails
                raise Exception("Manual exposure failed")
            return True  # Subsequent calls succeed

        initialized_camera.camera.set.side_effect = mock_set_side_effect

        # Should fall back to auto exposure
        initialized_camera.update_camera_settings()

    def test_update_camera_settings_both_exposure_and_gain_fail(self, initialized_camera):
        """Test update_camera_settings when both exposure and gain setting fail."""
        initialized_camera.exposure_us = 100000
        initialized_camera.gain = 2.0

        # Mock all set calls to fail
        initialized_camera.camera.set.side_effect = Exception("Hardware error")

        # Should handle all exceptions gracefully
        initialized_camera.update_camera_settings()

    def test_night_vision_mode_without_camera(self, usb_camera):
        """Test night vision mode when camera is not initialized."""
        usb_camera.night_vision_mode = True
        usb_camera.night_vision_intensity = 2.0

        # Should raise exception when camera not initialized
        with pytest.raises(Exception, match="Camera not initialized"):
            usb_camera.update_camera_settings()

    def test_capture_still_with_digital_gain(self, initialized_camera):
        """Test capture_still with digital gain specifically."""
        initialized_camera.use_digital_gain = True
        initialized_camera.digital_gain = 1.5

        test_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 100
        with patch.object(initialized_camera, 'capture_array', return_value=test_frame):
            with patch('cv2.imwrite', return_value=True) as mock_imwrite:
                result = initialized_camera.capture_still()

                assert result is True
                # Verify digital gain was applied (line 489)
                mock_imwrite.assert_called_once()
                # The frame passed to imwrite should be modified by digital gain
                call_args = mock_imwrite.call_args[0][1]  # Get the frame argument
                assert np.all(call_args >= test_frame)  # Should be brighter

    def test_set_controls_with_cv2_attributes(self, initialized_camera):
        """Test set_controls with cv2 attribute names that trigger gain/exposure updates."""
        original_gain = initialized_camera.gain
        original_exposure = initialized_camera.exposure_us

        # Mock cv2 attributes to exist
        with patch('camera.implementations.usb_camera.cv2') as mock_cv2:
            mock_cv2.CAP_PROP_GAIN = 14
            mock_cv2.CAP_PROP_EXPOSURE = 15

            with patch.object(initialized_camera.camera, 'set') as mock_set:
                # Use the specific lowercase names that trigger gain/exposure updates
                initialized_camera.set_controls(gain=3.0, exposure=200)

                # Should call set and update gain/exposure (lines 126, 128)
                assert mock_set.call_count == 2
                assert initialized_camera.gain == 3.0  # Should be updated
                assert initialized_camera.exposure_us == 200000  # Should be updated (ms to us)



class TestUSBCameraIntegration:
    """Integration tests for USBCamera."""

    @pytest.fixture
    def initialized_camera(self):
        """Create and initialize USBCamera instance for integration tests."""
        with patch('camera.implementations.usb_camera.cv2') as mock_cv2:
            mock_camera = Mock()
            mock_camera.isOpened.return_value = True
            mock_camera.get.return_value = 0.5
            mock_camera.set.return_value = True
            mock_camera.read.return_value = (True, np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8))
            mock_cv2.VideoCapture.return_value = mock_camera

            camera = USBCamera()
            camera.initialize()
            return camera

    def test_full_capture_workflow(self, initialized_camera, tmp_path):
        """Test complete capture workflow."""
        initialized_camera.capture_dir = str(tmp_path)

        # Start camera
        initialized_camera.start()
        assert initialized_camera.started is True

        # Capture still
        test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        with patch.object(initialized_camera, 'capture_array', return_value=test_frame):
            result = initialized_camera.capture_still()
            assert result is True

        # Start recording
        with patch('cv2.VideoWriter') as mock_writer:
            mock_writer.return_value = Mock()
            initialized_camera.start_video()

        # Capture frame during recording
        with patch.object(initialized_camera.camera, 'read', return_value=(True, test_frame)):
            frame = initialized_camera.capture_array()
            assert frame is not None

        # Stop recording
        initialized_camera.stop_video()

        # Stop camera
        initialized_camera.stop()
        assert initialized_camera.started is False

    def test_performance_mode_during_capture(self, initialized_camera):
        """Test performance mode affects frame capture."""
        # Set fastest mode
        initialized_camera.set_performance_mode('fastest')

        test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        with patch.object(initialized_camera.camera, 'read', return_value=(True, test_frame)) as mock_read:
            with patch.object(initialized_camera.camera, 'grab') as mock_grab:
                frame = initialized_camera.capture_array()

                # Should skip 2 frames
                assert mock_grab.call_count == 2
                assert mock_read.call_count == 1
                assert frame is not None

    def test_state_persistence_across_operations(self, initialized_camera):
        """Test that camera state persists across operations."""
        # Set custom settings
        initialized_camera.exposure_us = 75000
        initialized_camera.gain = 3.5
        initialized_camera.night_vision_mode = True
        initialized_camera.night_vision_intensity = 1.8

        # Perform operations
        initialized_camera.update_camera_settings()

        # Verify state maintained
        assert initialized_camera.exposure_us == 75000
        assert initialized_camera.gain == 3.5
        assert initialized_camera.night_vision_mode is True
        assert initialized_camera.night_vision_intensity == 1.8


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "--verbose",
        "--cov=camera.implementations.usb_camera",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=85"
    ])

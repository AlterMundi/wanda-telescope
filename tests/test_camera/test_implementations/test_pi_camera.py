import pytest
import logging
from unittest.mock import patch, PropertyMock
from camera.implementations.pi_camera import PiCamera

class TestPiCamera:
    def test_init_default_values(self):
        """Test PiCamera initialization with default values."""
        # Act
        camera = PiCamera()

        # Assert - Check all default attribute values
        assert camera.camera is None
        assert camera.is_recording is False
        assert camera.video_encoder is None
        assert camera.video_output is None
        assert camera.status == "Pi camera initialized"

        # Camera settings attributes
        assert camera.exposure_us == 100000
        assert camera.gain == 1.0
        assert camera.use_digital_gain is False
        assert camera.digital_gain == 1.0
        assert camera.save_raw is False
        assert camera.recording is False
        assert camera.capture_status == "Ready"
        assert camera.capture_dir == "captures"  # Default value
        assert camera.skip_frames == 0
        assert camera.exposure_mode == "manual"


    @patch('camera.implementations.pi_camera.logger')
    def test_init_logs_creation(self, mock_logger):
        """Test that PiCamera logs its creation."""
        # Act
        PiCamera()

        # Assert
        mock_logger.info.assert_called_once_with("Pi camera instance created")

    @patch('camera.implementations.pi_camera.AbstractCamera.__init__')
    def test_init_calls_super_init(self, mock_super_init):
        """Test that PiCamera calls its parent class __init__."""
        # Act
        PiCamera()

        # Assert
        mock_super_init.assert_called_once()

    @patch('camera.implementations.pi_camera.AbstractCamera.save_original_state')
    def test_save_original_state_calls_super(self, mock_super_save):
        """Test that PiCamera calls parent's save_original_state."""
        camera = PiCamera()
        camera.save_original_state()
        mock_super_save.assert_called_once()

    @patch('camera.implementations.pi_camera.AbstractCamera.save_original_state')
    def test_save_original_state_no_camera(self, mock_super_save):
        """Test save_original_state when camera is None."""
        camera = PiCamera()
        camera.camera = None  # Explicitly set to None
        camera.save_original_state()

        # Should not set _original_hardware_state since camera is None
        assert not hasattr(camera, '_original_hardware_state') or camera._original_hardware_state is None

    @patch('camera.implementations.pi_camera.AbstractCamera.save_original_state')
    @patch('camera.implementations.pi_camera.logger')
    def test_save_original_state_with_camera(self, mock_logger, mock_super_save):
        """Test save_original_state when camera exists."""
        camera = PiCamera()

        # Mock camera object
        mock_camera = patch('camera.implementations.pi_camera.Picamera2').start()
        camera.camera = mock_camera

        # Mock camera controls
        mock_controls = {'ExposureTime': 100000, 'AnalogueGain': 1.0}
        mock_camera.camera_controls = mock_controls

        camera.save_original_state()

        # Should set _original_hardware_state
        assert hasattr(camera, '_original_hardware_state')
        assert camera._original_hardware_state['controls'] == mock_controls
        assert camera._original_hardware_state['exposure_mode'] == 'manual'
        mock_logger.info.assert_called_with("Saved original Pi camera hardware state")

    @patch('camera.implementations.pi_camera.AbstractCamera.save_original_state')
    @patch('camera.implementations.pi_camera.logger')
    def test_save_original_state_with_camera_exception(self, mock_logger, mock_super_save):
        """Test save_original_state when accessing camera controls raises exception."""
        camera = PiCamera()

        # Mock camera object
        mock_camera = patch('camera.implementations.pi_camera.Picamera2').start()
        camera.camera = mock_camera

        # Mock camera controls to raise exception
        type(mock_camera).camera_controls = PropertyMock(side_effect=Exception("Test exception"))

        camera.save_original_state()

        # Should set _original_hardware_state to None due to exception
        assert hasattr(camera, '_original_hardware_state')
        assert camera._original_hardware_state is None
        mock_logger.warning.assert_called_with("Could not save original hardware state: Test exception")

    @patch('camera.implementations.pi_camera.AbstractCamera.restore_original_state')
    def test_restore_original_state_calls_super(self, mock_super_restore):
        """Test that PiCamera calls parent's restore_original_state."""
        camera = PiCamera()
        camera.restore_original_state()
        mock_super_restore.assert_called_once()

    @patch('camera.implementations.pi_camera.AbstractCamera.restore_original_state')
    def test_restore_original_state_no_camera(self, mock_super_restore):
        """Test restore_original_state when camera is None."""
        camera = PiCamera()
        camera.camera = None  # Explicitly set to None
        camera._original_hardware_state = None

        # Should not raise exception since camera is None
        camera.restore_original_state()

    @patch('camera.implementations.pi_camera.AbstractCamera.restore_original_state')
    @patch('camera.implementations.pi_camera.logger')
    def test_restore_original_state_with_camera(self, mock_logger, mock_super_restore):
        """Test restore_original_state when camera exists and has saved state."""
        camera = PiCamera()

        # Mock camera object
        mock_camera = patch('camera.implementations.pi_camera.Picamera2').start()
        camera.camera = mock_camera

        # Set up original hardware state
        original_controls = {'ExposureTime': 200000, 'AnalogueGain': 2.0}
        camera._original_hardware_state = {
            'controls': original_controls,
            'exposure_mode': 'auto'
        }

        camera.restore_original_state()

        # Should restore controls and exposure mode
        mock_camera.set_controls.assert_called_once_with(original_controls)
        assert camera.exposure_mode == 'auto'
        mock_logger.info.assert_called_with("Restored original Pi camera hardware state")

    @patch('camera.implementations.pi_camera.AbstractCamera.restore_original_state')
    @patch('camera.implementations.pi_camera.logger')
    def test_restore_original_state_with_camera_exception(self, mock_logger, mock_super_restore):
        """Test restore_original_state when setting controls raises exception."""
        camera = PiCamera()
        camera.exposure_mode = 'manual'  # Start with different mode

        # Mock camera object
        mock_camera = patch('camera.implementations.pi_camera.Picamera2').start()
        camera.camera = mock_camera

        # Mock set_controls to raise exception
        mock_camera.set_controls.side_effect = Exception("Set controls failed")

        # Set up original hardware state
        original_controls = {'ExposureTime': 200000, 'AnalogueGain': 2.0}
        camera._original_hardware_state = {
            'controls': original_controls,
            'exposure_mode': 'auto'
        }

        camera.restore_original_state()

        # Should still set exposure mode despite set_controls exception
        assert camera.exposure_mode == 'auto'
        mock_logger.warning.assert_called_with("Could not restore original hardware state: Set controls failed")

    @patch('camera.implementations.pi_camera.Picamera2.global_camera_info')
    @patch('camera.implementations.pi_camera.Picamera2')
    @patch('camera.implementations.pi_camera.os.makedirs')
    @patch('camera.implementations.pi_camera.logger')
    def test_initialize_success(self, mock_logger, mock_makedirs, mock_picamera2_class, mock_global_camera_info):
        """Test successful Pi camera initialization."""
        # Setup mocks
        mock_global_camera_info.return_value = [{'id': 'test_camera'}]
        mock_camera_instance = mock_picamera2_class.return_value

        camera = PiCamera()
        camera.initialize()

        # Verify camera creation and initialization
        mock_picamera2_class.assert_called_once()
        assert camera.camera == mock_camera_instance
        assert camera.status == "Pi camera ready"
        mock_makedirs.assert_called_once_with("captures", exist_ok=True)
        mock_logger.info.assert_any_call("Detected 1 camera(s)")
        mock_logger.info.assert_any_call("Pi camera hardware initialized successfully")

    @patch('camera.implementations.pi_camera.Picamera2.global_camera_info')
    @patch('camera.implementations.pi_camera.logger')
    def test_initialize_no_cameras(self, mock_logger, mock_global_camera_info):
        """Test initialization when no cameras are detected."""
        mock_global_camera_info.return_value = []

        camera = PiCamera()

        with pytest.raises(Exception) as exc_info:
            camera.initialize()

        assert "No cameras detected" in str(exc_info.value)
        mock_logger.info.assert_any_call("Pi camera: initialize()")

    @patch('camera.implementations.pi_camera.Picamera2.global_camera_info')
    @patch('camera.implementations.pi_camera.Picamera2')
    @patch('camera.implementations.pi_camera.time.sleep')
    @patch('camera.implementations.pi_camera.logger')
    def test_initialize_retry_on_indexerror(self, mock_logger, mock_sleep, mock_picamera2_class, mock_global_camera_info):
        """Test initialization retries on IndexError."""
        # First call raises IndexError, second call succeeds
        mock_global_camera_info.side_effect = [IndexError("test"), [{'id': 'test_camera'}]]

        camera = PiCamera()
        camera.initialize()

        # Should have retried once
        assert mock_sleep.call_count == 1
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_any_call("Pi camera hardware initialized successfully")

    @patch('camera.implementations.pi_camera.time.sleep')
    @patch('camera.implementations.pi_camera.logger')
    def test_initialize_max_retries_exceeded(self, mock_logger, mock_sleep):
        """Test initialization when max retries are exceeded (lines 114-118)."""
        # Mock Picamera2.global_camera_info to always raise IndexError
        with patch('camera.implementations.pi_camera.Picamera2.global_camera_info', side_effect=IndexError("Camera not found")):
            camera = PiCamera()

            # Should raise exception after 3 retries
            with pytest.raises(Exception) as exc_info:
                camera.initialize()

            # Verify error message
            assert "Failed to initialize Pi camera after 3 attempts" in str(exc_info.value)
            assert "The camera hardware is not responding" in str(exc_info.value)

            # Verify sleep was called 2 times (attempts 0 and 1, but not attempt 2)
            assert mock_sleep.call_count == 2

            # Verify status was set
            assert camera.status == "Pi camera error: Hardware connection issue"

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_create_preview_configuration_default(self, mock_picamera2_class):
        """Test create_preview_configuration with default parameters."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'size': (1440, 1080)}
        mock_camera_instance.create_preview_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        result = camera.create_preview_configuration()

        mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 1080)})
        assert result == mock_config

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_create_preview_configuration_custom_main(self, mock_picamera2_class):
        """Test create_preview_configuration with custom main parameter."""
        mock_camera_instance = mock_picamera2_class.return_value
        custom_main = {'size': (1920, 1080), 'format': 'RGB888'}
        mock_config = {'size': (1920, 1080)}
        mock_camera_instance.create_preview_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        result = camera.create_preview_configuration(main=custom_main)

        mock_camera_instance.create_preview_configuration.assert_called_once_with(main=custom_main)
        assert result == mock_config

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_create_still_configuration_default(self, mock_picamera2_class):
        """Test create_still_configuration with default parameters."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (4056, 3040)}}
        mock_camera_instance.create_still_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        result = camera.create_still_configuration()

        expected_config = {'main': {'size': (4056, 3040)}}
        mock_camera_instance.create_still_configuration.assert_called_once_with(**expected_config)
        assert result == mock_config

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_create_still_configuration_with_raw(self, mock_picamera2_class):
        """Test create_still_configuration with raw parameter and save_raw enabled."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (4056, 3040)}, 'raw': {'size': (4056, 3040)}}
        mock_camera_instance.create_still_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.save_raw = True

        result = camera.create_still_configuration(raw={'format': 'RAW'})

        expected_config = {'main': {'size': (4056, 3040)}, 'raw': {'size': (4056, 3040)}}
        mock_camera_instance.create_still_configuration.assert_called_once_with(**expected_config)
        assert result == mock_config

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_create_still_configuration_without_raw_when_save_raw_false(self, mock_picamera2_class):
        """Test create_still_configuration ignores raw parameter when save_raw is False."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (4056, 3040)}}
        mock_camera_instance.create_still_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.save_raw = False  # Explicitly set to False

        result = camera.create_still_configuration(raw={'format': 'RAW'})

        expected_config = {'main': {'size': (4056, 3040)}}
        mock_camera_instance.create_still_configuration.assert_called_once_with(**expected_config)
        assert result == mock_config

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_create_video_configuration_default(self, mock_picamera2_class):
        """Test create_video_configuration with default parameters."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'size': (1920, 1080), 'format': 'RGB888'}
        mock_camera_instance.create_video_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        result = camera.create_video_configuration()

        mock_camera_instance.create_video_configuration.assert_called_once_with(main={'size': (1920, 1080), 'format': 'RGB888'})
        assert result == mock_config

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_create_video_configuration_custom_main(self, mock_picamera2_class):
        """Test create_video_configuration with custom main parameter."""
        mock_camera_instance = mock_picamera2_class.return_value
        custom_main = {'size': (1280, 720), 'format': 'YUV420'}
        mock_config = {'size': (1280, 720), 'format': 'YUV420'}
        mock_camera_instance.create_video_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        result = camera.create_video_configuration(main=custom_main)

        mock_camera_instance.create_video_configuration.assert_called_once_with(main=custom_main)
        assert result == mock_config

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_configure(self, mock_picamera2_class):
        """Test configure."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (1920, 1080)}}

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.configure(mock_config)
        mock_camera_instance.configure.assert_called_once_with(mock_config)

    def test_configure_no_camera(self):
        """Test configure when camera is not initialized."""
        camera = PiCamera()
        camera.camera = None

        with pytest.raises(Exception, match="Camera not initialized"):
            camera.configure({'main': {'size': (1920, 1080)}})

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_set_controls(self, mock_picamera2_class):
        """Test set_controls."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'ExposureTime': 100000, 'AnalogueGain': 1.0}

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.set_controls(mock_config)
        mock_camera_instance.set_controls.assert_called_once_with(mock_config)

    def test_set_controls_no_camera(self):
        """Test set_controls when camera is not initialized."""
        camera = PiCamera()
        camera.camera = None

        with pytest.raises(Exception, match="Camera not initialized"):
            camera.set_controls({'ExposureTime': 100000})

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_start(self, mock_picamera2_class):
        """Test start."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (1440, 1080)}}
        mock_camera_instance.create_preview_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        camera.start()

        # Verify camera operations were called
        mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 1080)})
        mock_camera_instance.configure.assert_called_once_with(mock_config)
        mock_camera_instance.start.assert_called_once()

        # Verify state changes
        assert camera.started == True
        assert camera.status == "Pi camera started"

    @patch('camera.implementations.pi_camera.Picamera2')
    @patch('camera.implementations.pi_camera.os.makedirs')
    @patch('camera.implementations.pi_camera.logger')
    def test_start_uninitialized_camera(self, mock_logger, mock_makedirs, mock_picamera2_class):
        """Test start when camera is not initialized (line 166)."""
        # Setup mocks for initialize
        mock_global_camera_info = patch('camera.implementations.pi_camera.Picamera2.global_camera_info')
        mock_global_camera_info.return_value = [{'id': 'test_camera'}]
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (1440, 1080)}}
        mock_camera_instance.create_preview_configuration.return_value = mock_config

        with mock_global_camera_info:
            camera = PiCamera()
            # camera.camera is None initially

            camera.start()

            # Verify initialize was called (line 166)
            mock_picamera2_class.assert_called_once()
            assert camera.camera == mock_camera_instance

            # Verify camera operations were called
            mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 1080)})
            mock_camera_instance.configure.assert_called_once_with(mock_config)
            mock_camera_instance.start.assert_called_once()

            # Verify state changes
            assert camera.started == True
            assert camera.status == "Pi camera started"

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_stop(self, mock_picamera2_class):
        """Test stop."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (1440, 1080)}}
        mock_camera_instance.create_preview_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.started = True  # Simulate camera being started

        camera.stop()

        # Verify camera operations were called
        mock_camera_instance.stop.assert_called_once()

        # Verify state changes
        assert camera.started == False
        assert camera.status == "Pi camera stopped"

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_stop_when_recording(self, mock_picamera2_class):
        """Test stop when camera is recording (covers conditional branch)."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (1440, 1080)}}
        mock_camera_instance.create_preview_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.started = True
        camera.is_recording = True  # This should trigger the conditional branch

        # Mock stop_recording to avoid the recursive call
        with patch.object(camera, 'stop_recording') as mock_stop_recording:
            camera.stop()

            # Verify stop_recording was called due to is_recording being True
            mock_stop_recording.assert_called_once()

        # Verify state changes
        assert camera.started == False
        assert camera.status == "Pi camera stopped"

    @patch('camera.implementations.pi_camera.FileOutput')
    @patch('camera.implementations.pi_camera.H264Encoder')
    @patch('camera.implementations.pi_camera.Picamera2')
    def test_start_recording(self, mock_picamera2_class, mock_h264_encoder_class, mock_file_output_class):
        """Test start_recording."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_encoder_instance = mock_h264_encoder_class.return_value
        mock_output_instance = mock_file_output_class.return_value
        mock_video_config = {'main': {'size': (1920, 1080), 'format': 'RGB888'}}
        mock_camera_instance.create_video_configuration.return_value = mock_video_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        camera.start_recording(mock_encoder_instance, "test.mp4")

        # Verify configuration and camera operations
        mock_camera_instance.create_video_configuration.assert_called_once_with(main={'size': (1920, 1080), 'format': 'RGB888'})
        mock_camera_instance.configure.assert_called_once_with(mock_video_config)
        mock_camera_instance.start.assert_called_once()
        mock_camera_instance.start_recording.assert_called_once_with(mock_encoder_instance, mock_output_instance)

        # Verify state changes
        assert camera.is_recording == True
        assert camera.recording == True
        assert camera.status == "Recording to test.mp4"

    @patch('camera.implementations.pi_camera.FileOutput')
    @patch('camera.implementations.pi_camera.H264Encoder')
    @patch('camera.implementations.pi_camera.Picamera2')
    def test_start_recording_when_already_started(self, mock_picamera2_class, mock_h264_encoder_class, mock_file_output_class):
        """Test start_recording when camera is already started (covers conditional branch)."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_encoder_instance = mock_h264_encoder_class.return_value
        mock_output_instance = mock_file_output_class.return_value
        mock_video_config = {'main': {'size': (1920, 1080), 'format': 'RGB888'}}
        mock_camera_instance.create_video_configuration.return_value = mock_video_config

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.started = True  # This should trigger the conditional branch at line 196

        camera.start_recording(mock_encoder_instance, "test.mp4")

        # Verify that camera.stop() was called first due to started being True
        mock_camera_instance.stop.assert_called_once()

        # Then verify normal recording setup
        mock_camera_instance.create_video_configuration.assert_called_once_with(main={'size': (1920, 1080), 'format': 'RGB888'})
        mock_camera_instance.configure.assert_called_once_with(mock_video_config)
        # start should be called once (after reconfiguration for recording)
        mock_camera_instance.start.assert_called_once()

    def test_start_recording_no_camera(self):
        """Test start_recording when camera is not initialized."""
        camera = PiCamera()
        camera.camera = None

        mock_encoder = patch('camera.implementations.pi_camera.H264Encoder').start()

        with pytest.raises(Exception, match="Camera not initialized"):
            camera.start_recording(mock_encoder, "test.mp4")

    @patch('camera.implementations.pi_camera.FileOutput')
    @patch('camera.implementations.pi_camera.H264Encoder')
    @patch('camera.implementations.pi_camera.Picamera2')
    def test_stop_recording(self, mock_picamera2_class, mock_h264_encoder_class, mock_file_output_class):
        """Test stop_recording."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_encoder_instance = mock_h264_encoder_class.return_value
        mock_output_instance = mock_file_output_class.return_value
        mock_video_config = {'main': {'size': (1920, 1080), 'format': 'RGB888'}}
        mock_preview_config = {'main': {'size': (1440, 1080)}}
        mock_camera_instance.create_video_configuration.return_value = mock_video_config
        mock_camera_instance.create_preview_configuration.return_value = mock_preview_config

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.started = True  # Simulate camera being started
        camera.is_recording = True  # Simulate recording in progress

        camera.stop_recording()

        # Verify recording was stopped
        mock_camera_instance.stop_recording.assert_called_once()

        # Verify preview was restarted
        mock_camera_instance.stop.assert_called_once()
        mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 1080)})
        mock_camera_instance.configure.assert_called_once_with(mock_preview_config)
        assert mock_camera_instance.start.call_count == 1  # Should be called once to restart preview

        # Verify state changes
        assert camera.is_recording == False
        assert camera.recording == False
        assert camera.status == "Recording stopped"

    @patch('camera.implementations.pi_camera.cv2')
    @patch('camera.implementations.pi_camera.Picamera2')
    def test_capture_file(self, mock_picamera2_class, mock_cv2):
        """Test capture_file."""
        import numpy as np

        mock_camera_instance = mock_picamera2_class.return_value

        # Mock configurations
        mock_still_config = {'main': {'size': (4056, 3040)}}
        mock_preview_config = {'main': {'size': (1440, 1080)}}
        mock_camera_instance.create_still_configuration.return_value = mock_still_config
        mock_camera_instance.create_preview_configuration.return_value = mock_preview_config

        # Mock numpy array for captured image
        mock_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_camera_instance.capture_array.return_value = mock_array

        # Make cv2.cvtColor return the array (simulating the conversion)
        mock_cv2.cvtColor.return_value = mock_array

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.started = True  # Simulate camera being started

        # Mock the update_camera_settings method
        with patch.object(camera, 'update_camera_settings'):
            result = camera.capture_file("test.jpg")

            # Verify the method calls
            mock_camera_instance.stop.assert_called()  # Should stop current session
            mock_camera_instance.create_still_configuration.assert_called_once()
            mock_camera_instance.configure.assert_any_call(mock_still_config)
            mock_camera_instance.start.assert_called()
            mock_camera_instance.capture_array.assert_called_once()

            # Verify OpenCV operations
            mock_cv2.cvtColor.assert_called_once_with(mock_array, mock_cv2.COLOR_RGB2BGR)
            mock_cv2.imwrite.assert_called_once_with("test.jpg", mock_array)

            # Verify preview restart
            mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 1080)})
            mock_camera_instance.configure.assert_any_call(mock_preview_config)

            # Verify return value
            assert result == True

            # Verify capture_status is not modified (should remain "Ready")
            assert camera.capture_status == "Ready"

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_capture_image(self, mock_picamera2_class):
        """Test capture_image."""
        import numpy as np

        mock_camera_instance = mock_picamera2_class.return_value
        mock_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_camera_instance.capture_array.return_value = mock_array
        mock_camera_instance.capture_file.return_value = True

        camera = PiCamera()
        camera.camera = mock_camera_instance

        # Mock temporary file operations
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.unlink'):

            mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test.jpg'
            mock_open.return_value.__enter__.return_value.read.return_value = b'mock_image_data'

            result = camera.capture_image()

            # Verify the method calls
            mock_camera_instance.capture_file.assert_called_once_with('/tmp/test.jpg')

            # Verify return value
            assert result == (True, b'mock_image_data')

    @patch('camera.implementations.pi_camera.Picamera2')
    @patch('camera.implementations.pi_camera.cv2')
    def test_capture_file_exception_handling(self, mock_cv2, mock_picamera2_class):
        """Test capture_file exception handling (lines 302-304)."""
        import numpy as np

        mock_camera_instance = mock_picamera2_class.return_value
        mock_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_camera_instance.capture_array.return_value = mock_array

        # Mock configurations
        mock_still_config = {'main': {'size': (4056, 3040)}}
        mock_preview_config = {'main': {'size': (1440, 1080)}}
        mock_camera_instance.create_still_configuration.return_value = mock_still_config
        mock_camera_instance.create_preview_configuration.return_value = mock_preview_config

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.started = True

        # Make cv2.imwrite raise an exception
        mock_cv2.cvtColor.return_value = mock_array
        mock_cv2.imwrite.side_effect = Exception("File write failed")

        with patch('camera.implementations.pi_camera.logger') as mock_logger:
            with pytest.raises(Exception, match="File write failed"):
                camera.capture_file("test.jpg")

            # Verify error was logged
            mock_logger.error.assert_called_with("Failed to capture file: File write failed")

    @patch('camera.implementations.pi_camera.cv2')
    @patch('camera.implementations.pi_camera.Picamera2')
    def test_capture_file_with_name_parameter(self, mock_picamera2_class, mock_cv2):
        """Test capture_file with name parameter (line 263)."""
        import numpy as np

        mock_camera_instance = mock_picamera2_class.return_value

        # Mock configurations
        mock_still_config = {'main': {'size': (4056, 3040)}}
        mock_preview_config = {'main': {'size': (1440, 1080)}}
        mock_camera_instance.create_still_configuration.return_value = mock_still_config
        mock_camera_instance.create_preview_configuration.return_value = mock_preview_config

        # Mock numpy array for captured image
        mock_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_camera_instance.capture_array.return_value = mock_array

        # Make cv2.cvtColor return the array (simulating the conversion)
        mock_cv2.cvtColor.return_value = mock_array

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.started = True  # Simulate camera being started

        # Mock the update_camera_settings method
        with patch.object(camera, 'update_camera_settings'):
            result = camera.capture_file("test.jpg", name="custom_name")

            # Verify the method calls - capture_array is called without parameters (uses default "main")
            mock_camera_instance.capture_array.assert_called_once_with()

            # Verify return value
            assert result == True

    def test_capture_image_no_camera(self):
        """Test capture_image when camera is not initialized (line 314)."""
        camera = PiCamera()
        camera.camera = None

        with pytest.raises(Exception, match="Camera not initialized"):
            camera.capture_image()

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_capture_image_error_handling(self, mock_picamera2_class):
        """Test capture_image error handling (lines 338-343)."""
        mock_camera_instance = mock_picamera2_class.return_value

        camera = PiCamera()
        camera.camera = mock_camera_instance

        # Mock capture_file to raise an exception
        with patch.object(camera, 'camera') as mock_camera:
            mock_camera.capture_file.side_effect = Exception("Capture failed")

            with patch('camera.implementations.pi_camera.logger') as mock_logger:
                result = camera.capture_image()

                # Verify error handling
                assert result == (False, None)
                mock_logger.error.assert_called_with("Error capturing image: Capture failed")

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_cleanup(self, mock_picamera2_class):
        """Test cleanup."""
        mock_camera_instance = mock_picamera2_class.return_value
        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.cleanup()
        mock_camera_instance.close.assert_called_once()
        assert camera.camera is None
        assert camera.status == "Pi camera cleaned up"
    
    def test_slider_to_us(self):
        """Test slider_to_us utility method."""
        camera = PiCamera()
        result = camera.slider_to_us(500)
        assert isinstance(result, int)
        assert result > 0

    def test_us_to_shutter_string(self):
        """Test us_to_shutter_string utility method."""
        camera = PiCamera()

        # Test short exposure
        result = camera.us_to_shutter_string(1000)  # 1ms
        assert "1/" in result

        # Test long exposure
        result = camera.us_to_shutter_string(1000000)  # 1 second
        assert "s" in result

    def test_gain_to_iso_conversion(self):
        """Test gain to ISO conversion."""
        camera = PiCamera()
        assert camera.gain_to_iso(1.0) == 100
        assert camera.gain_to_iso(2.0) == 200

    def test_iso_to_gain_conversion(self):
        """Test ISO to gain conversion."""
        camera = PiCamera()
        assert camera.iso_to_gain(100) == 1.0
        assert camera.iso_to_gain(200) == 2.0

    def test_exposure_time_getters(self):
        """Test exposure time getter methods."""
        camera = PiCamera()
        camera.exposure_us = 1000000  # 1 second

        assert camera.get_exposure_us() == 1000000
        assert camera.get_exposure_seconds() == 1.0

    def test_set_exposure_us(self):
        """Test setting exposure time with validation."""
        camera = PiCamera()
        camera.camera = patch('camera.implementations.pi_camera.Picamera2').start()

        # Test valid exposure
        camera.set_exposure_us(500000)
        assert camera.exposure_us == 500000
        camera.camera.set_controls.assert_called_with({"ExposureTime": 500000})

        # Reset mock for next test
        camera.camera.reset_mock()

        # Test clamping minimum
        camera.set_exposure_us(50)  # Below minimum
        assert camera.exposure_us == 100  # Should be clamped
        camera.camera.set_controls.assert_called_with({"ExposureTime": 100})

        # Reset mock for next test
        camera.camera.reset_mock()

        # Test clamping maximum
        camera.set_exposure_us(400000000)  # Above maximum
        assert camera.exposure_us == 300000000  # Should be clamped

    def test_set_exposure_us_no_camera(self):
        """Test set_exposure_us when camera is not initialized."""
        camera = PiCamera()
        camera.camera = None

        with pytest.raises(Exception, match="Camera not initialized"):
            camera.set_exposure_us(500000)

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_set_exposure_us_error_handling(self, mock_picamera2_class):
        """Test set_exposure_us error handling (lines 397-398)."""
        mock_camera_instance = mock_picamera2_class.return_value

        camera = PiCamera()
        camera.camera = mock_camera_instance

        # Mock set_controls to raise an exception
        mock_camera_instance.set_controls.side_effect = Exception("Set controls failed")

        with patch('camera.implementations.pi_camera.logger') as mock_logger:
            camera.set_exposure_us(500000)

            # Verify warning was logged
            mock_logger.warning.assert_called_with("Could not set exposure time: Set controls failed")

            # Verify exposure_us was still set
            assert camera.exposure_us == 500000

    def test_update_camera_settings(self):
        """Test updating camera settings."""
        camera = PiCamera()
        camera.camera = patch('camera.implementations.pi_camera.Picamera2').start()

        # Set test values
        camera.exposure_us = 200000
        camera.gain = 2.0

        camera.update_camera_settings()

        # Verify camera controls were set
        camera.camera.set_controls.assert_called_once()
        controls = camera.camera.set_controls.call_args[0][0]
        assert 'ExposureTime' in controls
        assert 'AnalogueGain' in controls

    def test_update_camera_settings_no_camera(self):
        """Test update_camera_settings when no camera is initialized."""
        camera = PiCamera()
        camera.camera = None

        # Should raise exception when camera is not initialized
        with pytest.raises(Exception, match="Camera not initialized"):
            camera.update_camera_settings()

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_update_camera_settings_error_handling(self, mock_picamera2_class):
        """Test update_camera_settings error handling (lines 433-434)."""
        mock_camera_instance = mock_picamera2_class.return_value

        camera = PiCamera()
        camera.camera = mock_camera_instance

        # Mock set_controls to raise an exception
        mock_camera_instance.set_controls.side_effect = Exception("Set controls failed")

        with patch('camera.implementations.pi_camera.logger') as mock_logger:
            camera.update_camera_settings()

            # Verify warning was logged
            mock_logger.warning.assert_called_with("Could not update camera settings: Set controls failed")

    def test_night_vision_mode(self):
        """Test night vision mode settings."""
        camera = PiCamera()
        camera.camera = patch('camera.implementations.pi_camera.Picamera2').start()

        # Enable night vision
        camera.night_vision_mode = True
        camera.night_vision_intensity = 50.0

        camera.update_camera_settings()

        # Verify digital gain is applied
        assert camera.use_digital_gain == True
        assert camera.digital_gain == 50.0

    def test_exposure_mode_persistence(self):
        """Test that exposure mode is preserved across operations."""
        camera = PiCamera()
        camera.exposure_mode = "auto"

        # Mock camera for save/restore operations
        mock_camera = patch('camera.implementations.pi_camera.Picamera2').start()
        camera.camera = mock_camera
        mock_camera.camera_controls = {'ExposureTime': 100000}

        # Save original state
        camera.save_original_state()
        assert camera._original_hardware_state['exposure_mode'] == 'auto'

        # Change exposure mode
        camera.exposure_mode = "manual"

        # Restore original state
        camera.restore_original_state()
        assert camera.exposure_mode == 'auto'

    def test_capture_array(self):
        """Test capture_array method."""
        import numpy as np

        mock_camera = patch('camera.implementations.pi_camera.Picamera2').start()
        mock_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_camera.capture_array.return_value = mock_array

        camera = PiCamera()
        camera.camera = mock_camera

        result = camera.capture_array()
        assert result is mock_array
        mock_camera.capture_array.assert_called_once()

    def test_capture_array_no_camera(self):
        """Test capture_array when camera is not initialized."""
        camera = PiCamera()
        camera.camera = None

        with pytest.raises(Exception, match="Camera not initialized"):
            camera.capture_array()

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_capture_array_exception_handling(self, mock_picamera2_class):
        """Test capture_array exception handling (lines 255-257)."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_camera_instance.capture_array.side_effect = Exception("Capture failed")

        camera = PiCamera()
        camera.camera = mock_camera_instance

        with patch('camera.implementations.pi_camera.logger') as mock_logger:
            with pytest.raises(Exception, match="Capture failed"):
                camera.capture_array()

            # Verify error was logged
            mock_logger.error.assert_called_with("Failed to capture array: Capture failed")

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_capture_array_with_frame_skipping(self, mock_picamera2_class):
        """Test capture_array with frame skipping (line 251)."""
        import numpy as np

        mock_camera_instance = mock_picamera2_class.return_value
        mock_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_camera_instance.capture_array.return_value = mock_array

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.skip_frames = 3  # Set skip_frames to test the loop

        result = camera.capture_array()

        # Verify the method was called
        assert result is mock_array
        mock_camera_instance.capture_array.assert_called_once()

        # Note: The frame skipping loop at line 251 is executed but doesn't actually
        # do anything (just pass statements), so we can't easily verify the loop
        # execution without more complex mocking

    def test_get_frame(self):
        """Test get_frame method."""
        import numpy as np

        mock_camera = patch('camera.implementations.pi_camera.Picamera2').start()
        mock_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_camera.capture_array.return_value = mock_array

        camera = PiCamera()
        camera.camera = mock_camera

        # Mock OpenCV operations
        with patch('camera.implementations.pi_camera.cv2') as mock_cv2:
            mock_cv2.cvtColor.return_value = mock_array

            # Create a proper mock for the encoded image array
            from unittest.mock import MagicMock
            mock_encoded = MagicMock()
            mock_encoded.tobytes.return_value = b'fake_jpeg_data'
            mock_cv2.imencode.return_value = (True, mock_encoded)

            result = camera.get_frame()
            assert result == b'fake_jpeg_data'

    @patch('camera.implementations.pi_camera.cv2')
    @patch('camera.implementations.pi_camera.Picamera2')
    def test_get_frame_with_digital_gain(self, mock_picamera2_class, mock_cv2):
        """Test get_frame with digital gain application (line 444)."""
        import numpy as np

        mock_camera_instance = mock_picamera2_class.return_value
        mock_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_camera_instance.capture_array.return_value = mock_array

        camera = PiCamera()
        camera.camera = mock_camera_instance

        # Enable digital gain
        camera.use_digital_gain = True
        camera.digital_gain = 2.0

        # Mock OpenCV operations
        mock_cv2.cvtColor.return_value = mock_array

        # Create a proper mock for the encoded image array
        from unittest.mock import MagicMock
        mock_encoded = MagicMock()
        mock_encoded.tobytes.return_value = b'fake_jpeg_data'
        mock_cv2.imencode.return_value = (True, mock_encoded)

        # Mock np.clip to verify digital gain is applied
        with patch('camera.implementations.pi_camera.np') as mock_np:
            # Create a mock array that has astype method
            mock_clipped_array = MagicMock()
            mock_clipped_array.astype.return_value = mock_array
            mock_np.clip.return_value = mock_clipped_array

            result = camera.get_frame()

            # Verify digital gain was applied (line 444)
            mock_np.clip.assert_called_once()
            call_args = mock_np.clip.call_args[0]
            # The first argument should be the result of array * digital_gain
            assert call_args[1] == 0  # Min value
            assert call_args[2] == 255  # Max value

            assert result == b'fake_jpeg_data'

    def test_capture_still(self):
        """Test capture_still method."""
        camera = PiCamera()
        camera.capture_dir = "/tmp"

        with patch.object(camera, 'capture_file', return_value=True) as mock_capture:
            result = camera.capture_still()
            assert result == True
            assert "Image saved" in camera.capture_status

    def test_capture_still_error_handling(self):
        """Test capture_still error handling (lines 470-473)."""
        camera = PiCamera()
        camera.capture_dir = "/tmp"

        # Mock capture_file to raise an exception
        with patch.object(camera, 'capture_file', side_effect=Exception("Capture failed")) as mock_capture:
            with patch('camera.implementations.pi_camera.logger') as mock_logger:
                result = camera.capture_still()

                # Verify error handling
                assert result == False
                assert "Capture failed" in camera.capture_status
                mock_logger.error.assert_called_with("Error capturing still: Capture failed")

    def test_start_video(self):
        """Test start_video method."""
        camera = PiCamera()
        camera.capture_dir = "/tmp"

        with patch.object(camera, 'start_recording') as mock_start_recording:
            result = camera.start_video()
            assert result == True
            mock_start_recording.assert_called_once()

    def test_start_video_error_handling(self):
        """Test start_video error handling (lines 482-484)."""
        camera = PiCamera()
        camera.capture_dir = "/tmp"

        # Mock start_recording to raise an exception
        with patch.object(camera, 'start_recording', side_effect=Exception("Recording failed")) as mock_start_recording:
            with patch('camera.implementations.pi_camera.logger') as mock_logger:
                result = camera.start_video()

                # Verify error handling
                assert result == False
                mock_logger.error.assert_called_with("Error starting video: Recording failed")

    def test_stop_video(self):
        """Test stop_video method."""
        camera = PiCamera()

        with patch.object(camera, 'stop_recording') as mock_stop_recording:
            result = camera.stop_video()
            assert result == True
            mock_stop_recording.assert_called_once()

    def test_stop_video_error_handling(self):
        """Test stop_video error handling (lines 491-493)."""
        camera = PiCamera()

        # Mock stop_recording to raise an exception
        with patch.object(camera, 'stop_recording', side_effect=Exception("Stop recording failed")) as mock_stop_recording:
            with patch('camera.implementations.pi_camera.logger') as mock_logger:
                result = camera.stop_video()

                # Verify error handling
                assert result == False
                mock_logger.error.assert_called_with("Error stopping video: Stop recording failed")

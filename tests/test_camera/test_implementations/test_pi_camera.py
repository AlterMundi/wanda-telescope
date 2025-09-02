import pytest
import logging
from unittest.mock import patch
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

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_create_preview_configuration_default(self, mock_picamera2_class):
        """Test create_preview_configuration with default parameters."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'size': (1440, 810)}
        mock_camera_instance.create_preview_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        result = camera.create_preview_configuration()

        mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 810)})
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

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_set_controls(self, mock_picamera2_class):
        """Test set_controls."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'ExposureTime': 100000, 'AnalogueGain': 1.0}

        camera = PiCamera()
        camera.camera = mock_camera_instance
        camera.set_controls(mock_config)
        mock_camera_instance.set_controls.assert_called_once_with(mock_config)

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_start(self, mock_picamera2_class):
        """Test start."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (1440, 810)}}
        mock_camera_instance.create_preview_configuration.return_value = mock_config

        camera = PiCamera()
        camera.camera = mock_camera_instance

        camera.start()

        # Verify camera operations were called
        mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 810)})
        mock_camera_instance.configure.assert_called_once_with(mock_config)
        mock_camera_instance.start.assert_called_once()

        # Verify state changes
        assert camera.started == True
        assert camera.status == "Pi camera started"

    @patch('camera.implementations.pi_camera.Picamera2')
    def test_stop(self, mock_picamera2_class):
        """Test stop."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_config = {'main': {'size': (1440, 810)}}
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
    def test_stop_recording(self, mock_picamera2_class, mock_h264_encoder_class, mock_file_output_class):
        """Test stop_recording."""
        mock_camera_instance = mock_picamera2_class.return_value
        mock_encoder_instance = mock_h264_encoder_class.return_value
        mock_output_instance = mock_file_output_class.return_value
        mock_video_config = {'main': {'size': (1920, 1080), 'format': 'RGB888'}}
        mock_preview_config = {'main': {'size': (1440, 810)}}
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
        mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 810)})
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
        mock_preview_config = {'main': {'size': (1440, 810)}}
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
            mock_camera_instance.create_preview_configuration.assert_called_once_with(main={'size': (1440, 810)})
            mock_camera_instance.configure.assert_any_call(mock_preview_config)

            # Verify return value
            assert result == True

            # Verify capture_status is not modified (should remain "Ready")
            assert camera.capture_status == "Ready"
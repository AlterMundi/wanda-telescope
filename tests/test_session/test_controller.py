"""
Comprehensive tests for SessionController class.
"""
import pytest
import os
import json
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, mock_open
from session.controller import SessionController


class TestSessionController:
    """Test suite for SessionController class."""

    @pytest.fixture
    def mock_camera(self):
        """Mock camera object for testing."""
        camera = Mock()
        camera.capture_file = Mock(return_value=True)
        camera.capture_still = Mock(return_value=True)
        return camera

    @pytest.fixture
    def mock_mount(self):
        """Mock mount object for testing."""
        mount = Mock()
        mount.tracking = False
        mount.start_tracking = Mock()
        mount.stop_tracking = Mock()
        return mount

    @pytest.fixture
    def mock_session_controller(self, mock_camera, mock_mount):
        """Mock SessionController instance for testing."""
        with patch('session.controller.logger'):
            controller = SessionController(mock_camera, mock_mount)
            yield controller

    @pytest.fixture
    def mock_os_makedirs(self):
        """Mock os.makedirs for testing."""
        with patch('os.makedirs') as mock_makedirs:
            yield mock_makedirs

    @pytest.fixture
    def mock_datetime(self):
        """Mock datetime for consistent testing."""
        with patch('session.controller.datetime') as mock_dt:
            # Set a fixed datetime for testing
            fixed_time = datetime(2023, 12, 1, 12, 0, 0)
            mock_dt.now.return_value = fixed_time
            mock_dt.fromisoformat = datetime.fromisoformat
            yield mock_dt

    def test_init(self, mock_camera, mock_mount):
        """Test SessionController initialization with default values."""
        with patch('session.controller.logger'):
            controller = SessionController(mock_camera, mock_mount)

        # Assert basic attributes
        assert controller.camera == mock_camera
        assert controller.mount == mock_mount
        assert controller.base_capture_dir == "captures"
        assert controller.current_session is None
        assert controller.session_thread is None
        assert controller.session_running is False
        assert hasattr(controller._session_lock, 'acquire')
        assert hasattr(controller._session_lock, 'release')

        # Assert session config defaults
        expected_config = {
            'name': '',
            'total_images': 0,
            'use_current_settings': True,
            'enable_tracking': False,
            'total_time_hours': None,
            'start_time': None,
            'end_time': None,
            'images_captured': 0,
            'session_dir': '',
            'status': 'idle',
            'mount_tracking_stopped': False
        }
        assert controller.session_config == expected_config

    def test_init_custom_capture_dir(self, mock_camera, mock_mount):
        """Test SessionController initialization with custom capture directory."""
        with patch('session.controller.logger'):
            controller = SessionController(mock_camera, mock_mount, base_capture_dir="/custom/path")

        assert controller.base_capture_dir == "/custom/path"

    @patch('session.controller.logger')
    def test_init_logs_initialization(self, mock_logger, mock_camera, mock_mount):
        """Test that SessionController logs its initialization."""
        SessionController(mock_camera, mock_mount)

        mock_logger.info.assert_called_once_with("Session controller initialized")

    def test_start_session_success(self, mock_session_controller, mock_os_makedirs, mock_datetime):
        """Test successful session start."""
        controller = mock_session_controller

        # Act
        result = controller.start_session("test_session", 10, use_current_settings=True, enable_tracking=False)

        # Assert
        assert result is True
        assert controller.session_running is True
        assert controller.session_thread is not None
        assert controller.session_thread.is_alive()
        assert controller.session_config['name'] == "test_session"
        assert controller.session_config['total_images'] == 10
        assert controller.session_config['status'] == 'running'
        assert controller.session_config['session_dir'] == "captures/test_session"
        mock_os_makedirs.assert_called_once_with("captures/test_session", exist_ok=True)

    def test_start_session_with_time_based(self, mock_session_controller, mock_os_makedirs, mock_datetime):
        """Test successful session start with time-based capture."""
        controller = mock_session_controller

        # Act
        result = controller.start_session("time_session", 10, total_time_hours=4.0)

        # Assert
        assert result is True
        assert controller.session_running is True
        assert controller.session_thread is not None
        assert controller.session_config['name'] == "time_session"
        assert controller.session_config['total_images'] == 10
        assert controller.session_config['total_time_hours'] == 4.0
        assert controller.session_config['status'] == 'running'
        mock_os_makedirs.assert_called_once_with("captures/time_session", exist_ok=True)

    def test_start_session_with_tracking(self, mock_session_controller, mock_mount):
        """Test session start with mount tracking enabled."""
        controller = mock_session_controller
        mock_mount.tracking = False

        with patch('os.makedirs'):
            with patch('session.controller.datetime'):
                # Act
                controller.start_session("test_session", 5, enable_tracking=True)

                # Assert
                mock_mount.start_tracking.assert_called_once()
                assert controller.session_config['enable_tracking'] is True

    def test_start_session_already_running(self, mock_session_controller):
        """Test starting session when one is already running."""
        controller = mock_session_controller
        controller.session_running = True

        # Act & Assert
        with pytest.raises(Exception, match="A session is already running"):
            controller.start_session("new_session", 5)

    def test_start_session_empty_name(self, mock_session_controller):
        """Test starting session with empty name."""
        controller = mock_session_controller

        # Act & Assert
        with pytest.raises(Exception, match="Session name cannot be empty"):
            controller.start_session("", 5)

    def test_start_session_whitespace_name(self, mock_session_controller):
        """Test starting session with whitespace-only name."""
        controller = mock_session_controller

        # Act & Assert
        with pytest.raises(Exception, match="Session name cannot be empty"):
            controller.start_session("   ", 5)

    def test_start_session_zero_images(self, mock_session_controller):
        """Test starting session with zero total images."""
        controller = mock_session_controller

        # Act & Assert
        with pytest.raises(Exception, match="Total images must be greater than 0"):
            controller.start_session("test", 0)

    def test_start_session_negative_images(self, mock_session_controller):
        """Test starting session with negative total images."""
        controller = mock_session_controller

        # Act & Assert
        with pytest.raises(Exception, match="Total images must be greater than 0"):
            controller.start_session("test", -1)

    def test_start_session_zero_time_hours(self, mock_session_controller):
        """Test starting session with zero total time hours."""
        controller = mock_session_controller

        # Act & Assert
        with pytest.raises(Exception, match="Total time hours must be greater than 0"):
            controller.start_session("test", 10, total_time_hours=0)

    def test_start_session_negative_time_hours(self, mock_session_controller):
        """Test starting session with negative total time hours."""
        controller = mock_session_controller

        # Act & Assert
        with pytest.raises(Exception, match="Total time hours must be greater than 0"):
            controller.start_session("test", 10, total_time_hours=-1)

    def test_start_session_directory_creation_failure(self, mock_session_controller):
        """Test session start when directory creation fails."""
        controller = mock_session_controller

        with patch('os.makedirs', side_effect=OSError("Permission denied")):
            # Act & Assert
            with pytest.raises(Exception, match="Failed to create session directory"):
                controller.start_session("test", 5)

    def test_stop_session_success(self, mock_session_controller):
        """Test successful session stop."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config['status'] = 'running'
        controller.session_config['name'] = 'test_session'
        controller.session_config['images_captured'] = 5

        with patch('session.controller.datetime'):
            # Act
            result = controller.stop_session()

            # Assert
            assert result is True
            assert controller.session_running is False
            assert controller.session_config['status'] == 'completed'
            assert controller.session_config['end_time'] is not None

    def test_stop_session_already_completed(self, mock_session_controller):
        """Test stopping session that is already completed."""
        controller = mock_session_controller
        controller.session_running = False
        controller.session_config['status'] = 'completed'

        with patch('session.controller.logger') as mock_logger:
            # Act
            result = controller.stop_session()

            # Assert
            assert result is True
            mock_logger.info.assert_called_with("Session already completed")

    def test_stop_session_with_tracking(self, mock_session_controller, mock_mount):
        """Test stopping session with mount tracking cleanup."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config.update({
            'enable_tracking': True,
            'status': 'running',
            'mount_tracking_stopped': False
        })
        mock_mount.tracking = True

        with patch('session.controller.datetime'):
            # Act
            controller.stop_session()

            # Assert
            mock_mount.stop_tracking.assert_called_once()
            assert controller.session_config['mount_tracking_stopped'] is True

    def test_get_session_status_idle(self, mock_session_controller):
        """Test getting session status when idle."""
        controller = mock_session_controller

        # Act
        status = controller.get_session_status()

        # Assert
        expected_status = {
            'running': False,
            'status': 'idle',
            'name': '',
            'total_images': 0,
            'images_captured': 0,
            'progress': 0,
            'elapsed_time': 0,
            'session_dir': '',
            'total_time_hours': None,
            'formatted_time': None,
            'estimated_completion': None
        }
        assert status == expected_status

    def test_get_session_status_running(self, mock_session_controller):
        """Test getting session status when running."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config.update({
            'name': 'test_session',
            'total_images': 10,
            'images_captured': 3,
            'start_time': '2023-12-01T11:30:00',
            'status': 'running',
            'session_dir': 'captures/test_session'
        })

        with patch('session.controller.datetime') as mock_dt:
            mock_dt.fromisoformat.return_value = datetime(2023, 12, 1, 11, 30, 0)
            mock_dt.now.return_value = datetime(2023, 12, 1, 12, 0, 0)

            # Act
            status = controller.get_session_status()

            # Assert
            assert status['running'] is True
            assert status['status'] == 'running'
            assert status['name'] == 'test_session'
            assert status['total_images'] == 10
            assert status['images_captured'] == 3
            assert status['progress'] == 30.0  # 3/10 * 100
            assert status['elapsed_time'] == 1800  # 30 minutes in seconds
            assert status['session_dir'] == 'captures/test_session'

    @patch('threading.Thread')
    def test_session_worker_thread_creation(self, mock_thread_class, mock_session_controller):
        """Test that session worker thread is created properly."""
        controller = mock_session_controller
        mock_thread_instance = Mock()
        mock_thread_class.return_value = mock_thread_instance

        with patch('os.makedirs'):
            with patch('session.controller.datetime'):
                # Act
                controller.start_session("test", 1)

                # Assert
                mock_thread_class.assert_called_once_with(target=controller._session_worker, daemon=True)
                mock_thread_instance.start.assert_called_once()

    @patch('time.sleep')
    def test_session_worker_capture_loop(self, mock_sleep, mock_session_controller):
        """Test session worker capture loop."""
        controller = mock_session_controller

        # Setup - Initialize session config properly
        controller.session_config.update({
            'total_images': 2,
            'images_captured': 0,
            'status': 'running'
        })

        # Mock capture to succeed
        with patch.object(controller, '_capture_session_image', return_value=True):
            with patch.object(controller, '_save_session_metadata'):
                # Act - simulate worker running briefly
                controller.session_running = True
                controller._session_worker()

                # Assert
                # Should have attempted to capture 2 images
                assert controller.session_config['images_captured'] == 2
                assert controller.session_config['status'] == 'completed'

    @patch('time.sleep')
    def test_session_worker_stops_when_completed(self, mock_sleep, mock_session_controller):
        """Test session worker stops when all images captured."""
        controller = mock_session_controller

        # Setup
        controller.session_config['total_images'] = 1
        controller.session_config['images_captured'] = 1

        # Act
        controller._session_worker()

        # Assert
        assert controller.session_running is False

    def test_session_worker_handles_capture_failure(self, mock_session_controller):
        """Test session worker handles capture failure."""
        controller = mock_session_controller

        # Setup - Initialize session config properly
        controller.session_config.update({
            'total_images': 1,
            'images_captured': 0,
            'status': 'running'
        })

        # Create a custom exception to ensure it's caught
        class TestCaptureException(Exception):
            pass

        # Mock capture to always fail with our custom exception
        with patch.object(controller, '_capture_session_image', side_effect=TestCaptureException("Capture failed")):
            with patch.object(controller, '_save_session_metadata'):
                # Act
                controller._session_worker()

                # Assert
                assert controller.session_running is False  # Session should stop
                # The key assertion is that the session stopped running after an exception
                assert not controller.session_running

    def test_capture_session_image_with_capture_file(self, mock_session_controller):
        """Test capturing image with camera that has capture_file method."""
        controller = mock_session_controller
        controller.session_config['images_captured'] = 0
        controller.session_config['session_dir'] = 'captures/test'

        # Act
        result = controller._capture_session_image()

        # Assert
        assert result is True
        controller.camera.capture_file.assert_called_once_with('captures/test/image_0001.jpg')

    def test_capture_session_image_with_capture_still(self, mock_session_controller):
        """Test capturing image with camera that has capture_still method."""
        controller = mock_session_controller
        controller.session_config['images_captured'] = 0
        controller.session_config['session_dir'] = 'captures/test'

        # Remove capture_file method to force capture_still path
        del controller.camera.capture_file

        with patch('glob.glob', return_value=['captures/test/capture_001.jpg']):
            with patch('os.path.getctime', return_value=1234567890.0):
                with patch('os.rename'):
                    # Act
                    result = controller._capture_session_image()

                    # Assert
                    assert result is True
                    controller.camera.capture_still.assert_called_once()

    def test_capture_session_image_capture_still_failure(self, mock_session_controller):
        """Test capture image when capture_still fails."""
        controller = mock_session_controller
        controller.camera.capture_still.return_value = False
        del controller.camera.capture_file

        # Act & Assert
        with pytest.raises(Exception, match="Camera capture failed"):
            controller._capture_session_image()

    def test_capture_session_image_no_supported_method(self, mock_session_controller):
        """Test capture image when camera has no supported capture method."""
        controller = mock_session_controller
        del controller.camera.capture_file
        del controller.camera.capture_still

        with patch('session.controller.logger') as mock_logger:
            # Act
            result = controller._capture_session_image()

            # Assert
            assert result is False
            mock_logger.error.assert_called_once_with("Camera does not support file capture")

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_session_metadata(self, mock_json_dump, mock_file, mock_session_controller):
        """Test saving session metadata to file."""
        controller = mock_session_controller
        controller.session_config['session_dir'] = 'captures/test'

        # Act
        controller._save_session_metadata()

        # Assert
        mock_file.assert_called_once_with('captures/test/session_metadata.json', 'w')
        mock_json_dump.assert_called_once()

    @patch('session.controller.logger')
    def test_save_session_metadata_failure(self, mock_logger, mock_session_controller):
        """Test handling failure when saving session metadata."""
        controller = mock_session_controller

        with patch('builtins.open', side_effect=OSError("Write failed")):
            # Act
            controller._save_session_metadata()

            # Assert
            mock_logger.error.assert_called_once_with("Failed to save session metadata: Write failed")

    def test_cleanup_when_not_running(self, mock_session_controller):
        """Test cleanup when session is not running."""
        controller = mock_session_controller
        controller.session_running = False

        with patch('session.controller.safe_log') as mock_safe_log:
            # Act
            controller.cleanup()

            # Assert
            mock_safe_log.assert_called_with('info', "Session controller cleaned up")

    def test_cleanup_when_running(self, mock_session_controller):
        """Test cleanup when session is running."""
        controller = mock_session_controller
        controller.session_running = True

        with patch.object(controller, 'stop_session', return_value=True) as mock_stop:
            with patch('session.controller.safe_log') as mock_safe_log:
                # Act
                controller.cleanup()

                # Assert
                mock_stop.assert_called_once()
                mock_safe_log.assert_called_with('info', "Session controller cleaned up")

    def test_thread_safety_lock_exists(self, mock_session_controller):
        """Test that SessionController has proper thread safety mechanisms."""
        controller = mock_session_controller

        # Assert that the session lock exists and is a threading lock
        assert hasattr(controller, '_session_lock')
        assert hasattr(controller._session_lock, 'acquire')
        assert hasattr(controller._session_lock, 'release')

        # Test that the lock can be acquired and released
        assert controller._session_lock.acquire(blocking=False)
        controller._session_lock.release()

    def test_critical_methods_use_thread_safety(self, mock_session_controller):
        """Test that critical methods use thread safety mechanisms."""
        controller = mock_session_controller

        # Test that methods can be called concurrently without issues
        import threading
        import time

        results = []
        errors = []

        def call_get_status():
            try:
                status = controller.get_session_status()
                results.append("status_success")
            except Exception as e:
                errors.append(f"status_error: {e}")

        # Only test get_status concurrently since start_session can only run once
        threads = []
        for _ in range(10):  # Test more get_status calls
            threads.append(threading.Thread(target=call_get_status))

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=1.0)

        # Assert no errors occurred (thread safety working)
        assert len(errors) == 0, f"Thread safety issues: {errors}"
        assert len(results) == 10, f"Expected 10 successful calls, got {len(results)}"

    def test_session_worker_mount_tracking_cleanup(self, mock_session_controller, mock_mount):
        """Test mount tracking cleanup in session worker finally block."""
        controller = mock_session_controller
        controller.session_config.update({
            'enable_tracking': True,
            'status': 'running',
            'mount_tracking_stopped': False
        })
        mock_mount.tracking = True

        # Act
        controller._session_worker()

        # Assert
        assert controller.session_config['status'] == 'completed'
        mock_mount.stop_tracking.assert_called_once()
        assert controller.session_config['mount_tracking_stopped'] is True

    def test_start_session_mount_tracking_failure(self, mock_session_controller, mock_mount):
        """Test start_session when mount tracking fails to start."""
        controller = mock_session_controller
        mock_mount.tracking = False
        mock_mount.start_tracking.side_effect = Exception("Mount tracking failed")

        with patch('os.makedirs'):
            with patch('session.controller.datetime'):
                with patch('session.controller.logger') as mock_logger:
                    # Act
                    result = controller.start_session("test_session", 5, enable_tracking=True)

                    # Assert
                    assert result is True  # Session should still start despite mount failure
                    assert controller.session_running is True
                    mock_mount.start_tracking.assert_called_once()
                    mock_logger.warning.assert_called_once_with("Failed to start mount tracking: Mount tracking failed")

    def test_stop_session_mount_tracking_failure(self, mock_session_controller, mock_mount):
        """Test stop_session when mount tracking fails to stop."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config.update({
            'enable_tracking': True,
            'status': 'running',
            'mount_tracking_stopped': False,
            'name': 'test_session',
            'images_captured': 3
        })
        mock_mount.tracking = True
        mock_mount.stop_tracking.side_effect = Exception("Mount tracking stop failed")

        with patch('session.controller.datetime'):
            with patch('session.controller.logger') as mock_logger:
                # Act
                result = controller.stop_session()

                # Assert
                assert result is True  # Session should still stop despite mount failure
                assert controller.session_running is False
                mock_mount.stop_tracking.assert_called_once()
                mock_logger.warning.assert_called_once_with("Failed to stop mount tracking: Mount tracking stop failed")

    def test_stop_session_thread_join(self, mock_session_controller):
        """Test stop_session thread join functionality."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config['status'] = 'running'
        controller.session_config['name'] = 'test_session'
        controller.session_config['images_captured'] = 5

        # Create a mock thread that's alive
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        mock_thread.join = Mock()
        controller.session_thread = mock_thread

        with patch('session.controller.datetime'):
            # Act
            result = controller.stop_session()

            # Assert
            assert result is True
            mock_thread.join.assert_called_once_with(timeout=5.0)

    def test_session_worker_mount_cleanup_failure(self, mock_session_controller, mock_mount):
        """Test mount cleanup failure in session worker finally block."""
        controller = mock_session_controller
        controller.session_config.update({
            'enable_tracking': True,
            'status': 'running',
            'mount_tracking_stopped': False
        })
        mock_mount.tracking = True
        mock_mount.stop_tracking.side_effect = Exception("Mount cleanup failed")

        with patch('session.controller.logger') as mock_logger:
            # Act
            controller._session_worker()

            # Assert
            assert controller.session_config['status'] == 'completed'
            mock_mount.stop_tracking.assert_called_once()
            mock_logger.warning.assert_called_once_with("Failed to stop mount tracking: Mount cleanup failed")

    def test_capture_session_image_capture_still_no_files(self, mock_session_controller):
        """Test capture_session_image when capture_still produces no files."""
        controller = mock_session_controller
        controller.session_config['images_captured'] = 0
        controller.session_config['session_dir'] = 'captures/test'

        # Remove capture_file method to force capture_still path
        del controller.camera.capture_file

        with patch('glob.glob', return_value=[]):  # No files found
            # Act
            result = controller._capture_session_image()

            # Assert
            assert result is False
            controller.camera.capture_still.assert_called_once()

    def test_session_worker_finally_error_logging(self, mock_session_controller):
        """Test that session worker finally block logs correctly when status is error."""
        controller = mock_session_controller

        # Setup session config with error status
        controller.session_config.update({
            'total_images': 1,
            'images_captured': 0,
            'status': 'error'  # Set status to error
        })

        with patch('session.controller.logger') as mock_logger:
            # Act
            controller._session_worker()

            # Assert
            mock_logger.info.assert_any_call("Session status is error, not changing to completed")

    def test_session_worker_exception_handling(self, mock_session_controller):
        """Test session worker exception handling in the main loop."""
        controller = mock_session_controller

        # Setup session config
        controller.session_config.update({
            'total_images': 2,
            'images_captured': 0,
            'status': 'running'
        })
        controller.session_running = True  # Start the session

        # Mock capture to raise an exception
        with patch.object(controller, '_capture_session_image', side_effect=Exception("Test capture error")):
            with patch.object(controller, '_save_session_metadata'):
                with patch('session.controller.logger') as mock_logger:
                    # Act
                    controller._session_worker()

                    # Assert
                    assert controller.session_running is False
                    # The status should be 'error' after exception handling
                    assert controller.session_config['status'] == 'error'
                    mock_logger.error.assert_any_call("Session worker error: Test capture error")
                    mock_logger.error.assert_any_call("Session status set to error in except block: error")
                    # Check that the finally block didn't override the error status
                    mock_logger.info.assert_any_call("Session status is error, not changing to completed")

    def test_calculate_capture_delay_no_time_based(self, mock_session_controller):
        """Test calculate_capture_delay for non-time-based sessions."""
        controller = mock_session_controller
        controller.session_config['total_time_hours'] = None

        # Act
        delay = controller._calculate_capture_delay()

        # Assert
        assert delay == 0.5

    def test_calculate_capture_delay_time_based_normal(self, mock_session_controller):
        """Test calculate_capture_delay for time-based sessions with normal progress."""
        controller = mock_session_controller
        controller.session_config.update({
            'total_time_hours': 2.0,  # 2 hours = 7200 seconds
            'total_images': 10,
            'images_captured': 3,  # 3 captured, so 7 remaining including current
            'start_time': '2023-12-01T12:00:00'
        })

        with patch('session.controller.datetime') as mock_dt:
            # Mock current time as 30 minutes after start
            mock_dt.fromisoformat.return_value = datetime(2023, 12, 1, 12, 0, 0)
            mock_dt.now.return_value = datetime(2023, 12, 1, 12, 30, 0)

            # Act
            delay = controller._calculate_capture_delay()

            # Assert - should calculate delay for remaining 6 images over remaining 5400 seconds
            # 5400 / 6 = 900 seconds = 15 minutes
            assert delay == 900.0

    def test_calculate_capture_delay_behind_schedule(self, mock_session_controller):
        """Test calculate_capture_delay when session is behind schedule."""
        controller = mock_session_controller
        controller.session_config.update({
            'total_time_hours': 1.0,  # 1 hour = 3600 seconds
            'total_images': 10,
            'images_captured': 3,
            'start_time': '2023-12-01T12:00:00'
        })

        with patch('session.controller.datetime') as mock_dt:
            # Mock current time as 2 hours after start (past the total time)
            mock_dt.fromisoformat.return_value = datetime(2023, 12, 1, 12, 0, 0)
            mock_dt.now.return_value = datetime(2023, 12, 1, 14, 0, 0)

            # Act
            delay = controller._calculate_capture_delay()

            # Assert - should return minimum delay when behind schedule
            assert delay == 0.5

    def test_calculate_capture_delay_last_image(self, mock_session_controller):
        """Test calculate_capture_delay for the last image."""
        controller = mock_session_controller
        controller.session_config.update({
            'total_time_hours': 2.0,
            'total_images': 5,
            'images_captured': 4,  # 4 captured, so 1 remaining (the current one)
            'start_time': '2023-12-01T12:00:00'
        })

        # Act
        delay = controller._calculate_capture_delay()

        # Assert - should return minimum delay for last image
        assert delay == 0.5

    def test_get_session_status_time_formatting_edge_cases(self, mock_session_controller):
        """Test time formatting for various edge cases."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config.update({
            'name': 'test_session',
            'total_images': 10,
            'images_captured': 3,
            'start_time': '2023-12-01T12:00:00',
            'status': 'running',
            'session_dir': 'captures/test_session'
        })

        # Test case 1: 0 hours, 0 minutes
        controller.session_config['total_time_hours'] = 0.0
        with patch('session.controller.datetime') as mock_dt:
            mock_dt.fromisoformat.return_value = datetime(2023, 12, 1, 12, 0, 0)
            mock_dt.now.return_value = datetime(2023, 12, 1, 12, 0, 0)
            
            status = controller.get_session_status()
            # When total_time_hours is 0.0, the condition evaluates to False, so formatted_time is None
            assert status['formatted_time'] is None

        # Test case 2: Only hours (no minutes)
        controller.session_config['total_time_hours'] = 2.0
        with patch('session.controller.datetime') as mock_dt:
            mock_dt.fromisoformat.return_value = datetime(2023, 12, 1, 12, 0, 0)
            mock_dt.now.return_value = datetime(2023, 12, 1, 12, 0, 0)
            
            status = controller.get_session_status()
            assert status['formatted_time'] == "2h"

        # Test case 3: Only minutes (no hours)
        controller.session_config['total_time_hours'] = 0.5  # 30 minutes
        with patch('session.controller.datetime') as mock_dt:
            mock_dt.fromisoformat.return_value = datetime(2023, 12, 1, 12, 0, 0)
            mock_dt.now.return_value = datetime(2023, 12, 1, 12, 0, 0)
            
            status = controller.get_session_status()
            assert status['formatted_time'] == "30m"

        # Test case 4: Both hours and minutes
        controller.session_config['total_time_hours'] = 2.5  # 2 hours 30 minutes
        with patch('session.controller.datetime') as mock_dt:
            mock_dt.fromisoformat.return_value = datetime(2023, 12, 1, 12, 0, 0)
            mock_dt.now.return_value = datetime(2023, 12, 1, 12, 0, 0)
            
            status = controller.get_session_status()
            assert status['formatted_time'] == "2h 30m"

    def test_get_session_status_time_formatting_no_time_based(self, mock_session_controller):
        """Test time formatting when no time-based session is configured."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config.update({
            'name': 'test_session',
            'total_images': 10,
            'images_captured': 3,
            'start_time': '2023-12-01T12:00:00',
            'status': 'running',
            'session_dir': 'captures/test_session',
            'total_time_hours': None  # No time-based session
        })

        status = controller.get_session_status()
        assert status['formatted_time'] is None

    def test_save_session_metadata_with_datetime_objects(self, mock_session_controller):
        """Test JSON serialization with datetime objects."""
        controller = mock_session_controller
        controller.session_config.update({
            'session_dir': 'captures/test',
            'start_time': datetime(2023, 12, 1, 12, 0, 0),
            'end_time': datetime(2023, 12, 1, 14, 0, 0)
        })

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                # Act
                controller._save_session_metadata()

                # Assert
                mock_file.assert_called_once_with('captures/test/session_metadata.json', 'w')
                mock_json_dump.assert_called_once()
                
                # Verify that datetime objects are properly handled
                call_args = mock_json_dump.call_args[0]
                metadata = call_args[0]
                assert 'start_time' in metadata
                assert 'end_time' in metadata

    def test_save_session_metadata_with_mock_objects(self, mock_session_controller):
        """Test JSON serialization with mock objects."""
        controller = mock_session_controller
        controller.session_config.update({
            'session_dir': 'captures/test',
            'mock_object': Mock()  # Add a mock object
        })

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                # Act
                controller._save_session_metadata()

                # Assert
                mock_file.assert_called_once_with('captures/test/session_metadata.json', 'w')
                mock_json_dump.assert_called_once()

    def test_json_serializer_with_mock_objects(self, mock_session_controller):
        """Test custom JSON serializer with mock objects."""
        controller = mock_session_controller
        mock_obj = Mock()
        mock_obj.__class__.__name__ = "MockCamera"

        # Act
        result = controller._json_serializer(mock_obj)

        # Assert
        assert result == "<Mock MockCamera>"

    def test_json_serializer_with_non_mock_objects(self, mock_session_controller):
        """Test custom JSON serializer with non-mock objects."""
        controller = mock_session_controller

        # Act & Assert
        with pytest.raises(TypeError, match="Object of type str is not JSON serializable"):
            controller._json_serializer("not_a_mock")

    def test_cleanup_thread_timeout_scenario(self, mock_session_controller):
        """Test cleanup when session thread doesn't finish within timeout."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config['status'] = 'running'
        controller.session_config['name'] = 'test_session'
        controller.session_config['images_captured'] = 5

        # Create a mock thread that stays alive
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        mock_thread.join = Mock()
        controller.session_thread = mock_thread

        with patch('session.controller.datetime'):
            with patch('session.controller.safe_log') as mock_safe_log:
                # Act
                controller.cleanup()

                # Assert - join should be called twice (once in stop_session, once in cleanup)
                assert mock_thread.join.call_count == 2
                mock_safe_log.assert_any_call('info', "Waiting for session thread to finish...")
                mock_safe_log.assert_any_call('warning', "Session thread did not finish within timeout")
                mock_safe_log.assert_any_call('info', "Session controller cleaned up")

    def test_cleanup_thread_finishes_normally(self, mock_session_controller):
        """Test cleanup when session thread finishes normally."""
        controller = mock_session_controller
        controller.session_running = False

        # Create a mock thread that finishes
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        mock_thread.join = Mock()
        controller.session_thread = mock_thread

        with patch('session.controller.safe_log') as mock_safe_log:
            # Act
            controller.cleanup()

            # Assert - join should not be called since thread is not alive
            mock_thread.join.assert_not_called()
            mock_safe_log.assert_called_with('info', "Session controller cleaned up")
            # Should not log timeout warning
            warning_calls = [call for call in mock_safe_log.call_args_list if 'warning' in str(call) and 'timeout' in str(call)]
            assert len(warning_calls) == 0, f"Unexpected timeout warning: {warning_calls}"

    def test_session_worker_concurrent_access(self, mock_session_controller):
        """Test session worker with concurrent access scenarios."""
        controller = mock_session_controller
        controller.session_config.update({
            'total_images': 3,
            'images_captured': 0,
            'status': 'running'
        })

        # Mock capture to succeed
        with patch.object(controller, '_capture_session_image', return_value=True):
            with patch.object(controller, '_save_session_metadata'):
                # Simulate concurrent access by calling get_session_status during worker
                status_calls = []
                
                def mock_get_status():
                    status_calls.append(controller.get_session_status())
                
                # Start worker in a thread
                controller.session_running = True
                worker_thread = threading.Thread(target=controller._session_worker)
                worker_thread.start()
                
                # Call get_status concurrently
                status_thread = threading.Thread(target=mock_get_status)
                status_thread.start()
                
                # Wait for both threads
                worker_thread.join(timeout=2.0)
                status_thread.join(timeout=2.0)
                
                # Assert
                assert len(status_calls) > 0
                assert controller.session_config['images_captured'] == 3

    def test_start_session_validation_comprehensive(self, mock_session_controller):
        """Test comprehensive validation of start_session parameters."""
        controller = mock_session_controller

        # Test various invalid names
        invalid_names = ["", "   ", "\t", "\n"]
        for invalid_name in invalid_names:
            with pytest.raises(Exception, match="Session name cannot be empty"):
                controller.start_session(invalid_name, 5)

        # Test None name - this will raise Exception because None.strip() fails
        with pytest.raises(Exception, match="Session name cannot be empty"):
            controller.start_session(None, 5)

        # Test various invalid image counts
        invalid_counts = [0, -1, -100]
        for invalid_count in invalid_counts:
            with pytest.raises(Exception, match="Total images must be greater than 0"):
                controller.start_session("test", invalid_count)

        # Test non-numeric image counts
        with pytest.raises(TypeError):
            controller.start_session("test", "not_a_number")
        
        with pytest.raises(TypeError):
            controller.start_session("test", None)

    def test_session_config_immutability_during_operation(self, mock_session_controller):
        """Test that session config remains consistent during operations."""
        controller = mock_session_controller
        controller.session_running = True
        controller.session_config.update({
            'name': 'test_session',
            'total_images': 5,
            'images_captured': 2,
            'status': 'running'
        })

        # Get initial config
        initial_config = controller.session_config.copy()

        # Perform operations that should not modify core config
        status = controller.get_session_status()
        
        # Assert core config remains unchanged
        assert controller.session_config['name'] == initial_config['name']
        assert controller.session_config['total_images'] == initial_config['total_images']
        assert controller.session_config['status'] == initial_config['status']

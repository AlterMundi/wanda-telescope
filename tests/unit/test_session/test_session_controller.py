"""Unit tests for SessionController class."""
import pytest
import os
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from session.controller import SessionController

class TestSessionController:
    """Test cases for SessionController class."""
    
    @pytest.fixture
    def mock_camera(self):
        """Create a mock camera instance."""
        camera = Mock()
        camera.capture_dir = "/tmp/test_captures"
        camera.capture_still.return_value = True
        camera.capture_file = Mock()
        return camera
    
    @pytest.fixture
    def mock_mount(self):
        """Create a mock mount instance."""
        mount = Mock()
        mount.tracking = False
        mount.start_tracking.return_value = True
        mount.stop_tracking.return_value = True
        return mount
    
    @pytest.fixture
    def session_controller(self, mock_camera, mock_mount, tmp_path):
        """Create a SessionController instance for testing."""
        with patch('session.controller.os.makedirs'):
            controller = SessionController(mock_camera, mock_mount, str(tmp_path))
            return controller
    
    def test_session_controller_initialization(self, session_controller):
        """Test SessionController initializes correctly."""
        assert session_controller.camera is not None
        assert session_controller.mount is not None
        assert session_controller.session_running is False
        assert session_controller.session_thread is None
        assert isinstance(session_controller.session_config, dict)
        assert session_controller.session_config['status'] == 'idle'
    
    def test_start_session_success(self, session_controller, tmp_path):
        """Test successful session start."""
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "20231201_120000"
            mock_datetime.now.return_value.isoformat.return_value = "2023-12-01T12:00:00"
            
            success = session_controller.start_session(
                name="test_session",
                total_images=5,
                use_current_settings=True,
                enable_tracking=False
            )
            
            assert success is True
            assert session_controller.session_running is True
            assert session_controller.session_config['name'] == "test_session"
            assert session_controller.session_config['total_images'] == 5
            assert session_controller.session_config['status'] == 'running'
            assert session_controller.session_thread is not None
            assert session_controller.session_thread.is_alive()
    
    def test_start_session_already_running(self, session_controller):
        """Test starting session when one is already running."""
        # Start first session
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'):
            session_controller.start_session("test1", 5)
        
        # Try to start second session
        with pytest.raises(Exception) as exc_info:
            session_controller.start_session("test2", 5)
        assert "A session is already running" in str(exc_info.value)
    
    def test_start_session_invalid_name(self, session_controller):
        """Test starting session with invalid name."""
        with pytest.raises(Exception) as exc_info:
            session_controller.start_session("", 5)
        assert "Session name cannot be empty" in str(exc_info.value)
        
        with pytest.raises(Exception) as exc_info:
            session_controller.start_session("   ", 5)
        assert "Session name cannot be empty" in str(exc_info.value)
    
    def test_start_session_invalid_total_images(self, session_controller):
        """Test starting session with invalid total images."""
        with pytest.raises(Exception) as exc_info:
            session_controller.start_session("test", 0)
        assert "Total images must be greater than 0" in str(exc_info.value)
        
        with pytest.raises(Exception) as exc_info:
            session_controller.start_session("test", -1)
        assert "Total images must be greater than 0" in str(exc_info.value)
    
    def test_start_session_with_tracking(self, session_controller, mock_mount):
        """Test starting session with mount tracking enabled."""
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'):
            
            success = session_controller.start_session(
                name="test_session",
                total_images=5,
                enable_tracking=True
            )
            
            assert success is True
            mock_mount.start_tracking.assert_called_once()
    
    def test_start_session_directory_creation_failure(self, session_controller):
        """Test session start when directory creation fails."""
        with patch('session.controller.os.makedirs', side_effect=OSError("Permission denied")):
            with pytest.raises(Exception) as exc_info:
                session_controller.start_session("test", 5)
            
            assert "Failed to create session directory" in str(exc_info.value)
    
    def test_stop_session_success(self, session_controller):
        """Test successful session stop."""
        # Start a session first
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'):
            session_controller.start_session("test", 5)
        
        # Stop the session
        with patch('session.controller.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2023-12-01T12:05:00"
            
            success = session_controller.stop_session()
            
            assert success is True
            assert session_controller.session_running is False
            assert session_controller.session_config['status'] == 'completed'
            assert session_controller.session_config['end_time'] is not None
    
    def test_stop_session_not_running(self, session_controller):
        """Test stopping session when none is running."""
        success = session_controller.stop_session()
        assert success is True
    
    def test_stop_session_with_tracking(self, session_controller, mock_mount):
        """Test stopping session that started mount tracking."""
        # Start session with tracking
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'):
            session_controller.start_session("test", 5, enable_tracking=True)
            mock_mount.tracking = True  # Simulate tracking started
        
        # Stop session
        with patch('session.controller.datetime'):
            session_controller.stop_session()
            # Mount tracking should be stopped when session is manually stopped
            assert mock_mount.stop_tracking.call_count == 1
    
    def test_get_session_status_idle(self, session_controller):
        """Test getting session status when idle."""
        status = session_controller.get_session_status()
        
        assert status['running'] is False
        assert status['status'] == 'idle'
        assert status['progress'] == 0
        assert status['elapsed_time'] == 0
    
    def test_get_session_status_running(self, session_controller):
        """Test getting session status when running."""
        # Start a session
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20231201_120000"
            mock_datetime.now.return_value.isoformat.return_value = "2023-12-01T12:00:00"
            
            session_controller.start_session("test", 10)
            session_controller.session_config['images_captured'] = 3
        
        # Get status
        with patch('session.controller.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 12, 1, 12, 0, 15)  # 15 seconds later
            mock_datetime.fromisoformat.return_value = datetime(2023, 12, 1, 12, 0, 0)
            
            status = session_controller.get_session_status()
            
            assert status['running'] is True
            assert status['name'] == 'test'
            assert status['total_images'] == 10
            assert status['images_captured'] == 3
            assert status['progress'] == 30.0
            assert status['elapsed_time'] == 15
    
    def test_session_worker_completion(self, session_controller, mock_camera):
        """Test session worker completes successfully."""
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'), \
             patch.object(session_controller, '_capture_session_image', return_value=True):
            
            session_controller.start_session("test", 3)  # 3 images, 1 second interval
            
            # Wait for session to complete
            session_controller.session_thread.join(timeout=5.0)
            
            assert session_controller.session_running is False
            assert session_controller.session_config['images_captured'] == 3
    
    def test_session_worker_error_handling(self, session_controller):
        """Test session worker handles errors gracefully."""
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'), \
             patch.object(session_controller, '_capture_session_image', side_effect=Exception("Capture error")):
            
            session_controller.start_session("test", 5)
            
            # Wait a bit for error to occur
            time.sleep(0.1)
            
            assert session_controller.session_config['status'] == 'error'
    
    def test_capture_session_image_success(self, session_controller, mock_camera):
        """Test successful session image capture."""
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'):
            session_controller.start_session("test", 5)
            session_controller.session_config['session_dir'] = "/tmp/test_session"
        
        # Reset the mock to clear calls from session start
        mock_camera.capture_file.reset_mock()
        
        with patch('session.controller.os.path.join', return_value="/tmp/test_session/image_0001.jpg"):
            success = session_controller._capture_session_image()
            assert success is True
            mock_camera.capture_file.assert_called_once()
    
    def test_capture_session_image_with_capture_still(self, session_controller, mock_camera):
        """Test session image capture using capture_still method."""
        # Remove capture_file method to simulate cameras that only have capture_still
        del mock_camera.capture_file
        
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'), \
             patch('glob.glob', return_value=["/tmp/test_session/capture_123.jpg"]), \
             patch('session.controller.os.rename'), \
             patch('session.controller.os.path.getctime', return_value=1234567890):
            
            session_controller.start_session("test", 5)
            session_controller.session_config['session_dir'] = "/tmp/test_session"
            # Reset the mock to clear calls from session start
            mock_camera.capture_still.reset_mock()
            
            success = session_controller._capture_session_image()
            assert success is True
            mock_camera.capture_still.assert_called_once()
    
    def test_capture_session_image_failure(self, session_controller, mock_camera):
        """Test session image capture failure."""
        mock_camera.capture_file.side_effect = Exception("Capture failed")
        
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'):
            session_controller.start_session("test", 5)
            session_controller.session_config['session_dir'] = "/tmp/test_session"
        
        # Wait for the worker thread to process the error
        session_controller.session_thread.join(timeout=5.0)
        
        # Check that the session status was set to error
        assert session_controller.session_config['status'] == 'error'
        
        # Clean up
        session_controller.stop_session()
    
    def test_save_session_metadata(self, session_controller, tmp_path):
        """Test saving session metadata to JSON file."""
        session_controller.session_config['session_dir'] = str(tmp_path)
        session_controller.session_config['name'] = 'test_session'
        session_controller.session_config['total_images'] = 5
        
        session_controller._save_session_metadata()
        
        metadata_file = tmp_path / 'session_metadata.json'
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        assert metadata['name'] == 'test_session'
        assert metadata['total_images'] == 5
    
    def test_save_session_metadata_failure(self, session_controller):
        """Test saving session metadata when file write fails."""
        session_controller.session_config['session_dir'] = '/invalid/path'
        
        # Should not raise exception, just log error
        session_controller._save_session_metadata()
    
    def test_cleanup(self, session_controller):
        """Test session controller cleanup."""
        # Start a session
        with patch('session.controller.os.makedirs'), \
             patch('session.controller.datetime'):
            session_controller.start_session("test", 5)
        
        # Cleanup
        session_controller.cleanup()
        
        assert session_controller.session_running is False
    
    def test_cleanup_no_session(self, session_controller):
        """Test cleanup when no session is running."""
        session_controller.cleanup()
        # Should not raise any exceptions 
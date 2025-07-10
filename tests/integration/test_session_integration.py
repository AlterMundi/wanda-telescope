"""Integration tests for session functionality."""
import pytest
import os
import time
import tempfile
import shutil
from unittest.mock import Mock, patch
import sys
import glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from session import SessionController
from camera.implementations.mock_camera import MockCamera
from mount.implementations.mock_mount import MockMount

class TestSessionIntegration:
    """Integration tests for session functionality."""
    
    @pytest.fixture
    def temp_capture_dir(self):
        """Create a temporary capture directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_camera(self, temp_capture_dir):
        """Create a mock camera with temporary capture directory."""
        camera = MockCamera(capture_dir=temp_capture_dir)
        camera.initialize()
        return camera
    
    @pytest.fixture
    def mock_mount(self):
        """Create a mock mount."""
        mount = MockMount()
        mount.initialize()
        return mount
    
    @pytest.fixture
    def session_controller(self, mock_camera, mock_mount, temp_capture_dir):
        """Create a session controller with real camera and mount."""
        return SessionController(mock_camera, mock_mount, temp_capture_dir)
    
    def test_session_with_mock_camera_and_mount(self, session_controller, temp_capture_dir):
        """Test session functionality with mock camera and mount."""
        # Start a session
        success = session_controller.start_session(
            name="integration_test",
            total_images=3,
            use_current_settings=True,
            enable_tracking=True
        )
        
        assert success is True
        assert session_controller.session_running is True
        
        # Wait for session to complete
        session_controller.session_thread.join(timeout=10.0)
        
        # Check session completed
        assert session_controller.session_running is False
        assert session_controller.session_config['images_captured'] == 3
        assert session_controller.session_config['status'] == 'completed'  # Completed when worker finishes
        
        # Manually stop the session (should be no-op since already completed)
        session_controller.stop_session()
        
        # Status should still be completed
        assert session_controller.session_config['status'] == 'completed'
        
        # Check session directory was created
        session_dir = os.path.join(temp_capture_dir, 'integration_test')
        assert os.path.exists(session_dir)
        assert os.path.exists(session_dir)
        
        # Check metadata file was created
        metadata_file = os.path.join(session_dir, 'session_metadata.json')
        assert os.path.exists(metadata_file)
        
        # Check images were captured
        image_files = [f for f in os.listdir(session_dir) if f.startswith('image_') and f.endswith('.jpg')]
        assert len(image_files) == 3
        
        # Verify image files are numbered correctly
        image_numbers = sorted([int(f.split('_')[1].split('.')[0]) for f in image_files])
        assert image_numbers == [1, 2, 3]
    
    def test_session_with_mount_tracking(self, session_controller, mock_mount):
        """Test session with mount tracking enabled."""
        # Start session with tracking
        success = session_controller.start_session(
            name="tracking_test",
            total_images=2,
            enable_tracking=True
        )
        
        assert success is True
        
        # Check mount tracking was started
        assert mock_mount.tracking is True
        
        # Wait for session to complete
        session_controller.session_thread.join(timeout=5.0)
        
        # Stop session
        session_controller.stop_session()
        
        # Check mount tracking was stopped
        assert mock_mount.tracking is False
    
    def test_session_status_updates(self, session_controller):
        """Test session status updates during execution."""
        # Start session
        session_controller.start_session(
            name="status_test",
            total_images=5
        )
        
        # Check initial status
        status = session_controller.get_session_status()
        assert status['running'] is True
        assert status['name'] == 'status_test'
        assert status['total_images'] == 5
        assert status['images_captured'] == 0
        assert status['progress'] == 0.0
        
        # Wait a bit and check progress
        time.sleep(1.0)
        status = session_controller.get_session_status()
        assert status['running'] is True
        assert status['images_captured'] > 0
        assert status['progress'] > 0.0
        
        # Wait for completion
        session_controller.session_thread.join(timeout=10.0)
        
        # Check final status
        status = session_controller.get_session_status()
        assert status['running'] is False
        assert status['images_captured'] == 5
        assert status['progress'] == 100.0
    
    def test_session_error_recovery(self, session_controller, mock_camera):
        """Test session error handling and recovery."""
        # Make camera capture fail by raising an exception
        original_capture_still = mock_camera.capture_still
        original_capture_file = None
        
        # Mock both methods that could be called
        mock_camera.capture_still = Mock(side_effect=Exception("Camera capture failed"))
        
        if hasattr(mock_camera, 'capture_file'):
            original_capture_file = mock_camera.capture_file
            mock_camera.capture_file = Mock(side_effect=Exception("Camera capture failed"))
        
        # Start session
        session_controller.start_session(
            name="error_test",
            total_images=3
        )
        
        # Wait for error to occur and thread to finish
        session_controller.session_thread.join(timeout=5.0)
        
        # Check session status - should be error when camera capture fails
        assert session_controller.session_config['status'] == 'error'
        
        # Manually stop the session (should be no-op since already completed)
        session_controller.stop_session()
        
        # Status should still be error
        assert session_controller.session_config['status'] == 'error'
        
        # Restore camera functionality
        mock_camera.capture_still = original_capture_still
        if original_capture_file is not None:
            mock_camera.capture_file = original_capture_file
        
        # Start new session should work
        success = session_controller.start_session(
            name="recovery_test",
            total_images=1
        )
        
        assert success is True
        
        # Wait for completion
        session_controller.session_thread.join(timeout=5.0)
        session_controller.stop_session()
        
    def test_session_directory_structure(self, session_controller, temp_capture_dir):
        """Test session creates proper directory structure."""
        # Start session
        session_controller.start_session(
            name="structure_test",
            total_images=1,
            use_current_settings=True,
            enable_tracking=False
        )
        
        # Wait for completion
        session_controller.session_thread.join(timeout=5.0)
        session_controller.stop_session()
        
        # Check directory structure
        session_dir = os.path.join(temp_capture_dir, 'structure_test')
        assert os.path.exists(session_dir)
        
        # Check required files exist
        assert os.path.exists(os.path.join(session_dir, 'session_metadata.json'))
        assert os.path.exists(os.path.join(session_dir, 'image_0001.jpg'))
    
    def test_session_metadata_content(self, session_controller, temp_capture_dir):
        """Test session metadata file content."""
        # Start session
        session_controller.start_session(
            name="metadata_test",
            total_images=2,
            use_current_settings=True,
            enable_tracking=True
        )
        
        # Wait for completion
        session_controller.session_thread.join(timeout=5.0)
        session_controller.stop_session()
        
        # Find session directory
        session_dir = os.path.join(temp_capture_dir, 'metadata_test')
        assert os.path.exists(session_dir)
        metadata_file = os.path.join(session_dir, 'session_metadata.json')
        
        # Read and verify metadata
        import json
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Check required fields
        assert metadata['name'] == 'metadata_test'
        assert metadata['total_images'] == 2
        assert metadata['use_current_settings'] is True
        assert metadata['enable_tracking'] is True
        assert metadata['images_captured'] == 2
        assert metadata['status'] == 'completed'
        assert 'start_time' in metadata
        assert 'end_time' in metadata
        assert 'session_dir' in metadata 
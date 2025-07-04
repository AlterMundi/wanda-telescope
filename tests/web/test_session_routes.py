"""Unit tests for session web routes."""
import pytest
import json
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.app import WandaApp
from session import SessionController

class TestSessionRoutes:
    """Test cases for session web routes."""
    
    @pytest.fixture
    def mock_camera(self):
        """Create a mock camera instance."""
        camera = Mock()
        camera.capture_dir = "/tmp/test_captures"
        camera.capture_still.return_value = True
        camera.capture_file = Mock()
        camera.us_to_shutter_string.return_value = "1/1000"
        camera.gain_to_iso.return_value = 100
        camera.slider_to_us.return_value = 1000
        camera.iso_to_gain.return_value = 1.0
        camera.exposure_us = 1000
        camera.gain = 1.0
        camera.use_digital_gain = False
        camera.digital_gain = 1.0
        camera.save_raw = False
        camera.skip_frames = 0
        camera.recording = False
        camera.capture_status = "Ready"
        camera.get_exposure_seconds.return_value = 0.001
        camera.update_camera_settings = Mock()
        camera.cleanup = Mock()
        return camera
    
    @pytest.fixture
    def mock_mount(self):
        """Create a mock mount instance."""
        mount = Mock()
        mount.tracking = False
        mount.status = "Mount ready"
        mount.direction = True
        mount.speed = 1.0
        mount.start_tracking.return_value = True
        mount.stop_tracking.return_value = True
        mount.update_settings = Mock()
        mount.cleanup = Mock()
        return mount
    
    @pytest.fixture
    def mock_session_controller(self):
        """Create a mock session controller."""
        controller = Mock()
        controller.start_session.return_value = True
        controller.stop_session.return_value = True
        controller.get_session_status.return_value = {
            'running': False,
            'status': 'idle',
            'progress': 0,
            'elapsed_time': 0
        }
        controller.cleanup = Mock()
        return controller
    
    @pytest.fixture
    def flask_app(self, mock_camera, mock_mount, mock_session_controller):
        """Create a Flask app instance for testing."""
        with patch('web.app.MountController', return_value=mock_mount), \
             patch('web.app.SessionController', return_value=mock_session_controller):
            app = WandaApp(camera=mock_camera)
            app.app.config["TESTING"] = True
            return app.app
    
    def test_start_session_success(self, flask_app, mock_session_controller):
        """Test successful session start via web route."""
        with flask_app.test_client() as client:
            response = client.post('/start_session', data={
                'session_name': 'test_session',
                'total_images': '5',
                'use_current_settings': 'on',
                'enable_tracking': 'on'
            }, headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify session controller was called correctly
            mock_session_controller.start_session.assert_called_once_with(
                name='test_session',
                total_images=5,
                use_current_settings=True,
                enable_tracking=True
            )
    
    def test_start_session_missing_name(self, flask_app):
        """Test session start with missing session name."""
        with flask_app.test_client() as client:
            response = client.post('/start_session', data={
                'total_images': '5'
            }, headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Session name is required' in data['error']
    
    def test_start_session_invalid_total_images(self, flask_app):
        """Test session start with invalid total images."""
        with flask_app.test_client() as client:
            response = client.post('/start_session', data={
                'session_name': 'test_session',
                'total_images': '0'
            }, headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Total images must be greater than 0' in data['error']
    
    def test_start_session_missing_total_images(self, flask_app):
        """Test session start with missing total images."""
        with flask_app.test_client() as client:
            response = client.post('/start_session', data={
                'session_name': 'test_session'
            }, headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Total images must be greater than 0' in data['error']
    
    def test_start_session_controller_error(self, flask_app, mock_session_controller):
        """Test session start when controller raises exception."""
        mock_session_controller.start_session.side_effect = Exception("Test error")
        
        with flask_app.test_client() as client:
            response = client.post('/start_session', data={
                'session_name': 'test_session',
                'total_images': '5'
            }, headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Test error' in data['error']
    
    def test_stop_session_success(self, flask_app, mock_session_controller):
        """Test successful session stop via web route."""
        with flask_app.test_client() as client:
            response = client.post('/stop_session', headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify session controller was called
            mock_session_controller.stop_session.assert_called_once()
    
    def test_stop_session_controller_error(self, flask_app, mock_session_controller):
        """Test session stop when controller raises exception."""
        mock_session_controller.stop_session.side_effect = Exception("Test error")
        
        with flask_app.test_client() as client:
            response = client.post('/stop_session', headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Test error' in data['error']
    
    def test_get_session_status_success(self, flask_app, mock_session_controller):
        """Test getting session status via web route."""
        mock_session_controller.get_session_status.return_value = {
            'running': True,
            'status': 'running',
            'name': 'test_session',
            'total_images': 10,
            'images_captured': 3,
            'progress': 30.0,
            'elapsed_time': 15
        }
        
        with flask_app.test_client() as client:
            response = client.get('/session_status', headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['running'] is True
            assert data['name'] == 'test_session'
            assert data['total_images'] == 10
            assert data['images_captured'] == 3
            assert data['progress'] == 30.0
            assert data['elapsed_time'] == 15
    
    def test_get_session_status_controller_error(self, flask_app, mock_session_controller):
        """Test getting session status when controller raises exception."""
        mock_session_controller.get_session_status.side_effect = Exception("Test error")
        
        with flask_app.test_client() as client:
            response = client.get('/session_status', headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'Test error' in data['error']
    
    def test_start_session_form_data_parsing(self, flask_app, mock_session_controller):
        """Test form data parsing for session start."""
        with flask_app.test_client() as client:
            response = client.post('/start_session', data={
                'session_name': '  test_session  ',  # Should be stripped
                'total_images': '5',
                'use_current_settings': 'on',
                'enable_tracking': 'on'
            }, headers={'Accept': 'application/json'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify session controller was called with stripped name and default values
            mock_session_controller.start_session.assert_called_once_with(
                name='test_session',  # Should be stripped
                total_images=5,
                use_current_settings=True,  # Should default to True when in form
                enable_tracking=True  # Should default to True when in form
            )
    
    def test_session_routes_without_json_header(self, flask_app):
        """Test session routes work without JSON Accept header."""
        with flask_app.test_client() as client:
            # Test start session
            response = client.post('/start_session', data={
                'session_name': 'test_session',
                'total_images': '5'
            })
            
            # Should still return JSON response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'success' in data
            
            # Test stop session
            response = client.post('/stop_session')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'success' in data
            
            # Test get status
            response = client.get('/session_status')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'running' in data 
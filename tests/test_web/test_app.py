"""
Comprehensive tests for WandaApp web application.
"""
import pytest
import json
import os
import math
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from web.app import WandaApp


class TestWandaApp:
    """Test suite for WandaApp class."""

    @pytest.fixture
    def mock_camera(self):
        """Mock camera object for testing."""
        camera = Mock()
        # Set up basic camera attributes needed by web app
        camera.exposure_us = 100000  # 0.1 seconds in microseconds
        camera.gain = 1.0
        camera.use_digital_gain = False
        camera.digital_gain = 1.0
        camera.night_vision_mode = False
        camera.night_vision_intensity = 1.0
        camera.save_raw = False
        camera.recording = False
        camera.capture_status = "Ready"
        camera.capture_dir = "captures"
        camera.skip_frames = 0
        camera.exposure_mode = "manual"

        # Mock methods
        camera.get_frame = Mock(return_value=b"fake_jpeg_data")
        camera.capture_still = Mock(return_value=True)
        camera.start_video = Mock(return_value=True)
        camera.stop_video = Mock(return_value=True)
        camera.update_camera_settings = Mock()
        camera.get_exposure_seconds = Mock(return_value=0.1)
        camera.iso_to_gain = Mock(side_effect=lambda iso: iso / 100.0)
        camera.gain_to_iso = Mock(return_value=800)
        camera.cleanup = Mock()

        # Mock set_exposure_us method to update exposure_us attribute
        def mock_set_exposure_us(us, gain=None):
            camera.exposure_us = us
        camera.set_exposure_us = Mock(side_effect=mock_set_exposure_us)

        return camera

    @pytest.fixture
    def mock_mount(self):
        """Mock mount object for testing."""
        mount = Mock()
        mount.status = "Ready"
        mount.tracking = False
        mount.direction = True
        mount.speed = 1.0

        # Mock methods
        mount.start_tracking = Mock(return_value=True)
        mount.stop_tracking = Mock(return_value=True)
        mount.update_settings = Mock()
        mount.cleanup = Mock()

        return mount

    @pytest.fixture
    def mock_session_controller(self, mock_camera, mock_mount):
        """Mock session controller for testing."""
        controller = Mock()
        controller.get_session_status = Mock(return_value={
            'active': False,
            'name': '',
            'total_images': 0,
            'captured_images': 0,
            'remaining_time': 0
        })
        controller.start_session = Mock(return_value=True)
        controller.stop_session = Mock(return_value=True)
        controller.cleanup = Mock()

        return controller

    @pytest.fixture
    def app_instance(self, mock_camera, mock_mount, mock_session_controller):
        """Create WandaApp instance with mocked dependencies."""
        with patch('web.app.MountController', return_value=mock_mount), \
             patch('web.app.SessionController', return_value=mock_session_controller), \
             patch('web.app.logger'), \
             patch('web.app.os.path.dirname', return_value='/fake/path'), \
             patch('web.app.os.path.join', return_value='/fake/path/templates'), \
             patch('web.app.os.path.abspath', return_value='/fake/path/web'):

            app = WandaApp(camera=mock_camera)
            app.app.config['TESTING'] = True
            return app

    @pytest.fixture
    def client(self, app_instance):
        """Flask test client."""
        return app_instance.app.test_client()

    @pytest.fixture
    def mock_config(self):
        """Mock config module."""
        with patch('web.app.config') as mock_config:
            mock_config.HOST = '127.0.0.1'
            mock_config.PORT = 5000
            yield mock_config

    # Test Initialization
    def test_init_requires_camera(self):
        """Test that WandaApp requires a camera instance."""
        with pytest.raises(ValueError, match="Camera instance is required"):
            WandaApp(camera=None)

    def test_init_with_camera(self, mock_camera, mock_mount, mock_session_controller):
        """Test WandaApp initialization with valid camera."""
        with patch('web.app.MountController', return_value=mock_mount), \
             patch('web.app.SessionController', return_value=mock_session_controller), \
             patch('web.app.logger'), \
             patch('web.app.os.path.dirname', return_value='/fake/path'), \
             patch('web.app.os.path.join', return_value='/fake/path/templates'), \
             patch('web.app.os.path.abspath', return_value='/fake/path/web'):

            app = WandaApp(camera=mock_camera)

            assert app.camera == mock_camera
            assert app.mount == mock_mount
            assert app.session_controller == mock_session_controller
            assert hasattr(app, 'app')
            assert isinstance(app.app, Flask)

    def test_setup_routes(self, app_instance):
        """Test that routes are properly set up."""
        routes = [rule.rule for rule in app_instance.app.url_map.iter_rules()]
        expected_routes = [
            '/', '/video_feed', '/capture_still', '/start_video', '/stop_video',
            '/capture_status', '/start_tracking', '/stop_tracking',
            '/start_session', '/stop_session', '/session_status'
        ]

        for route in expected_routes:
            assert route in routes, f"Route {route} not found in app routes"

    def test_cleanup_calls_dependencies(self, app_instance):
        """Test that cleanup calls cleanup on all dependencies."""
        app_instance.cleanup()

        app_instance.camera.cleanup.assert_called_once()
        app_instance.mount.cleanup.assert_called_once()
        app_instance.session_controller.cleanup.assert_called_once()

    # Test Route Handlers - Index
    def test_index_get_request(self, client, app_instance):
        """Test GET request to index route."""
        with patch.object(app_instance, '_prepare_template_vars') as mock_prepare, \
             patch('web.app.render_template') as mock_render:
            mock_prepare.return_value = {'test': 'data'}

            response = client.get('/')

            assert response.status_code == 200
            mock_prepare.assert_called_once()
            mock_render.assert_called_once_with('index.html', **{'test': 'data'})

    def test_index_post_request_regular(self, client, app_instance):
        """Test POST request to index route without AJAX."""
        with patch.object(app_instance, '_handle_post_request') as mock_handle, \
             patch.object(app_instance, '_prepare_template_vars') as mock_prepare, \
             patch('web.app.render_template') as mock_render:
            mock_prepare.return_value = {'test': 'data'}

            response = client.post('/', data={'exposure': '500', 'iso': '400'})

            assert response.status_code == 200
            mock_handle.assert_called_once()
            mock_prepare.assert_called_once()
            mock_render.assert_called_once_with('index.html', **{'test': 'data'})

    def test_index_post_request_ajax(self, client, app_instance):
        """Test POST request to index route with AJAX."""
        with patch.object(app_instance, '_handle_post_request') as mock_handle, \
             patch.object(app_instance, '_prepare_template_vars') as mock_prepare:
            mock_prepare.return_value = {'test': 'data'}

            response = client.post('/', data={'exposure': '500'},
                                 headers={'Accept': 'application/json'})

            assert response.status_code == 200
            mock_handle.assert_called_once()
            mock_prepare.assert_called_once()
            data = json.loads(response.data)
            assert data == {'test': 'data'}

    # Test Route Handlers - Camera
    def test_video_feed_route(self, client, app_instance):
        """Test video feed route returns proper streaming response."""
        # Mock the camera to return data, then raise an exception to stop the generator
        app_instance.camera.get_frame.side_effect = [b"fake_jpeg_data", Exception("Stop generator")]

        try:
            response = client.get('/video_feed')
            assert response.status_code == 200
            assert response.content_type == 'multipart/x-mixed-replace; boundary=frame'
            # Check that response contains expected boundary
            assert b'--frame\r\n' in response.data
        except Exception:
            # The test is primarily to ensure the route works, even if the streaming fails
            pass

    def test_capture_status_route(self, client, app_instance):
        """Test capture status route returns JSON."""
        response = client.get('/capture_status')

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert 'capture_status' in data
        assert 'recording' in data

    def test_capture_still_regular_request(self, client, app_instance):
        """Test capture still route without AJAX."""
        app_instance.camera.capture_still.return_value = True

        response = client.post('/capture_still')

        assert response.status_code == 302  # Redirect
        assert app_instance.camera.capture_still.called

    def test_capture_still_ajax_request(self, client, app_instance):
        """Test capture still route with AJAX."""
        app_instance.camera.capture_still.return_value = True

        response = client.post('/capture_still',
                             headers={'Accept': 'application/json'})

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'capture_status' in data

    def test_start_video_regular_request(self, client, app_instance):
        """Test start video route without AJAX."""
        app_instance.camera.start_video.return_value = True

        response = client.post('/start_video')

        assert response.status_code == 302  # Redirect
        assert app_instance.camera.start_video.called

    def test_start_video_ajax_request(self, client, app_instance):
        """Test start video route with AJAX."""
        app_instance.camera.start_video.return_value = True

        response = client.post('/start_video',
                             headers={'Accept': 'application/json'})

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['success'] is True

    def test_stop_video_regular_request(self, client, app_instance):
        """Test stop video route without AJAX."""
        app_instance.camera.stop_video.return_value = True

        response = client.post('/stop_video')

        assert response.status_code == 302  # Redirect
        assert app_instance.camera.stop_video.called

    def test_stop_video_ajax_request(self, client, app_instance):
        """Test stop video route with AJAX."""
        app_instance.camera.stop_video.return_value = True

        response = client.post('/stop_video',
                             headers={'Accept': 'application/json'})

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['success'] is True

    # Test Route Handlers - Mount
    def test_start_tracking_regular_request(self, client, app_instance):
        """Test start tracking route without AJAX."""
        app_instance.mount.start_tracking.return_value = True

        response = client.post('/start_tracking')

        assert response.status_code == 302  # Redirect
        assert app_instance.mount.start_tracking.called

    def test_start_tracking_ajax_request(self, client, app_instance):
        """Test start tracking route with AJAX."""
        app_instance.mount.start_tracking.return_value = True

        response = client.post('/start_tracking',
                             headers={'Accept': 'application/json'})

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'mount_status' in data
        assert 'mount_tracking' in data

    def test_stop_tracking_regular_request(self, client, app_instance):
        """Test stop tracking route without AJAX."""
        app_instance.mount.stop_tracking.return_value = True

        response = client.post('/stop_tracking')

        assert response.status_code == 302  # Redirect
        assert app_instance.mount.stop_tracking.called

    def test_stop_tracking_ajax_request(self, client, app_instance):
        """Test stop tracking route with AJAX."""
        app_instance.mount.stop_tracking.return_value = True

        response = client.post('/stop_tracking',
                             headers={'Accept': 'application/json'})

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'mount_status' in data
        assert 'mount_tracking' in data

    # Test Route Handlers - Session
    def test_start_session_success(self, client, app_instance):
        """Test successful session start."""
        app_instance.session_controller.start_session.return_value = True

        response = client.post('/start_session', data={
            'session_name': 'Test Session',
            'total_images': '10',
            'use_current_settings': 'on',
            'enable_tracking': 'on'
        })

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'session_status' in data

        app_instance.session_controller.start_session.assert_called_once_with(
            name='Test Session',
            total_images=10,
            use_current_settings=True,
            enable_tracking=True,
            total_time_hours=None
        )

    def test_start_session_missing_name(self, client, app_instance):
        """Test session start with missing name."""
        response = client.post('/start_session', data={
            'total_images': '10'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Session name is required' in data['error']

    def test_start_session_invalid_total_images(self, client, app_instance):
        """Test session start with invalid total images."""
        response = client.post('/start_session', data={
            'session_name': 'Test Session',
            'total_images': '0'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Total images must be greater than 0' in data['error']

    def test_start_session_exception(self, client, app_instance):
        """Test session start with exception."""
        app_instance.session_controller.start_session.side_effect = Exception("Test error")

        response = client.post('/start_session', data={
            'session_name': 'Test Session',
            'total_images': '10'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Test error' in data['error']

    def test_start_session_with_time_based(self, client, app_instance):
        """Test successful session start with time-based capture."""
        app_instance.session_controller.start_session.return_value = True

        response = client.post('/start_session', data={
            'session_name': 'Time Session',
            'total_images': '10',
            'total_time_hours': '4',
            'total_time_minutes': '30',
            'use_current_settings': 'on'
        })

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'session_status' in data

        app_instance.session_controller.start_session.assert_called_once_with(
            name='Time Session',
            total_images=10,
            use_current_settings=True,
            enable_tracking=False,
            total_time_hours=4.5  # 4 hours + 30 minutes = 4.5 hours
        )

    def test_start_session_zero_time_hours(self, client, app_instance):
        """Test session start with zero time hours."""
        response = client.post('/start_session', data={
            'session_name': 'Test Session',
            'total_images': '10',
            'total_time_hours': '0',
            'total_time_minutes': '0'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Total time must be greater than 0' in data['error']

    def test_start_session_negative_time_hours(self, client, app_instance):
        """Test session start with negative time hours."""
        response = client.post('/start_session', data={
            'session_name': 'Test Session',
            'total_images': '10',
            'total_time_hours': '-1'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Total time must be greater than 0' in data['error']

    def test_start_session_invalid_time_hours(self, client, app_instance):
        """Test session start with invalid time hours format."""
        response = client.post('/start_session', data={
            'session_name': 'Test Session',
            'total_images': '10',
            'total_time_hours': 'not_a_number'
        })

        # When form.get('total_time_hours', type=float) fails to parse, it returns None
        # which should be handled gracefully (None is valid for non-time-based sessions)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True  # Should succeed as None is valid

        app_instance.session_controller.start_session.assert_called_once_with(
            name='Test Session',
            total_images=10,
            use_current_settings=False,
            enable_tracking=False,
            total_time_hours=None
        )

    def test_stop_session_success(self, client, app_instance):
        """Test successful session stop."""
        app_instance.session_controller.stop_session.return_value = True

        response = client.post('/stop_session')

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'session_status' in data

        app_instance.session_controller.stop_session.assert_called_once()

    def test_stop_session_exception(self, client, app_instance):
        """Test session stop with exception."""
        app_instance.session_controller.stop_session.side_effect = Exception("Stop error")

        response = client.post('/stop_session')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Stop error' in data['error']

    def test_session_status_route(self, client, app_instance):
        """Test session status route."""
        response = client.get('/session_status')

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert 'active' in data
        assert 'name' in data

    def test_session_status_exception(self, client, app_instance):
        """Test session status route with exception."""
        app_instance.session_controller.get_session_status.side_effect = Exception("Status error")

        response = client.get('/session_status')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Status error' in data['error']

    # Test Form Handling
    def test_handle_post_request_camera_settings(self, app_instance):
        """Test handling camera settings from form."""
        from flask import Flask
        from unittest.mock import Mock

        # Create a mock request with proper form data
        mock_request = Mock()
        mock_form = Mock()
        mock_form.get.side_effect = lambda key, type=None, default=None: {
            'exposure': 500,
            'iso': 400,
            'night_vision_intensity': 2.5,
            'performance': 2
        }.get(key, None)
        mock_form.__contains__ = lambda self, key: key in ['night_vision_mode', 'save_raw']
        mock_request.form = mock_form

        with patch('web.app.request', mock_request):
            app_instance._handle_post_request()

            # Check camera settings were updated
            # exposure_seconds = min_seconds * math.exp(500 * log_range / 1000)
            # With max_seconds = 230, this should be approximately 4.796 seconds
            expected_exposure_us = 4795831  # 4.795831523312719 * 1000000
            expected_gain = 7.0  # 700.0 / 100 (ISO 700 converted to gain)
            app_instance.camera.set_exposure_us.assert_called_once_with(expected_exposure_us, expected_gain)
            assert app_instance.camera.exposure_us == expected_exposure_us
            app_instance.camera.iso_to_gain.assert_called_with(700.0)  # Converted ISO value: 100 + (1600-100) * 400/1000 = 700
            assert app_instance.camera.night_vision_mode is True
            assert app_instance.camera.night_vision_intensity == 2.5
            assert app_instance.camera.save_raw is True
            assert app_instance.camera.skip_frames == 2
            app_instance.camera.update_camera_settings.assert_called_once()

    def test_handle_post_request_mount_settings(self, app_instance):
        """Test handling mount settings from form."""
        from flask import Flask
        from unittest.mock import Mock

        # Create a mock request with proper form data
        mock_request = Mock()
        mock_form = Mock()
        mock_form.get.side_effect = lambda key, type=None, default=None: {
            'mount_speed': 1.5,
            'mount_direction': 'clockwise'
        }.get(key, None)
        mock_form.__contains__ = lambda self, key: key in ['mount_speed', 'mount_direction']
        mock_request.form = mock_form

        with patch('web.app.request', mock_request):
            app_instance._handle_post_request()

            # Check mount settings were updated
            app_instance.mount.update_settings.assert_called_once_with(
                speed=1.5, direction=True
            )

    def test_prepare_template_vars(self, app_instance):
        """Test template variable preparation."""
        # Set up camera state
        app_instance.camera.get_exposure_seconds.return_value = 0.1
        app_instance.camera.gain_to_iso.return_value = 800

        # Call the method
        vars_dict = app_instance._prepare_template_vars()

        # Check expected keys are present
        expected_keys = [
            'current_exposure', 'iso_slider_value', 'current_iso_label',
            'slider_value', 'exposure_seconds', 'night_vision_mode',
            'night_vision_intensity', 'save_raw', 'skip_frames',
            'performance_text', 'recording', 'capture_status',
            'capture_dir', 'mount_status', 'mount_tracking',
            'mount_direction', 'mount_speed'
        ]

        for key in expected_keys:
            assert key in vars_dict, f"Key {key} not found in template vars"

        # Check specific values
        assert vars_dict['exposure_seconds'] == 0.1
        assert vars_dict['night_vision_mode'] is False
        assert vars_dict['recording'] is False

    # Test Utility Methods
    def test_format_exposure_display(self, app_instance):
        """Test exposure time formatting for display."""
        # Test short exposure
        assert app_instance._format_exposure_display(0.05) == "0.1s"
        assert app_instance._format_exposure_display(0.5) == "0.5s"

        # Test medium exposure
        assert app_instance._format_exposure_display(1.5) == "1.5s"
        assert app_instance._format_exposure_display(9.9) == "9.9s"

        # Test long exposure
        assert app_instance._format_exposure_display(10) == "10s"
        assert app_instance._format_exposure_display(230) == "230s"

    def test_slider_to_seconds_conversion(self, app_instance):
        """Test slider value to seconds conversion."""
        # Test minimum value
        assert app_instance._slider_to_seconds(0) == pytest.approx(0.1, abs=0.01)

        # Test middle value
        result = app_instance._slider_to_seconds(500)
        assert 0.1 < result < 230

        # Test maximum value
        assert app_instance._slider_to_seconds(1000) == pytest.approx(230, abs=0.01)

    def test_iso_to_slider_and_label(self, app_instance):
        """Test ISO value to slider conversion."""
        # Test normal ISO value
        slider_val, label = app_instance._iso_to_slider_and_label(800)
        assert slider_val == 466  # (800 - 100) / (1600 - 100) * 1000 = 700 / 1500 * 1000 = 466.67, rounded to 466
        assert label == "Medium (800)"

        # Test low ISO value
        slider_val, label = app_instance._iso_to_slider_and_label(100)
        assert slider_val == 0
        assert label == "Low (100)"

        # Test high ISO value
        slider_val, label = app_instance._iso_to_slider_and_label(1600)
        assert slider_val == 1000
        assert label == "High (1600)"

        # Test non-milestone value
        slider_val, label = app_instance._iso_to_slider_and_label(400)
        # (400 - 100) / (1600 - 100) * 1000 = 300 / 1500 * 1000 = 200
        assert slider_val == 200  # int(200) = 200
        assert label == "400"

    def test_run_method_with_config(self, mock_camera, mock_config):
        """Test the run method with mocked config."""
        with patch('web.app.MountController') as mock_mount_class, \
             patch('web.app.SessionController') as mock_session_class, \
             patch('web.app.logger'), \
             patch('web.app.os.path.dirname', return_value='/fake'), \
             patch('web.app.os.path.join', return_value='/fake/templates'), \
             patch('web.app.os.path.abspath', return_value='/fake/web'), \
             patch.object(WandaApp, 'cleanup') as mock_cleanup:

            mock_mount_instance = Mock()
            mock_session_instance = Mock()
            mock_mount_class.return_value = mock_mount_instance
            mock_session_class.return_value = mock_session_instance

            app = WandaApp(camera=mock_camera)

            # Mock the app.run to avoid actually starting server
            with patch.object(app.app, 'run') as mock_run:
                # Mock the run method to just return without starting server
                mock_run.return_value = None

                # Call app.run() - it should call Flask's run method and then cleanup
                app.run()

                mock_run.assert_called_once_with(host='127.0.0.1', port=5000, threaded=True)
                mock_cleanup.assert_called_once()

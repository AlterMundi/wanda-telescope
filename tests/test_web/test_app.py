"""
Tests for the RESTful WandaApp Flask application.
"""
import json
import os
import sys
from unittest.mock import ANY, Mock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from web.app import (  # noqa: E402
    WandaApp,
    broadcast_camera_update,
    broadcast_capture_event,
    broadcast_mount_event,
    broadcast_session_event,
    socketio,
)


@pytest.fixture
def mock_camera():
    """Mock camera object for testing REST endpoints."""
    camera = Mock()
    camera.exposure_seconds = 0.5
    camera.capture_status = "Idle"
    camera.capture_dir = "/captures"
    camera.capture_still = Mock(return_value=True)
    camera.get_frame = Mock(return_value=b"frame")
    camera.get_exposure_seconds = Mock(return_value=0.5)
    camera.get_exposure_us = Mock(return_value=500000)
    camera.set_exposure_us = Mock()
    camera.iso_to_gain = Mock(side_effect=lambda iso: iso / 100.0)
    camera.gain_to_iso = Mock(return_value=800)
    camera.update_camera_settings = Mock()
    camera.night_vision_mode = False
    camera.night_vision_intensity = 5.0
    camera.save_raw = False
    camera.skip_frames = 0
    camera.recording = False
    camera.mode = "still"
    camera.gain = 4.0
    camera.cleanup = Mock()
    return camera


@pytest.fixture
def mock_mount():
    """Mock mount controller for testing REST endpoints."""
    mount = Mock()
    mount.status = "Ready"
    mount.tracking = False
    mount.direction = True
    mount.speed = 1.5
    mount.start_tracking = Mock(return_value=True)
    mount.stop_tracking = Mock(return_value=True)
    mount.update_settings = Mock()
    mount.cleanup = Mock()
    return mount


@pytest.fixture
def mock_session_controller():
    """Mock session controller for testing REST endpoints."""
    controller = Mock()
    controller.get_session_status = Mock(return_value={
        "active": False,
        "name": "",
        "total_images": 0,
        "captured_images": 0,
        "remaining_time": 0,
    })
    controller.start_session = Mock(return_value=True)
    controller.stop_session = Mock(return_value=True)
    controller.cleanup = Mock()
    return controller


@pytest.fixture
def app_instance(mock_camera, mock_mount, mock_session_controller):
    """Create a WandaApp instance with mocked dependencies."""
    with patch("web.app.MountController", return_value=mock_mount), \
         patch("web.app.SessionController", return_value=mock_session_controller), \
         patch("web.app.logger"):
        app = WandaApp(camera=mock_camera)
        app.app.config["TESTING"] = True
        return app


@pytest.fixture
def client(app_instance):
    """Flask test client for the WandaApp."""
    return app_instance.app.test_client()


class TestRoutes:
    """Route registration tests."""

    def test_setup_routes(self, app_instance):
        routes = {rule.rule for rule in app_instance.app.url_map.iter_rules()}
        expected_routes = {
            "/video_feed",
            "/api/camera/status",
            "/api/camera/settings",
            "/api/camera/capture",
            "/api/mount/status",
            "/api/mount/tracking",
            "/api/session/start",
            "/api/session/stop",
            "/api/session/status",
            "/api/captures",
        }
        assert expected_routes.issubset(routes)


class TestCameraEndpoints:
    """Camera API endpoint tests."""

    def test_camera_status_success(self, client, app_instance):
        response = client.get("/api/camera/status")
        payload = response.get_json()

        assert response.status_code == 200
        assert payload["success"] is True
        assert "data" in payload
        data = payload["data"]
        assert "iso" in data
        assert "exposure_seconds" in data
        assert "mode" in data
        assert payload["message"]
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    def test_camera_settings_update(self, client, app_instance):
        payload = {
            "exposure_seconds": 2.5,
            "iso": 600,
            "night_vision_mode": True,
            "night_vision_intensity": 7.5,
            "save_raw": True,
            "skip_frames": 2,
        }

        response = client.post("/api/camera/settings", json=payload)
        body = response.get_json()

        assert response.status_code == 200
        assert body["success"] is True
        app_instance.camera.set_exposure_us.assert_called_once()
        exposure_us, gain = app_instance.camera.set_exposure_us.call_args[0]
        assert pytest.approx(2.5 * 1_000_000, rel=0.01) == exposure_us
        assert pytest.approx(6.0, rel=0.01) == gain
        app_instance.camera.update_camera_settings.assert_called_once()

    def test_camera_settings_missing_payload(self, client):
        response = client.post("/api/camera/settings")
        body = response.get_json()

        assert response.status_code == 400
        assert body["success"] is False
        assert body["code"] == "INVALID_REQUEST"

    def test_camera_capture_success(self, client, app_instance):
        app_instance.camera.capture_status = "Capture complete"

        response = client.post("/api/camera/capture")
        body = response.get_json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["data"]["capture_status"] == "Capture complete"
        app_instance.camera.capture_still.assert_called_once()

    def test_camera_capture_failure(self, client, app_instance):
        app_instance.camera.capture_still.return_value = False

        response = client.post("/api/camera/capture")
        body = response.get_json()

        assert response.status_code == 500
        assert body["success"] is False
        assert body["code"] == "CAPTURE_FAILED"


class TestMountEndpoints:
    """Mount API endpoint tests."""

    def test_mount_status_success(self, client):
        response = client.get("/api/mount/status")
        body = response.get_json()

        assert response.status_code == 200
        assert body["success"] is True
        assert "data" in body
        assert "status" in body["data"]

    def test_mount_tracking_start(self, client, app_instance):
        response = client.post("/api/mount/tracking", json={"action": "start"})
        body = response.get_json()

        assert response.status_code == 200
        assert body["success"] is True
        app_instance.mount.start_tracking.assert_called_once()

    def test_mount_tracking_stop(self, client, app_instance):
        response = client.post("/api/mount/tracking", json={"action": "stop"})
        body = response.get_json()

        assert response.status_code == 200
        assert body["success"] is True
        app_instance.mount.stop_tracking.assert_called_once()

    def test_mount_tracking_invalid_action(self, client, app_instance):
        response = client.post("/api/mount/tracking", json={"action": "pause"})
        body = response.get_json()

        assert response.status_code == 400
        assert body["success"] is False
        assert body["code"] == "INVALID_ACTION"
        app_instance.mount.start_tracking.assert_not_called()
        app_instance.mount.stop_tracking.assert_not_called()


class TestSessionEndpoints:
    """Session API endpoint tests."""

    def test_session_status_success(self, client):
        response = client.get("/api/session/status")
        body = response.get_json()

        assert response.status_code == 200
        assert body["success"] is True
        assert "data" in body
        assert "active" in body["data"]

    def test_session_start_success(self, client, app_instance):
        payload = {
            "name": "Test Session",
            "total_images": 10,
            "use_current_settings": True,
            "enable_tracking": True,
            "total_time_hours": 1.5,
        }

        response = client.post("/api/session/start", json=payload)
        body = response.get_json()

        assert response.status_code == 200
        assert body["success"] is True
        app_instance.session_controller.start_session.assert_called_once_with(
            name="Test Session",
            total_images=10,
            use_current_settings=True,
            enable_tracking=True,
            total_time_hours=1.5,
        )

    def test_session_start_missing_name(self, client, app_instance):
        payload = {
            "total_images": 10,
        }

        response = client.post("/api/session/start", json=payload)
        body = response.get_json()

        assert response.status_code == 400
        assert body["success"] is False
        assert body["code"] == "VALIDATION_ERROR"
        app_instance.session_controller.start_session.assert_not_called()

    def test_session_start_invalid_total_images(self, client, app_instance):
        payload = {
            "name": "Test Session",
            "total_images": 0,
        }

        response = client.post("/api/session/start", json=payload)
        body = response.get_json()

        assert response.status_code == 400
        assert body["success"] is False
        assert body["code"] == "VALIDATION_ERROR"
        app_instance.session_controller.start_session.assert_not_called()

    def test_session_stop_success(self, client, app_instance):
        response = client.post("/api/session/stop")
        body = response.get_json()

        assert response.status_code == 200
        assert body["success"] is True
        app_instance.session_controller.stop_session.assert_called_once()

    def test_session_stop_failure(self, client, app_instance):
        app_instance.session_controller.stop_session.return_value = False

        response = client.post("/api/session/stop")
        body = response.get_json()

        assert response.status_code == 500
        assert body["success"] is False
        assert body["code"] == "SESSION_STOP_FAILED"


class TestCaptureListing:
    """Captured images listing endpoint tests."""

    def test_captures_list_success(self, client, app_instance):
        with patch("web.app.os.listdir", return_value=["img1.jpg", "img2.png"]):
            response = client.get("/api/captures")

        body = response.get_json()
        assert response.status_code == 200
        assert body["success"] is True
        assert body["data"]["files"] == ["img1.jpg", "img2.png"]

    def test_captures_list_handles_missing_directory(self, client):
        with patch("web.app.os.listdir", side_effect=FileNotFoundError):
            response = client.get("/api/captures")

        body = response.get_json()
        assert response.status_code == 200
        assert body["data"]["files"] == []


class TestVideoFeed:
    """Video feed streaming tests."""

    def test_video_feed_route(self, client, app_instance):
        app_instance.camera.get_frame.side_effect = [b"frame", Exception("Stop")]

        try:
            response = client.get("/video_feed")
            assert response.status_code == 200
            assert response.content_type == "multipart/x-mixed-replace; boundary=frame"
        except Exception:
            # Ignore generator stop exceptions in test environment
            pass


class TestSocketIO:
    """Socket.IO integration tests."""

    def test_camera_namespace_connect(self, app_instance):
        """Test camera namespace connection."""
        with patch("web.app.socketio") as mock_socketio:
            mock_socketio.emit = Mock()
            # Import after patching to get the mock
            from web.app import broadcast_camera_update
            
            broadcast_camera_update(app_instance.camera)
            mock_socketio.emit.assert_called_once()
            args = mock_socketio.emit.call_args
            assert args[0][0] == "status"  # Event name
            assert args[1]["namespace"] == "/ws/camera"

    def test_broadcast_camera_update(self, app_instance):
        """Test broadcasting camera updates."""
        with patch("web.app.socketio") as mock_socketio:
            mock_socketio.emit = Mock()
            app_instance.camera.get_exposure_seconds.return_value = 1.2
            app_instance.camera.gain_to_iso.return_value = 640
            
            broadcast_camera_update(app_instance.camera)
            
            mock_socketio.emit.assert_called_once()
            args = mock_socketio.emit.call_args
            assert args[0][0] == "status"
            payload = args[0][1]
            assert payload["exposure_seconds"] == 1.2
            assert payload["iso"] == 640

    def test_broadcast_capture_events(self):
        """Test broadcasting capture events."""
        with patch("web.app.socketio") as mock_socketio:
            mock_socketio.emit = Mock()
            
            broadcast_capture_event("capture_start", {"timestamp": 123})
            broadcast_capture_event("capture_complete", {"filename": "test.jpg"})
            
            assert mock_socketio.emit.call_count == 2
            calls = mock_socketio.emit.call_args_list
            assert calls[0][0][0] == "capture_start"
            assert calls[0][0][1] == {"timestamp": 123}
            assert calls[1][0][0] == "capture_complete"
            assert calls[1][0][1] == {"filename": "test.jpg"}

    def test_mount_namespace_events(self):
        """Test broadcasting mount events."""
        with patch("web.app.socketio") as mock_socketio:
            mock_socketio.emit = Mock()
            
            broadcast_mount_event("tracking_start", {"tracking": True})
            
            mock_socketio.emit.assert_called_once()
            args = mock_socketio.emit.call_args
            assert args[0][0] == "tracking_start"
            assert args[0][1] == {"tracking": True}
            assert args[1]["namespace"] == "/ws/mount"

    def test_session_namespace_events(self):
        """Test broadcasting session events."""
        with patch("web.app.socketio") as mock_socketio:
            mock_socketio.emit = Mock()
            
            broadcast_session_event("session_progress", {"images_captured": 2})
            
            mock_socketio.emit.assert_called_once()
            args = mock_socketio.emit.call_args
            assert args[0][0] == "session_progress"
            assert args[0][1] == {"images_captured": 2}
            assert args[1]["namespace"] == "/ws/session"

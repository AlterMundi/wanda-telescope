#!/bin/bash
# WANDA Telescope Test Structure Generator - One-liner command
# Copy and paste this entire command into your terminal:

mkdir -p tests/{unit/{test_camera,test_mount,test_utils},integration,web} && \
echo '"""Shared pytest fixtures for WANDA telescope testing."""
import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_camera():
    """Create a mock camera instance."""
    from camera.implementations.mock_camera import MockCamera
    camera = MockCamera()
    camera.initialize()
    return camera

@pytest.fixture
def mock_mount():
    """Create a mock mount instance."""
    from mount.implementations.mock_mount import MockMount
    mount = MockMount()
    mount.initialize()
    return mount

@pytest.fixture
def mock_gpio():
    """Mock RPi.GPIO module."""
    with patch.dict("sys.modules", {"RPi": Mock(), "RPi.GPIO": Mock()}):
        yield Mock()

@pytest.fixture
def mock_picamera2():
    """Mock picamera2 module."""
    mock_picamera = Mock()
    mock_picamera.Picamera2 = Mock()
    with patch.dict("sys.modules", {"picamera2": mock_picamera}):
        yield mock_picamera

@pytest.fixture
def flask_app(mock_camera):
    """Create a Flask app instance for testing."""
    from web.app import WandaApp
    app = WandaApp(camera=mock_camera)
    app.app.config["TESTING"] = True
    return app.app

@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()' > tests/conftest.py && \
echo '"""Unit tests for camera factory functionality."""
import pytest
from unittest.mock import patch, Mock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from camera.factory import CameraFactory
from camera.implementations.mock_camera import MockCamera

class TestCameraFactory:
    def test_create_camera_returns_mock_when_no_hardware(self):
        """Test that factory returns mock camera when no hardware is available."""
        with patch("camera.factory.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value.isOpened.return_value = False
            with patch.dict("sys.modules", {"picamera2": None}):
                camera = CameraFactory.create_camera()
                assert isinstance(camera, MockCamera)

    def test_list_available_cameras(self):
        """Test listing available cameras."""
        cameras = CameraFactory.list_available_cameras()
        assert isinstance(cameras, list)' > tests/unit/test_camera/test_factory.py && \
echo '"""Unit tests for mock camera implementation."""
import pytest
import numpy as np
from unittest.mock import Mock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from camera.implementations.mock_camera import MockCamera

class TestMockCamera:
    def test_mock_camera_initialization(self):
        """Test mock camera initializes correctly."""
        camera = MockCamera()
        assert camera.started is False
        assert camera.options == {}

    def test_start_stop(self):
        """Test starting and stopping the camera."""
        camera = MockCamera()
        camera.start()
        assert camera.started is True
        camera.stop()
        assert camera.started is False

    def test_capture_array(self):
        """Test capturing array."""
        camera = MockCamera()
        result = camera.capture_array()
        assert isinstance(result, np.ndarray)' > tests/unit/test_camera/test_mock_camera.py && \
echo '"""Unit tests for USB camera implementation."""
import pytest
from unittest.mock import Mock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from camera.implementations.usb_camera import USBCamera

class TestUSBCamera:
    def test_usb_camera_initialization(self):
        """Test USB camera initializes correctly."""
        camera = USBCamera()
        assert hasattr(camera, "camera")
        assert hasattr(camera, "exposure_us")

    def test_configure(self):
        """Test configuring the camera."""
        camera = USBCamera()
        camera.configure({"test": "value"})  # Should not raise exception' > tests/unit/test_camera/test_usb_camera.py && \
echo '"""Unit tests for Pi camera implementation."""
import pytest
from unittest.mock import Mock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

class TestPiCamera:
    def test_pi_camera_with_mocked_hardware(self, mock_picamera2):
        """Test Pi camera with mocked picamera2."""
        from camera.implementations.pi_camera import PiCamera
        camera = PiCamera()
        assert hasattr(camera, "camera")
        assert hasattr(camera, "exposure_us")

    def test_create_configurations(self, mock_picamera2):
        """Test creating camera configurations."""
        from camera.implementations.pi_camera import PiCamera
        camera = PiCamera()
        
        preview_config = camera.create_preview_configuration()
        assert isinstance(preview_config, dict)
        
        still_config = camera.create_still_configuration()
        assert isinstance(still_config, dict)' > tests/unit/test_camera/test_pi_camera.py && \
echo '"""Unit tests for mount factory."""
import pytest
from unittest.mock import Mock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from mount.factory import MountFactory
from mount.implementations.mock_mount import MockMount

class TestMountFactory:
    def test_create_mount_returns_mock_when_gpio_unavailable(self):
        """Test that factory returns mock mount when RPi.GPIO is not available."""
        with patch.dict("sys.modules", {"RPi": None, "RPi.GPIO": None}):
            mount = MountFactory.create_mount()
            assert isinstance(mount, MockMount)' > tests/unit/test_mount/test_factory.py && \
echo '"""Unit tests for mock mount implementation."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from mount.implementations.mock_mount import MockMount

class TestMockMount:
    def test_mock_mount_initialization(self):
        """Test mock mount initializes correctly."""
        mount = MockMount()
        assert mount.tracking is False
        assert mount.direction is True
        assert mount.speed == 1.0

    def test_start_stop_tracking(self):
        """Test starting and stopping tracking."""
        mount = MockMount()
        mount.initialize()
        mount.start_tracking()
        assert mount.tracking is True
        mount.stop_tracking()
        assert mount.tracking is False' > tests/unit/test_mount/test_mock_mount.py && \
echo '"""Unit tests for Pi mount implementation."""
import pytest
from unittest.mock import Mock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

class TestPiMount:
    def test_pi_mount_with_mocked_gpio(self, mock_gpio):
        """Test Pi mount with mocked GPIO."""
        from mount.implementations.pi_mount import PiMount
        mount = PiMount()
        assert hasattr(mount, "motor_pins")
        assert hasattr(mount, "tracking")' > tests/unit/test_mount/test_pi_mount.py && \
echo '"""Unit tests for storage utilities."""
import pytest
import tempfile
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.storage import get_capture_dir, get_free_space, format_space

class TestStorageUtils:
    def test_get_capture_dir(self):
        """Test capture directory selection."""
        capture_dir = get_capture_dir()
        assert isinstance(capture_dir, str)
        assert len(capture_dir) > 0

    def test_get_free_space(self):
        """Test getting free space."""
        free_space = get_free_space(".")
        assert isinstance(free_space, int)
        assert free_space >= 0

    def test_format_space(self):
        """Test space formatting."""
        assert format_space(1024) == "1.0 KB"
        assert format_space(1024 * 1024) == "1.0 MB"' > tests/unit/test_utils/test_storage.py && \
echo '"""Unit tests for configuration."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config

class TestConfig:
    def test_config_values_exist(self):
        """Test that required config values exist."""
        assert hasattr(config, "DEFAULT_EXPOSURE_US")
        assert hasattr(config, "DEFAULT_GAIN")
        assert hasattr(config, "HOST")
        assert hasattr(config, "PORT")

    def test_config_types(self):
        """Test config value types."""
        assert isinstance(config.DEFAULT_EXPOSURE_US, int)
        assert isinstance(config.HOST, str)
        assert isinstance(config.PORT, int)' > tests/unit/test_config.py && \
echo '"""Integration tests between camera and mount systems."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from camera.factory import CameraFactory
from mount.factory import MountFactory

class TestCameraMountIntegration:
    def test_factory_creates_compatible_instances(self):
        """Test that factories create compatible instances."""
        camera = CameraFactory.create_camera()
        mount = MountFactory.create_mount()
        
        assert camera is not None
        assert mount is not None
        
        camera.initialize()
        mount.initialize()
        
        camera.cleanup()
        mount.cleanup()

    def test_concurrent_operation(self):
        """Test camera and mount can operate concurrently."""
        camera = CameraFactory.create_camera()
        mount = MountFactory.create_mount()
        
        camera.initialize()
        mount.initialize()
        
        camera.start()
        mount.start_tracking()
        
        assert camera.started is True
        assert mount.tracking is True
        
        mount.stop_tracking()
        camera.stop()
        
        camera.cleanup()
        mount.cleanup()' > tests/integration/test_camera_mount_integration.py && \
echo '"""Integration tests for web and camera systems."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.app import WandaApp
from camera.factory import CameraFactory

class TestWebCameraIntegration:
    def test_web_app_with_camera(self):
        """Test web app integrates with camera system."""
        camera = CameraFactory.create_camera()
        camera.initialize()
        
        app = WandaApp(camera=camera)
        assert app.camera == camera
        
        with app.app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200
        
        app.cleanup()' > tests/integration/test_web_camera_integration.py && \
echo '"""Unit tests for web application."""
import pytest
import json
from unittest.mock import Mock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.app import WandaApp

class TestWandaApp:
    def test_wanda_app_initialization(self, mock_camera):
        """Test WandaApp initializes correctly."""
        app = WandaApp(camera=mock_camera)
        assert app.camera == mock_camera
        assert app.mount is not None' > tests/web/test_app.py && \
echo '"""Unit tests for web routes."""
import pytest
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestWebRoutes:
    def test_index_get(self, client):
        """Test GET request to index page."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Wanda Telescope" in response.data

    def test_video_feed(self, client):
        """Test video feed endpoint."""
        response = client.get("/video_feed")
        assert response.status_code == 200

    def test_capture_still(self, client):
        """Test capture still endpoint."""
        response = client.post("/capture_still")
        assert response.status_code in [200, 302]

    def test_start_tracking(self, client):
        """Test start tracking endpoint."""
        response = client.post("/start_tracking")
        assert response.status_code in [200, 302]' > tests/web/test_routes.py && \
echo '"""Unit tests for web templates."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestWebTemplates:
    def test_index_template_renders(self, client):
        """Test that index template renders correctly."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Camera Controls" in response.data
        assert b"Mount Controls" in response.data

    def test_template_has_required_elements(self, client):
        """Test that template contains required UI elements."""
        response = client.get("/")
        assert b"video_feed" in response.data
        assert b"capture_still" in response.data
        assert b"start_tracking" in response.data' > tests/web/test_templates.py && \
find tests -name "*.py" -exec touch {}/__init__.py \; 2>/dev/null || true && \
echo '# Test requirements
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-flask>=1.2.0
responses>=0.23.0' > requirements-test.txt && \
echo '[tool:pytest]
testpaths = tests
python_files = test_*.py
addopts = --cov=camera --cov=mount --cov=web --cov=utils -v
markers = 
    unit: Unit tests
    integration: Integration tests
    web: Web interface tests' > pytest.ini && \
echo "🔭 WANDA Test Structure Generated Successfully!" && \
echo "📁 Created $(find tests -name '*.py' | wc -l) test files in organized structure" && \
echo "🚀 Next steps:" && \
echo "   1. pip install -r requirements-test.txt" && \
echo "   2. pytest tests/ --cov" && \
echo "   3. Start writing your specific tests!" && \
ls -la tests/ && \
echo "✅ Test structure ready for WANDA telescope project!"

"""
Pytest configuration file that sets up the test environment.
"""
import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# This ensures the path is set up before any tests are imported

@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_capture_dir():
    """Create a temporary directory for test captures that gets cleaned up."""
    temp_dir = tempfile.mkdtemp(prefix="test_captures_")
    yield temp_dir
    # Clean up the temporary directory after tests
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        # Log but don't fail if cleanup fails
        print(f"Warning: Could not clean up test capture directory {temp_dir}: {e}")

@pytest.fixture
def mock_camera(test_capture_dir):
    """Create a mock camera instance with test capture directory."""
    from camera.implementations.mock_camera import MockCamera
    camera = MockCamera(capture_dir=test_capture_dir)
    # Don't call initialize() here - let tests do it if needed
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
    mock_picamera.encoders = Mock()
    mock_picamera.outputs = Mock()
    with patch.dict("sys.modules", {"picamera2": mock_picamera}):
        yield mock_picamera

@pytest.fixture
def flask_app(test_capture_dir):
    """Create a Flask app instance for testing."""
    from web.app import WandaApp
    from camera.implementations.mock_camera import MockCamera
    
    # Create camera with test capture directory
    camera = MockCamera(capture_dir=test_capture_dir)
    app = WandaApp(camera=camera)
    app.app.config["TESTING"] = True
    return app.app

@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()
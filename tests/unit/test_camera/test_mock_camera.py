"""Unit tests for mock camera implementation."""
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
        assert isinstance(result, np.ndarray)

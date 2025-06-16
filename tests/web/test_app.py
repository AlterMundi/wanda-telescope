"""Unit tests for web application."""
import pytest
import json
from unittest.mock import Mock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.app import WandaApp

class TestWandaApp:
    def test_wanda_app_initialization(self):
        """Test WandaApp initializes correctly."""
        from camera.implementations.mock_camera import MockCamera
        camera = MockCamera()
        
        app = WandaApp(camera=camera)
        assert app.camera == camera
        assert app.mount is not None
"""Integration tests for web and camera systems."""
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
        
        app.cleanup()

"""Integration tests between camera and mount systems."""
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
        mount.cleanup()

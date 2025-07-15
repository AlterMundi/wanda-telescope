"""
Integration tests for camera parameters.
These tests verify that camera settings are properly applied to the hardware.
Note: These tests may take longer to run as they test actual camera functionality.
"""
import pytest
import time
import os
import tempfile
import shutil
import math
from unittest.mock import Mock, patch
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from camera import CameraFactory
from web.app import WandaApp


class TestCameraParameterIntegration:
    """Integration tests for camera parameter application."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary capture directory
        self.test_capture_dir = tempfile.mkdtemp()
        
        # Create camera instance
        self.camera = CameraFactory.create_camera()
        self.camera.capture_dir = self.test_capture_dir
        
        # Create web app instance
        self.app = WandaApp(camera=self.camera)
        
        # Initialize camera
        self.camera.initialize()
        self.camera.start()
    
    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'camera'):
            self.camera.cleanup()
        if hasattr(self, 'test_capture_dir') and os.path.exists(self.test_capture_dir):
            shutil.rmtree(self.test_capture_dir)
    
    def test_exposure_time_application(self):
        """Test that exposure time is properly applied to camera."""
        # Test various exposure times
        test_exposures = [0.1, 1.0, 5.0, 30.0, 300.0]
        
        for exposure_seconds in test_exposures:
            # Set exposure time
            exposure_us = int(exposure_seconds * 1000000)
            self.camera.exposure_us = exposure_us
            self.camera.update_camera_settings()
            
            # Verify exposure was set
            actual_exposure = self.camera.get_exposure_seconds()
            assert abs(actual_exposure - exposure_seconds) < 0.1, \
                f"Expected {exposure_seconds}s, got {actual_exposure}s"
            
            # Test that the camera actually respects the exposure time
            # by measuring capture time for longer exposures
            if exposure_seconds >= 1.0:
                start_time = time.time()
                self.camera.capture_still()
                capture_time = time.time() - start_time
                
                # Allow some tolerance for processing overhead
                assert capture_time >= exposure_seconds * 0.8, \
                    f"Capture took {capture_time}s, expected at least {exposure_seconds * 0.8}s"
    
    def test_iso_sensitivity_application(self):
        """Test that ISO sensitivity is properly applied to camera."""
        # Test various ISO values
        test_isos = [20, 100, 400, 800, 1600]
        
        for iso in test_isos:
            # Set ISO
            gain = self.camera.iso_to_gain(iso)
            self.camera.gain = gain
            self.camera.update_camera_settings()
            
            # Verify gain was set
            actual_iso = self.camera.gain_to_iso(self.camera.gain)
            assert abs(actual_iso - iso) < 50, \
                f"Expected ISO {iso}, got {actual_iso}"
    
    def test_night_vision_mode_application(self):
        """Test that night vision mode is properly applied."""
        # Test night vision mode enabled
        self.camera.night_vision_mode = True
        self.camera.night_vision_intensity = 40.0
        self.camera.update_camera_settings()
        
        # Verify night vision settings were applied
        assert self.camera.use_digital_gain == True
        assert self.camera.digital_gain == 40.0
        
        # Test night vision mode disabled
        self.camera.night_vision_mode = False
        self.camera.update_camera_settings()
        
        # Verify night vision settings were disabled
        assert self.camera.use_digital_gain == False
        assert self.camera.digital_gain == 1.0
    
    def test_night_vision_intensity_range(self):
        """Test night vision intensity across the full range."""
        # Test minimum intensity
        self.camera.night_vision_mode = True
        self.camera.night_vision_intensity = 1.0
        self.camera.update_camera_settings()
        assert self.camera.digital_gain == 1.0
        
        # Test maximum intensity
        self.camera.night_vision_intensity = 80.0
        self.camera.update_camera_settings()
        assert self.camera.digital_gain == 80.0
        
        # Test middle intensity
        self.camera.night_vision_intensity = 40.0
        self.camera.update_camera_settings()
        assert self.camera.digital_gain == 40.0
    
    def test_performance_settings_application(self):
        """Test that performance settings are properly applied."""
        # Test different performance modes
        test_modes = [0, 2, 5]  # High Quality, Balanced, Lowest CPU
        
        for mode in test_modes:
            self.camera.skip_frames = mode
            self.camera.update_camera_settings()
            
            # Verify skip_frames was set
            assert self.camera.skip_frames == mode
    
    def test_web_app_parameter_handling(self):
        """Test that web app properly handles parameter updates."""
        # Test exposure time update through web app
        with self.app.app.test_request_context('/', method='POST', data={
            'exposure': '1000',  # Maximum exposure (300s)
            'iso': '1000',  # Maximum ISO (1600)
            'night_vision_mode': 'on',
            'night_vision_intensity': '80.0',
            'performance': '5'
        }):
            self.app._handle_post_request()
            
            # Verify settings were applied
            assert abs(self.camera.get_exposure_seconds() - 300.0) < 1.0
            assert self.camera.gain_to_iso(self.camera.gain) >= 1600
            assert self.camera.night_vision_mode == True
            assert self.camera.night_vision_intensity == 80.0
            assert self.camera.skip_frames == 5
    
    def test_parameter_persistence(self):
        """Test that parameters persist across multiple updates."""
        # Set initial parameters
        self.camera.exposure_us = 5000000  # 5 seconds
        self.camera.gain = 2.0  # ISO 200
        self.camera.night_vision_mode = True
        self.camera.night_vision_intensity = 20.0
        self.camera.update_camera_settings()
        
        # Verify initial settings
        assert abs(self.camera.get_exposure_seconds() - 5.0) < 0.1
        assert self.camera.gain_to_iso(self.camera.gain) == 200
        assert self.camera.night_vision_mode == True
        assert self.camera.night_vision_intensity == 20.0
        
        # Update some parameters
        self.camera.exposure_us = 10000000  # 10 seconds
        self.camera.night_vision_intensity = 40.0
        self.camera.update_camera_settings()
        
        # Verify updated settings and persistence of unchanged settings
        assert abs(self.camera.get_exposure_seconds() - 10.0) < 0.1
        assert self.camera.gain_to_iso(self.camera.gain) == 200  # Should persist
        assert self.camera.night_vision_mode == True  # Should persist
        assert self.camera.night_vision_intensity == 40.0  # Should be updated
    
    def test_parameter_validation(self):
        """Test that parameters are properly validated and clamped."""
        # Test exposure time validation
        self.camera.exposure_us = -1000  # Invalid negative value
        self.camera.update_camera_settings()
        assert self.camera.exposure_us >= 0  # Should be clamped
        
        # Test ISO validation
        self.camera.gain = -1.0  # Invalid negative gain
        self.camera.update_camera_settings()
        assert self.camera.gain >= 0  # Should be clamped
        
        # Test night vision intensity validation
        self.camera.night_vision_intensity = 100.0  # Above maximum
        self.camera.update_camera_settings()
        assert self.camera.night_vision_intensity <= 80.0  # Should be clamped
        
        self.camera.night_vision_intensity = 0.5  # Below minimum
        self.camera.update_camera_settings()
        assert self.camera.night_vision_intensity >= 1.0  # Should be clamped
    
    def test_capture_with_different_settings(self):
        """Test that captures work correctly with different parameter combinations."""
        # Test capture with default settings
        success = self.camera.capture_still()
        assert success == True
        
        # Test capture with long exposure
        self.camera.exposure_us = 5000000  # 5 seconds
        self.camera.update_camera_settings()
        success = self.camera.capture_still()
        assert success == True
        
        # Test capture with high ISO
        self.camera.gain = 8.0  # ISO 800
        self.camera.update_camera_settings()
        success = self.camera.capture_still()
        assert success == True
        
        # Test capture with night vision mode
        self.camera.night_vision_mode = True
        self.camera.night_vision_intensity = 40.0
        self.camera.update_camera_settings()
        success = self.camera.capture_still()
        assert success == True
    
    def test_frame_processing_with_night_vision(self):
        """Test that night vision mode properly processes frames."""
        # Test frame processing without night vision
        self.camera.night_vision_mode = False
        self.camera.update_camera_settings()
        
        frame1 = self.camera.capture_array()
        assert frame1 is not None
        
        # Test frame processing with night vision
        self.camera.night_vision_mode = True
        self.camera.night_vision_intensity = 2.0
        self.camera.update_camera_settings()
        
        frame2 = self.camera.capture_array()
        assert frame2 is not None
        
        # The frames should be different due to digital gain
        # (Note: This is a basic test - actual brightness differences may vary)
        assert frame1.shape == frame2.shape
    
    def test_parameter_boundaries(self):
        """Test parameter behavior at boundary values."""
        # Test minimum exposure time
        self.camera.exposure_us = 100  # 0.0001 seconds
        self.camera.update_camera_settings()
        assert self.camera.exposure_us >= 100
        
        # Test maximum exposure time
        self.camera.exposure_us = 300000000  # 300 seconds
        self.camera.update_camera_settings()
        assert self.camera.exposure_us <= 300000000
        
        # Test minimum ISO
        self.camera.gain = 0.2  # ISO 20
        self.camera.update_camera_settings()
        assert self.camera.gain >= 0.2
        
        # Test maximum ISO
        self.camera.gain = 16.0  # ISO 1600
        self.camera.update_camera_settings()
        assert self.camera.gain <= 16.0
        
        # Test minimum night vision intensity
        self.camera.night_vision_intensity = 1.0
        self.camera.update_camera_settings()
        assert self.camera.night_vision_intensity >= 1.0
        
        # Test maximum night vision intensity
        self.camera.night_vision_intensity = 80.0
        self.camera.update_camera_settings()
        assert self.camera.night_vision_intensity <= 80.0


class TestCameraParameterStress:
    """Stress tests for camera parameters."""
    
    def setup_method(self):
        """Set up test environment."""
        self.test_capture_dir = tempfile.mkdtemp()
        self.camera = CameraFactory.create_camera()
        self.camera.capture_dir = self.test_capture_dir
        self.camera.initialize()
        self.camera.start()
    
    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'camera'):
            self.camera.cleanup()
        if hasattr(self, 'test_capture_dir') and os.path.exists(self.test_capture_dir):
            shutil.rmtree(self.test_capture_dir)
    
    def test_rapid_parameter_changes(self):
        """Test rapid parameter changes to ensure stability."""
        for i in range(10):
            # Rapidly change exposure time
            exposure_seconds = 0.1 + (i * 0.5)
            self.camera.exposure_us = int(exposure_seconds * 1000000)
            
            # Rapidly change ISO
            iso = 20 + (i * 100)
            self.camera.gain = self.camera.iso_to_gain(iso)
            
            # Rapidly change night vision intensity
            intensity = 1.0 + (i * 8.0)
            self.camera.night_vision_intensity = intensity
            
            # Update settings
            self.camera.update_camera_settings()
            
            # Verify settings were applied
            actual_exposure = self.camera.get_exposure_seconds()
            assert abs(actual_exposure - exposure_seconds) < 0.1
            
            actual_iso = self.camera.gain_to_iso(self.camera.gain)
            assert abs(actual_iso - iso) < 100
            
            # Small delay to allow camera to process
            time.sleep(0.1)
    
    def test_concurrent_parameter_access(self):
        """Test concurrent access to camera parameters."""
        import threading
        
        def change_exposure():
            for i in range(5):
                self.camera.exposure_us = 1000000 * (i + 1)  # 1-5 seconds
                self.camera.update_camera_settings()
                time.sleep(0.1)
        
        def change_iso():
            for i in range(5):
                self.camera.gain = 1.0 + (i * 2.0)  # 1.0, 3.0, 5.0, 7.0, 9.0
                self.camera.update_camera_settings()
                time.sleep(0.1)
        
        def change_night_vision():
            for i in range(5):
                self.camera.night_vision_intensity = 10.0 + (i * 15.0)  # 10, 25, 40, 55, 70
                self.camera.update_camera_settings()
                time.sleep(0.1)
        
        # Run parameter changes concurrently
        threads = [
            threading.Thread(target=change_exposure),
            threading.Thread(target=change_iso),
            threading.Thread(target=change_night_vision)
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify camera is still functional
        success = self.camera.capture_still()
        assert success == True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 
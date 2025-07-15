#!/usr/bin/env python3
"""
Debug script to test exposure settings on the camera.
"""
import time
import logging
from camera import CameraFactory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_exposure_settings():
    """Test exposure settings directly on the camera."""
    print("=== Camera Exposure Debug Test ===")
    
    # Create camera
    camera = CameraFactory.create_camera()
    camera.initialize()
    camera.start()
    
    print(f"Camera type: {type(camera).__name__}")
    if hasattr(camera, 'status'):
        print(f"Camera status: {camera.status}")
    else:
        print("Camera status: Not available")
    
    # Test different exposure times
    test_exposures = [0.1, 1.0, 5.0, 10.0]
    
    for exposure_seconds in test_exposures:
        print(f"\n--- Testing {exposure_seconds}s exposure ---")
        
        # Set exposure
        exposure_us = int(exposure_seconds * 1000000)
        camera.exposure_us = exposure_us
        camera.update_camera_settings()
        
        # Verify exposure was set
        actual_exposure = camera.get_exposure_seconds()
        print(f"Requested: {exposure_seconds}s, Actual: {actual_exposure}s")
        
        # Test capture time
        if exposure_seconds >= 1.0:
            print(f"Capturing with {exposure_seconds}s exposure...")
            start_time = time.time()
            success = camera.capture_still()
            capture_time = time.time() - start_time
            print(f"Capture success: {success}")
            print(f"Capture took: {capture_time:.3f}s")
            print(f"Expected at least: {exposure_seconds * 0.8:.3f}s")
            
            if capture_time < exposure_seconds * 0.8:
                print("⚠️  WARNING: Capture was too fast! Exposure not applied correctly.")
            else:
                print("✅ Exposure appears to be working correctly.")
    
    # Clean up
    camera.cleanup()
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_exposure_settings() 
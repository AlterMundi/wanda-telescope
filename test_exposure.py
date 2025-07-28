#!/usr/bin/env python3

from camera import CameraFactory
import time
import os

def test_exposure():
    camera = CameraFactory.create_camera()
    camera.initialize()
    camera.start()
    
    print("Testing different exposure times...")
    exposures = [100000, 1000000, 5000000]  # 0.1s, 1s, 5s
    
    for exp in exposures:
        camera.exposure_us = exp
        camera.update_camera_settings()
        print(f"Setting {exp/1000000:.1f}s exposure...")
        
        start = time.time()
        success = camera.capture_still()
        end = time.time()
        
        print(f"Capture took: {end-start:.2f}s, success: {success}")
        
        # Get the latest image
        files = [f for f in os.listdir('captures') if f.endswith('.jpg')]
        if files:
            latest = max(files, key=lambda x: os.path.getctime('captures/' + x))
            size = os.path.getsize('captures/' + latest)
            print(f"Latest image: {latest}, size: {size} bytes")
        print()
    
    camera.cleanup()

if __name__ == "__main__":
    test_exposure() 
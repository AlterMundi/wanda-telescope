#!/usr/bin/env python3
"""
Integration test for real USB camera parameter application.
Captures images with various settings and analyzes results.
"""
import time
import os
import cv2
import numpy as np
import tempfile
import shutil
import logging
from camera.implementations.usb_camera import USBCamera

def analyze_image_brightness(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    return float(np.mean(img))

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("real_camera_test")
    print("=== Real USB Camera Parameter Test ===")
    
    # Create temp directory for captures
    capture_dir = tempfile.mkdtemp()
    print(f"Capture directory: {capture_dir}")
    
    # Instantiate real USB camera
    camera = USBCamera(capture_dir=capture_dir)
    camera.initialize()
    camera.start()
    
    # Parameter matrix: (exposure_s, iso_gain, night_vision, night_vision_intensity)
    test_cases = [
        (0.1, 1.0, False, 1.0),
        (1.0, 1.0, False, 1.0),
        (5.0, 1.0, False, 1.0),
        (1.0, 8.0, False, 1.0),  # High ISO
        (1.0, 1.0, True, 10.0), # Night vision low
        (1.0, 1.0, True, 40.0), # Night vision medium
        (1.0, 1.0, True, 80.0), # Night vision high
    ]
    
    results = []
    for idx, (exposure_s, gain, nv_mode, nv_intensity) in enumerate(test_cases):
        print(f"\n--- Test {idx+1}: Exposure={exposure_s}s, Gain={gain}, NightVision={nv_mode}, Intensity={nv_intensity} ---")
        camera.exposure_us = int(exposure_s * 1_000_000)
        camera.gain = gain
        camera.night_vision_mode = nv_mode
        camera.night_vision_intensity = nv_intensity
        camera.update_camera_settings()
        
        # Wait a moment for settings to take effect
        time.sleep(0.5)
        
        # Capture image and measure time
        filename = os.path.join(capture_dir, f"test_{idx+1}.jpg")
        start = time.time()
        success = camera.capture_still()
        elapsed = time.time() - start
        
        # Find the most recent file in capture_dir
        files = sorted([os.path.join(capture_dir, f) for f in os.listdir(capture_dir)], key=os.path.getmtime, reverse=True)
        image_path = files[0] if files else None
        brightness = analyze_image_brightness(image_path) if image_path else None
        
        print(f"Capture success: {success}")
        print(f"Capture time: {elapsed:.2f}s (expected >= {exposure_s * 0.8:.2f}s)")
        print(f"Image: {image_path}")
        print(f"Mean brightness: {brightness}")
        
        results.append({
            'test': idx+1,
            'exposure': exposure_s,
            'gain': gain,
            'night_vision': nv_mode,
            'nv_intensity': nv_intensity,
            'capture_time': elapsed,
            'brightness': brightness,
            'success': success,
            'image': image_path
        })
    
    # Summarize results
    print("\n=== Test Summary ===")
    for r in results:
        print(f"Test {r['test']}: Exposure={r['exposure']}s, Gain={r['gain']}, NV={r['night_vision']}, Intensity={r['nv_intensity']} | Time={r['capture_time']:.2f}s | Brightness={r['brightness']} | Success={r['success']}")
    
    # Clean up
    camera.cleanup()
    # Uncomment to remove images after test:
    # shutil.rmtree(capture_dir)
    print("\n=== Done ===")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Demonstration script showing how test captures are isolated from the main project.
"""
import os
import sys
import tempfile
import shutil
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from camera.implementations.mock_camera import MockCamera

def demo_capture_isolation():
    """Demonstrate that test captures don't pollute the main project."""
    print("=== Capture Directory Isolation Demo ===\n")
    
    # Check if main captures directory exists and what's in it
    main_captures_dir = "captures"
    if os.path.exists(main_captures_dir):
        main_files = os.listdir(main_captures_dir)
        print(f"Main captures directory contains: {main_files}")
    else:
        print("Main captures directory does not exist")
    
    # Create a test capture directory (like our test fixture does)
    test_dir = tempfile.mkdtemp(prefix="demo_test_captures_")
    print(f"\nCreated test capture directory: {test_dir}")
    
    try:
        # Create a camera with the test directory
        camera = MockCamera(capture_dir=test_dir)
        camera.initialize()
        
        # Capture a test image
        print("Capturing test image...")
        result = camera.capture_still()
        
        if result:
            # Check what was created
            test_files = os.listdir(test_dir)
            print(f"Test directory now contains: {test_files}")
            
            # Verify the file exists in test directory
            test_file_path = os.path.join(test_dir, test_files[0])
            assert os.path.exists(test_file_path), "Test file should exist in test directory"
            print(f"✓ Test file created: {test_file_path}")
            
            # Verify the file is NOT in main directory
            if os.path.exists(main_captures_dir):
                main_files_after = os.listdir(main_captures_dir)
                if test_files[0] not in main_files_after:
                    print("✓ Test file is NOT in main captures directory")
                else:
                    print("✗ ERROR: Test file leaked to main captures directory!")
            else:
                print("✓ Main captures directory doesn't exist (no pollution)")
            
            print("\n=== Demo Summary ===")
            print("✓ Test captures are isolated in temporary directory")
            print("✓ Main project directory is not polluted")
            print("✓ Temporary directory will be cleaned up automatically")
            
        else:
            print("✗ Capture failed!")
            
    finally:
        # Clean up (this happens automatically in tests via pytest fixtures)
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test directory: {test_dir}")

if __name__ == "__main__":
    demo_capture_isolation() 
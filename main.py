"""
Main entry point for Wanda astrophotography system.
Initializes all components and starts the web server.
"""
import logging
import sys
import signal
from web.app import WandaApp
from camera import CameraFactory

# Configure logging
def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('wanda.log')
        ]
    )
    return logging.getLogger(__name__)

def initialize_camera():
    """Initialize the camera system.
    
    Returns:
        The initialized camera instance or None if initialization fails.
    """
    try:
        # Create camera instance using factory
        camera = CameraFactory.create_camera()
        
        # Initialize the camera hardware
        camera.initialize()
        
        # Configure camera for preview
        preview_config = camera.create_preview_configuration()
        camera.configure(preview_config)
        
        # Start the camera
        camera.start()
        
        # Save the original camera state for restoration on exit
        camera.save_original_state()
        
        print("Camera initialized successfully")
        return camera
    except Exception as e:
        print(f"Failed to initialize camera: {e}")
        return None

def signal_handler(sig, frame):
    """Handle termination signals."""
    print("Received termination signal, shutting down...")
    if 'camera' in globals() and camera is not None:
        try:
            # Restore original camera state before cleanup
            camera.restore_original_state()
            camera.stop()
            camera.cleanup()
            print("Camera restored to original state and cleaned up")
        except Exception as e:
            print(f"Error during camera cleanup: {e}")
    sys.exit(0)

def main():
    """Main application entry point."""
    print("Starting Wanda Astrophotography System")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize camera
    global camera
    camera = initialize_camera()
    
    # Create and run the web application
    app = WandaApp(camera=camera)
    try:
        app.run()
    except Exception as e:
        print(f"Error running application: {e}")
        if camera is not None:
            try:
                # Restore original camera state before cleanup
                camera.restore_original_state()
                camera.stop()
                camera.cleanup()
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    logger = setup_logging()
    main()
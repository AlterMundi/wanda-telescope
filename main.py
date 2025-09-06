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
    # Create a more robust logging configuration
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler with error handling
    try:
        file_handler = logging.FileHandler('wanda.log')
        file_handler.setFormatter(formatter)
        handlers = [console_handler, file_handler]
    except Exception as e:
        print(f"Warning: Could not create log file handler: {e}")
        handlers = [console_handler]
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # Force reconfiguration to avoid conflicts
    )
    
    # Ensure all handlers are properly configured
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
    
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
        print("\n" + "="*60)
        print("CAMERA INITIALIZATION FAILED")
        print("="*60)
        print(f"\n{e}\n")
        print("="*60)
        print("\nThe application will continue without camera functionality.")
        print("Please fix the hardware issue and restart the application.\n")
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
    
    # Flush all logging handlers before exit
    try:
        logging.shutdown()
    except Exception as e:
        print(f"Error during logging shutdown: {e}")
    
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
    if camera is None:
        print("Cannot start web application without camera.")
        print("Please fix the camera issue and restart the application.")
        sys.exit(1)

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
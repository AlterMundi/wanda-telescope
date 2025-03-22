"""
Main entry point for Wanda astrophotography system.
Initializes all components and starts the web server.
"""
import logging
import sys
import signal
from web.app import WandaApp

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

def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info("Received termination signal, shutting down...")
    sys.exit(0)

def main():
    """Main application entry point."""
    logger.info("Starting Wanda Astrophotography System")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run the web application
    app = WandaApp()
    try:
        app.run()
    except Exception as e:
        logger.error(f"Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger = setup_logging()
    main()
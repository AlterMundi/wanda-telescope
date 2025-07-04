"""
Session controller for managing capture sessions with multiple images.
"""
import os
import json
import time
import logging
import threading
import glob
from datetime import datetime
from typing import Optional, Dict, Any
from .exceptions import (
    SessionError,
    SessionAlreadyRunningError,
    SessionConfigurationError
)

logger = logging.getLogger(__name__)

class SessionController:
    """Controller class for managing capture sessions."""
    
    def __init__(self, camera, mount, base_capture_dir="captures"):
        """Initialize the session controller.
        
        Args:
            camera: Camera instance (from camera factory)
            mount: Mount controller instance
            base_capture_dir: Base directory for storing captures
        """
        self.camera = camera
        self.mount = mount
        self.base_capture_dir = base_capture_dir
        
        # Session state
        self.current_session = None
        self.session_thread = None
        self.session_running = False
        
        # Session configuration
        self.session_config = {
            'name': '',
            'total_images': 0,
            'use_current_settings': True,
            'enable_tracking': False,
            'start_time': None,
            'end_time': None,
            'images_captured': 0,
            'session_dir': '',
            'status': 'idle'
        }
        
        logger.info("Session controller initialized")
    
    def start_session(self, name: str, total_images: int,
                     use_current_settings: bool = True, enable_tracking: bool = False) -> bool:
        """Start a new capture session.
        
        Args:
            name: Session name (used for directory naming)
            total_images: Total number of images to capture
            use_current_settings: Whether to use current camera settings
            enable_tracking: Whether to enable mount tracking during session
            
        Returns:
            bool: True if session started successfully
            
        Raises:
            SessionAlreadyRunningError: If a session is already running
            SessionConfigurationError: If configuration is invalid
        """
        if self.session_running:
            raise SessionAlreadyRunningError("A session is already running")
        
        # Validate configuration
        if not name or not name.strip():
            raise SessionConfigurationError("Session name cannot be empty")
        
        if total_images <= 0:
            raise SessionConfigurationError("Total images must be greater than 0")
        
        # Create session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.base_capture_dir, f"session_{name}_{timestamp}")
        
        try:
            os.makedirs(session_dir, exist_ok=True)
        except Exception as e:
            raise SessionConfigurationError(f"Failed to create session directory: {str(e)}")
        
        # Configure session
        self.session_config.update({
            'name': name,
            'total_images': total_images,
            'use_current_settings': use_current_settings,
            'enable_tracking': enable_tracking,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'images_captured': 0,
            'session_dir': session_dir,
            'status': 'running'
        })
        
        # Save session metadata
        self._save_session_metadata()
        
        # Start mount tracking if enabled
        if enable_tracking and not self.mount.tracking:
            try:
                self.mount.start_tracking()
                logger.info("Mount tracking started for session")
            except Exception as e:
                logger.warning(f"Failed to start mount tracking: {e}")
        
        # Start session thread
        self.session_running = True
        self.session_thread = threading.Thread(target=self._session_worker, daemon=True)
        self.session_thread.start()
        
        logger.info(f"Session '{name}' started: {total_images} images")
        return True
    
    def stop_session(self) -> bool:
        """Stop the current session.
        
        Returns:
            bool: True if session stopped successfully
        """
        if not self.session_running and self.session_config['status'] == 'completed':
            logger.info("Session already completed")
            return True
        
        logger.info("Stopping session...")
        self.session_running = False
        
        # Wait for session thread to finish
        if self.session_thread and self.session_thread.is_alive():
            self.session_thread.join(timeout=5.0)
        
        # Update session metadata
        self.session_config['end_time'] = datetime.now().isoformat()
        self.session_config['status'] = 'completed'
        self._save_session_metadata()
        
        # Stop mount tracking if it was started by the session
        if (self.session_config.get('enable_tracking', False) and 
            self.mount.tracking):
            try:
                self.mount.stop_tracking()
                logger.info("Mount tracking stopped")
            except Exception as e:
                logger.warning(f"Failed to stop mount tracking: {e}")
        
        logger.info(f"Session '{self.session_config['name']}' stopped. "
                   f"Captured {self.session_config['images_captured']} images")
        return True
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status.
        
        Returns:
            Dict containing session status information
        """
        # Calculate progress and elapsed time
        total_images = self.session_config['total_images']
        images_captured = self.session_config['images_captured']
        progress = (images_captured / total_images * 100) if total_images > 0 else 0
        
        # Calculate elapsed time
        elapsed_time = 0
        if self.session_config['start_time']:
            start_time = datetime.fromisoformat(self.session_config['start_time'])
            elapsed_time = int((datetime.now() - start_time).total_seconds())
        
        # Base status response
        status_response = {
            'running': self.session_running,
            'status': self.session_config['status'],
            'name': self.session_config['name'],
            'total_images': total_images,
            'images_captured': images_captured,
            'progress': round(progress, 1),
            'elapsed_time': elapsed_time,
            'session_dir': self.session_config['session_dir']
        }
        
        return status_response
    
    def _session_worker(self):
        """Background worker thread for session capture."""
        logger.info("Session worker started")
        
        try:
            while self.session_running:
                # Check if we've captured all images
                if self.session_config['images_captured'] >= self.session_config['total_images']:
                    logger.info("Session completed - all images captured")
                    break
                
                # Capture image
                if self._capture_session_image():
                    self.session_config['images_captured'] += 1
                    self._save_session_metadata()
                    
                    logger.info(f"Captured image {self.session_config['images_captured']}/"
                              f"{self.session_config['total_images']}")
                
                # Small delay between captures to prevent overwhelming the camera
                if (self.session_running and 
                    self.session_config['images_captured'] < self.session_config['total_images']):
                    time.sleep(0.5)  # 500ms delay between captures
        
        except Exception as e:
            logger.error(f"Session worker error: {e}")
            self.session_config['status'] = 'error'
            self._save_session_metadata()
            logger.error(f"Session status set to error in except block")
            return  # Exit the worker immediately on error
        
        finally:
            self.session_running = False
            logger.info(f"Session status at finally: {self.session_config['status']}")
            # Only set to completed if still running (i.e., no error occurred)
            # Note: We don't set status to 'completed' here - that only happens when stop_session() is called
            # We also don't stop mount tracking here - that only happens when stop_session() is called
            logger.info("Session worker finished")
    
    def _capture_session_image(self) -> bool:
        """Capture a single image for the session.
        
        Returns:
            bool: True if capture was successful
        """
        # Generate filename
        image_number = self.session_config['images_captured'] + 1
        filename = os.path.join(
            self.session_config['session_dir'],
            f"image_{image_number:04d}.jpg"
        )
        
        # Capture image using camera
        if hasattr(self.camera, 'capture_file'):
            self.camera.capture_file(filename)
        elif hasattr(self.camera, 'capture_still'):
            # For cameras that use capture_still, we need to handle the filename differently
            success = self.camera.capture_still()
            if success:
                # Rename the captured file to our desired filename
                # This assumes the camera saves to a timestamped filename
                import glob
                session_files = glob.glob(os.path.join(self.session_config['session_dir'], "capture_*.jpg"))
                if session_files:
                    latest_file = max(session_files, key=os.path.getctime)
                    os.rename(latest_file, filename)
                    return True
                return False
            return False
        else:
            logger.error("Camera does not support file capture")
            return False
        
        return True
    
    def _save_session_metadata(self):
        """Save session metadata to JSON file."""
        try:
            metadata_file = os.path.join(self.session_config['session_dir'], 'session_metadata.json')
            
            # Create a copy of config without non-serializable objects
            metadata = self.session_config.copy()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save session metadata: {e}")
    
    def cleanup(self):
        """Clean up session controller resources."""
        if self.session_running:
            self.stop_session()
        
        logger.info("Session controller cleaned up") 
"""
Session controller for managing capture sessions with multiple images.
"""
import os
import json
import time
import logging
import threading
import glob
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def safe_log(level, message, *args, **kwargs):
    """Safely log a message, handling I/O errors gracefully."""
    # Always use stderr for session worker logs to avoid file handle issues
    print(f"[{level.upper()}] {message}", file=sys.stderr)

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
        self._shutdown = False
        self._session_lock = threading.Lock()  # Add lock to prevent race conditions
        
        # Session configuration
        self.session_config = {
            'name': '',
            'total_images': 0,
            'use_current_settings': True,
            'enable_tracking': False,
            'total_time_hours': None,
            'start_time': None,
            'end_time': None,
            'images_captured': 0,
            'session_dir': '',
            'status': 'idle',
            'mount_tracking_stopped': False
        }
        
        logger.info("Session controller initialized")
    
    def start_session(self, name: str, total_images: int,
                     use_current_settings: bool = True, enable_tracking: bool = False,
                     total_time_hours: Optional[float] = None) -> bool:
        """Start a new capture session.

        Args:
            name: Session name (used for directory naming)
            total_images: Total number of images to capture
            use_current_settings: Whether to use current camera settings
            enable_tracking: Whether to enable mount tracking during session
            total_time_hours: Total time in hours to spread the captures over (optional)

        Returns:
            bool: True if session started successfully

        Raises:
            Exception: If a session is already running or configuration is invalid
        """
        with self._session_lock:
            if self.session_running:
                raise Exception("A session is already running")
            
            # Validate configuration
            if not name or not name.strip():
                raise Exception("Session name cannot be empty")
            
            if total_images <= 0:
                raise Exception("Total images must be greater than 0")

            if total_time_hours is not None and total_time_hours <= 0:
                raise Exception("Total time hours must be greater than 0")
            
            # Create session directory
            session_dir = os.path.join(self.base_capture_dir, name)
            
            try:
                os.makedirs(session_dir, exist_ok=True)
            except Exception as e:
                raise Exception(f"Failed to create session directory: {str(e)}")
            
            # Configure session
            self.session_config.update({
                'name': name,
                'total_images': total_images,
                'use_current_settings': use_current_settings,
                'enable_tracking': enable_tracking,
                'total_time_hours': total_time_hours,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'images_captured': 0,
                'session_dir': session_dir,
                'status': 'running',
                'mount_tracking_stopped': False
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
            
            if total_time_hours is not None:
                logger.info(f"Session '{name}' started: {total_images} images over {total_time_hours} hours")
            else:
                logger.info(f"Session '{name}' started: {total_images} images")
            return True
    
    def stop_session(self) -> bool:
        """Stop the current session.
        
        Returns:
            bool: True if session stopped successfully
        """
        with self._session_lock:
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
        if self.session_config['status'] == 'running':
            self.session_config['status'] = 'completed'
        self._save_session_metadata()
        
        # Stop mount tracking if it was started by the session
        if (self.session_config.get('enable_tracking', False) and 
            self.mount.tracking and not self.session_config.get('mount_tracking_stopped', False)):
            try:
                self.mount.stop_tracking()
                self.session_config['mount_tracking_stopped'] = True
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
        with self._session_lock:
            # Calculate progress and elapsed time
            total_images = self.session_config['total_images']
            images_captured = self.session_config['images_captured']
            progress = (images_captured / total_images * 100) if total_images > 0 else 0
            
            # Calculate elapsed time
            elapsed_time = 0
            if self.session_config['start_time']:
                start_time = datetime.fromisoformat(self.session_config['start_time'])
                elapsed_time = int((datetime.now() - start_time).total_seconds())
            
            # Calculate estimated completion time for time-based sessions
            estimated_completion = None
            total_time_hours = self.session_config.get('total_time_hours')
            formatted_time = None

            if total_time_hours and self.session_config['start_time']:
                start_time = datetime.fromisoformat(self.session_config['start_time'])
                estimated_completion = int((start_time + timedelta(hours=total_time_hours)).timestamp())

                # Format the total time as hours and minutes
                hours = int(total_time_hours)
                minutes = int((total_time_hours - hours) * 60)
                if hours > 0 and minutes > 0:
                    formatted_time = f"{hours}h {minutes}m"
                elif hours > 0:
                    formatted_time = f"{hours}h"
                elif minutes > 0:
                    formatted_time = f"{minutes}m"
                else:
                    formatted_time = "0m"

            # Base status response
            status_response = {
                'running': self.session_running,
                'status': self.session_config['status'],
                'name': self.session_config['name'],
                'total_images': total_images,
                'images_captured': images_captured,
                'progress': round(progress, 1),
                'elapsed_time': elapsed_time,
                'session_dir': self.session_config['session_dir'],
                'total_time_hours': total_time_hours,
                'formatted_time': formatted_time,
                'estimated_completion': estimated_completion
            }
            
            return status_response
    
    def _session_worker(self):
        """Background worker thread for session capture."""
        logger.info("Session worker started")
        
        try:
            while self.session_running and not self._shutdown:
                # Check if we've captured all images
                with self._session_lock:
                    if self.session_config['images_captured'] >= self.session_config['total_images']:
                        logger.info("Session completed - all images captured")
                        break
                
                # Capture image
                if self._capture_session_image():
                    with self._session_lock:
                        self.session_config['images_captured'] += 1
                        self._save_session_metadata()
                        
                        safe_log('info', f"Captured image {self.session_config['images_captured']}/"
                                  f"{self.session_config['total_images']}")
                
                # Calculate delay between captures
                with self._session_lock:
                    if (self.session_running and
                        self.session_config['images_captured'] < self.session_config['total_images']):
                        delay = self._calculate_capture_delay()
                        time.sleep(delay)
        
        except Exception as e:
            logger.error(f"Session worker error: {e}")
            with self._session_lock:
                self.session_config['status'] = 'error'
                self._save_session_metadata()
                logger.error(f"Session status set to error in except block: {self.session_config['status']}")
            return  # Exit the worker immediately on error
        
        finally:
            self.session_running = False
            with self._session_lock:
                logger.info(f"Session status at finally: {self.session_config['status']}")
                # Only set status to completed if it's still running (not error)
                if self.session_config['status'] == 'running':
                    self.session_config['status'] = 'completed'
                    self._save_session_metadata()
                    logger.info("Session status set to completed")
                elif self.session_config['status'] == 'error':
                    logger.info("Session status is error, not changing to completed")
                # Stop mount tracking if it was started by the session and session completed naturally
                if (self.session_config.get('enable_tracking', False) and 
                    self.mount.tracking and 
                    self.session_config['status'] == 'completed' and not self.session_config.get('mount_tracking_stopped', False)):
                    try:
                        self.mount.stop_tracking()
                        self.session_config['mount_tracking_stopped'] = True
                        logger.info("Mount tracking stopped (natural completion)")
                    except Exception as e:
                        logger.warning(f"Failed to stop mount tracking: {e}")
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
            return True
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
            else:
                # If capture_still returns False, it means capture failed
                raise Exception("Camera capture failed")
        else:
            logger.error("Camera does not support file capture")
            return False

    def _calculate_capture_delay(self) -> float:
        """Calculate the delay between captures based on session configuration.

        Returns:
            float: Delay in seconds between captures
        """
        total_time_hours = self.session_config.get('total_time_hours')
        if total_time_hours is None:
            # Default delay for non-time-based sessions
            return 0.5

        total_images = self.session_config['total_images']
        images_captured = self.session_config['images_captured']

        # Calculate total time in seconds
        total_time_seconds = total_time_hours * 3600

        # Calculate remaining time and images
        remaining_images = total_images - images_captured - 1  # -1 because we've already captured the current image
        if remaining_images <= 0:
            return 0.5  # Default delay for last image

        # Calculate delay needed to spread remaining images over remaining time
        start_time = datetime.fromisoformat(self.session_config['start_time'])
        elapsed_time = (datetime.now() - start_time).total_seconds()
        remaining_time_seconds = total_time_seconds - elapsed_time
        if remaining_time_seconds <= 0:
            return 0.5  # Default delay if we're behind schedule

        delay = remaining_time_seconds / remaining_images

        # Ensure minimum delay to prevent overwhelming the camera
        return max(delay, 0.5)

    def _save_session_metadata(self):
        """Save session metadata to JSON file."""
        try:
            metadata_file = os.path.join(self.session_config['session_dir'], 'session_metadata.json')

            # Create a copy of config and handle non-serializable objects
            metadata = {}
            for key, value in self.session_config.items():
                if isinstance(value, datetime):
                    metadata[key] = value.isoformat()
                elif hasattr(value, '__class__') and 'Mock' in value.__class__.__name__:
                    # Skip mock objects (used in testing)
                    continue
                else:
                    metadata[key] = value

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=self._json_serializer)

        except Exception as e:
            logger.error(f"Failed to save session metadata: {e}")

    def _json_serializer(self, obj):
        """Custom JSON serializer for non-serializable objects."""
        if hasattr(obj, '__class__') and 'Mock' in obj.__class__.__name__:
            return f"<Mock {obj.__class__.__name__}>"
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
    
    def cleanup(self):
        """Clean up session controller resources."""
        # Set shutdown flag to stop any running threads
        self._shutdown = True
        
        if self.session_running:
            self.stop_session()
        
        # Wait for session thread to finish with a longer timeout
        if self.session_thread and self.session_thread.is_alive():
            safe_log('info', "Waiting for session thread to finish...")
            self.session_thread.join(timeout=10.0)
            if self.session_thread.is_alive():
                safe_log('warning', "Session thread did not finish within timeout")
        
        safe_log('info', "Session controller cleaned up") 
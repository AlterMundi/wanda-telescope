"""
Web application for Wanda astrophotography system.
Provides a web interface to control the camera and mount.
"""
import math
import time
import logging
import os
from flask import Flask, Response, request, redirect, url_for, render_template, jsonify
import config
from camera import CameraFactory
from mount.controller import MountController
from session import SessionController

logger = logging.getLogger(__name__)

class WandaApp:
    """Web application for controlling the Wanda system."""
    
    def __init__(self, camera=None):
        """Initialize the web application with controllers."""
        # Create Flask app with proper template and static folders
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        
        self.app = Flask(__name__, 
                         template_folder=template_dir,
                         static_folder=static_dir)
                         
        if camera is None:
            raise ValueError("Camera instance is required")
        self.camera = camera
        self.mount = MountController()
        self.session_controller = SessionController(self.camera, self.mount, self.camera.capture_dir)
        self.setup_routes()
        logger.info("Web application initialized")
    
    def setup_routes(self):
        """Set up the application routes."""
        # Main routes
        self.app.route('/', methods=['GET', 'POST'])(self.index)
        self.app.route('/video_feed')(self.video_feed)
        
        # Camera routes
        self.app.route('/capture_still', methods=['POST'])(self.capture_still)
        self.app.route('/start_video', methods=['POST'])(self.start_video)
        self.app.route('/stop_video', methods=['POST'])(self.stop_video)
        self.app.route('/capture_status')(self.get_capture_status)
        
        # Mount routes
        self.app.route('/start_tracking', methods=['POST'])(self.start_tracking)
        self.app.route('/stop_tracking', methods=['POST'])(self.stop_tracking)
        
        # Session routes
        self.app.route('/start_session', methods=['POST'])(self.start_session)
        self.app.route('/stop_session', methods=['POST'])(self.stop_session)
        self.app.route('/session_status')(self.get_session_status)
    
    def run(self):
        """Run the web application."""
        try:
            logger.info(f"Starting web server on {config.HOST}:{config.PORT}")
            self.app.run(host=config.HOST, port=config.PORT, threaded=True)
        except Exception as e:
            logger.error(f"Error in web server: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources when shutting down."""
        logger.info("Application shutting down, cleaning up resources...")
        self.camera.cleanup()
        self.mount.cleanup()
        self.session_controller.cleanup()
        logger.info("Application shutdown complete")
    
    # Route handlers
    def index(self):
        """Handle the main page request."""
        if request.method == 'POST':
            self._handle_post_request()
            
            # Return JSON response if this is an AJAX request
            if request.headers.get('Accept') == 'application/json':
                template_vars = self._prepare_template_vars()
                return jsonify(template_vars)
        
        # Prepare template variables for regular page render
        template_vars = self._prepare_template_vars()
        return render_template('index.html', **template_vars)
    
    def _handle_post_request(self):
        """Handle POST requests to the main page."""
        # Camera settings
        slider_value = request.form.get('exposure', type=int)
        iso = request.form.get('iso', type=int)
        
        # Handle camera settings - apply both exposure and ISO together
        if slider_value is not None or iso is not None:
            # Convert slider value to exposure time in seconds, then to microseconds
            if slider_value is not None:
                exposure_seconds = self._slider_to_seconds(slider_value)
                exposure_us = int(exposure_seconds * 1000000)
            else:
                exposure_us = self.camera.get_exposure_us()

            # Convert ISO slider value (0-1000) to actual ISO value, with validation
            if iso is not None:
                min_iso = 100  # Maps to gain 1.0 (IMX477 minimum)
                max_iso = 1600  # Maps to gain 16.0 (IMX477 maximum)
                try:
                    iso_slider_value = int(iso)
                    # Convert slider value to ISO value
                    actual_iso = min_iso + (max_iso - min_iso) * iso_slider_value / 1000
                    actual_iso = max(min_iso, min(max_iso, actual_iso))  # Clamp to range
                except (ValueError, TypeError):
                    actual_iso = 800  # Default to Medium
                gain = self.camera.iso_to_gain(actual_iso)
            else:
                gain = self.camera.gain

            # Apply both exposure and gain to camera
            self.camera.set_exposure_us(exposure_us, gain)
        
        # Night vision mode settings
        self.camera.night_vision_mode = 'night_vision_mode' in request.form
        
        night_vision_intensity = request.form.get('night_vision_intensity', type=float)
        if night_vision_intensity is not None:
            self.camera.night_vision_intensity = max(1.0, min(night_vision_intensity, 80.0))
        
        # RAW toggle
        self.camera.save_raw = 'save_raw' in request.form
        
        # Performance setting
        performance_value = request.form.get('performance', type=int)
        if performance_value is not None:
            self.camera.skip_frames = performance_value
        
        # Apply camera settings
        self.camera.update_camera_settings()
        
        # Handle mount settings
        mount_speed = request.form.get('mount_speed', type=float)
        mount_dir = request.form.get('mount_direction')
        
        if mount_speed is not None or mount_dir is not None:
            direction = (mount_dir == 'clockwise') if mount_dir is not None else None
            self.mount.update_settings(speed=mount_speed, direction=direction)
    
    def _prepare_template_vars(self):
        """Prepare template variables for the index page."""
        # Convert exposure time to seconds for display
        exposure_seconds = self.camera.get_exposure_seconds()
        current_exposure = self._format_exposure_display(exposure_seconds)
        
        # Convert current ISO to slider value and label
        current_iso = self.camera.gain_to_iso(self.camera.gain)
        iso_slider_value, current_iso_label = self._iso_to_slider_and_label(current_iso)
        
        # Calculate slider value from exposure time in seconds
        min_seconds = 0.1
        max_seconds = 230  # IMX477 sensor maximum
        slider_max = 1000
        log_range = math.log(max_seconds / min_seconds)
        slider_value = int(1000 * math.log(exposure_seconds / min_seconds) / log_range)
        slider_value = max(0, min(slider_value, slider_max))
        
        # Get current exposure time in seconds for the countdown
        exposure_seconds = self.camera.get_exposure_seconds()
        
        # Convert performance setting to text
        performance_labels = ['High Quality', 'Good Quality', 'Balanced', 'Moderate', 'Low CPU', 'Lowest CPU']
        performance_text = performance_labels[min(self.camera.skip_frames, len(performance_labels) - 1)]
        
        return {
            'current_exposure': current_exposure,
            'iso_slider_value': iso_slider_value,
            'current_iso_label': current_iso_label,
            'slider_value': slider_value,
            'exposure_seconds': exposure_seconds,
            'night_vision_mode': self.camera.night_vision_mode,
            'night_vision_intensity': self.camera.night_vision_intensity,
            'save_raw': self.camera.save_raw,
            'skip_frames': self.camera.skip_frames,
            'performance_text': performance_text,
            'recording': self.camera.recording,
            'capture_status': self.camera.capture_status,
            'capture_dir': self.camera.capture_dir,
            'mount_status': self.mount.status,
            'mount_tracking': self.mount.tracking,
            'mount_direction': self.mount.direction,
            'mount_speed': self.mount.speed
        }
    
    def _format_exposure_display(self, seconds):
        """Format exposure time in seconds for display."""
        if seconds < 1:
            return f"{seconds:.1f}s"
        elif seconds < 10:
            return f"{seconds:.1f}s"
        else:
            return f"{int(seconds)}s"
    
    def _slider_to_seconds(self, slider_value):
        """Convert slider value (0-1000) to exposure time in seconds."""
        import math
        min_seconds = 0.1
        max_seconds = 230  # IMX477 sensor maximum
        log_range = math.log(max_seconds / min_seconds)
        return min_seconds * math.exp(slider_value * log_range / 1000)
    
    def _iso_to_slider_and_label(self, iso_value):
        """Convert ISO value to slider position and display label."""
        min_iso = 100  # Maps to gain 1.0 (IMX477 minimum)
        max_iso = 1600  # Maps to gain 16.0 (IMX477 maximum)
        
        # Convert ISO value to slider position (0-1000)
        slider_value = int(1000 * (iso_value - min_iso) / (max_iso - min_iso))
        slider_value = max(0, min(1000, slider_value))  # Clamp to range
        
        # Check if we're near milestone values for display
        milestones = [100, 800, 1600]
        milestone_labels = {100: 'Low (100)', 800: 'Medium (800)', 1600: 'High (1600)'}
        
        # Find if we're close to a milestone
        for milestone in milestones:
            if abs(iso_value - milestone) <= 50:  # Same threshold as frontend
                return slider_value, milestone_labels[milestone]
        
        # If not near a milestone, show the actual value
        return slider_value, str(int(iso_value))
    
    def video_feed(self):
        """Stream video feed from the camera."""
        def generate():
            while True:
                frame_data = self.camera.get_frame()
                if frame_data is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                else:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + b'' + b'\r\n')
                time.sleep(0.1)
                
        return Response(generate(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    
    def get_capture_status(self):
        """Return the current capture status."""
        return jsonify({
            'capture_status': self.camera.capture_status,
            'recording': self.camera.recording
        })
    
    # Camera route handlers
    def capture_still(self):
        """Capture a still image."""
        # Update initial status
        self.camera.capture_status = "Preparing to capture..."
        success = self.camera.capture_still()
        
        # If AJAX request, return JSON
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': success,
                'capture_status': self.camera.capture_status,
                'recording': self.camera.recording,
                'exposure_seconds': self.camera.get_exposure_seconds(),
                'capture_initiated': True
            })
        
        # Otherwise, redirect to index
        return redirect(url_for('index'))
    
    def start_video(self):
        """Start video recording."""
        success = self.camera.start_video()
        
        # If AJAX request, return JSON
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': success,
                'capture_status': self.camera.capture_status,
                'recording': self.camera.recording
            })
        
        # Otherwise, redirect to index
        return redirect(url_for('index'))
    
    def stop_video(self):
        """Stop video recording."""
        success = self.camera.stop_video()
        
        # If AJAX request, return JSON
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': success,
                'capture_status': self.camera.capture_status,
                'recording': self.camera.recording
            })
        
        # Otherwise, redirect to index
        return redirect(url_for('index'))
    
    # Mount route handlers
    def start_tracking(self):
        """Start mount tracking."""
        success = self.mount.start_tracking()
        
        # If AJAX request, return JSON
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': success,
                'mount_status': self.mount.status,
                'mount_tracking': self.mount.tracking
            })
        
        # Otherwise, redirect to index
        return redirect(url_for('index'))
    
    def stop_tracking(self):
        """Stop mount tracking."""
        success = self.mount.stop_tracking()
        
        # If AJAX request, return JSON
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': success,
                'mount_status': self.mount.status,
                'mount_tracking': self.mount.tracking
            })
        
        # Otherwise, redirect to index
        return redirect(url_for('index'))
    
    # Session route handlers
    def start_session(self):
        """Start a capture session."""
        try:
            # Get session parameters from form
            name = request.form.get('session_name', '').strip()
            total_images = request.form.get('total_images', type=int)
            use_current_settings = 'use_current_settings' in request.form
            enable_tracking = 'enable_tracking' in request.form

            # Handle time parameters (hours and minutes)
            total_time_hours = request.form.get('total_time_hours', type=int)
            total_time_minutes = request.form.get('total_time_minutes', type=int)

            # Convert to total hours if both are provided
            if total_time_hours is not None or total_time_minutes is not None:
                hours = total_time_hours or 0
                minutes = total_time_minutes or 0
                total_time_hours = hours + (minutes / 60.0)
            else:
                total_time_hours = None
            
            # Validate required parameters
            if not name:
                return jsonify({'success': False, 'error': 'Session name is required'})
            
            if not total_images or total_images <= 0:
                return jsonify({'success': False, 'error': 'Total images must be greater than 0'})

            if total_time_hours is not None and total_time_hours <= 0:
                return jsonify({'success': False, 'error': 'Total time must be greater than 0'})
            
            # Start the session
            success = self.session_controller.start_session(
                name=name,
                total_images=total_images,
                use_current_settings=use_current_settings,
                enable_tracking=enable_tracking,
                total_time_hours=total_time_hours if total_time_hours and total_time_hours > 0 else None
            )
            
            return jsonify({
                'success': success,
                'session_status': self.session_controller.get_session_status()
            })
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    def stop_session(self):
        """Stop the current session."""
        try:
            success = self.session_controller.stop_session()
            
            return jsonify({
                'success': success,
                'session_status': self.session_controller.get_session_status()
            })
            
        except Exception as e:
            logger.error(f"Error stopping session: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    def get_session_status(self):
        """Get current session status."""
        try:
            status = self.session_controller.get_session_status()
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return jsonify({'error': str(e)})
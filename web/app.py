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
                         
        self.camera = camera if camera else CameraFactory.create_camera()
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
        
        if slider_value is not None and iso is not None:
            # Convert slider value to exposure time in seconds, then to microseconds
            exposure_seconds = self._slider_to_seconds(slider_value)
            self.camera.exposure_us = int(exposure_seconds * 1000000)
            self.camera.gain = self.camera.iso_to_gain(iso)
        
        # Digital gain settings
        self.camera.use_digital_gain = 'use_digital_gain' in request.form
        
        digital_gain_value = request.form.get('digital_gain', type=float)
        if digital_gain_value is not None:
            self.camera.digital_gain = max(1.0, min(digital_gain_value, 80.0))
        
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
        current_iso = self.camera.gain_to_iso(self.camera.gain)
        
        # Calculate slider value from exposure time in seconds
        min_seconds = 0.1
        max_seconds = 300
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
            'current_iso': current_iso,
            'slider_value': slider_value,
            'exposure_seconds': exposure_seconds,
            'use_digital_gain': self.camera.use_digital_gain,
            'digital_gain': self.camera.digital_gain,
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
        max_seconds = 300
        log_range = math.log(max_seconds / min_seconds)
        return min_seconds * math.exp(slider_value * log_range / 1000)
    
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
            
            # Validate required parameters
            if not name:
                return jsonify({'success': False, 'error': 'Session name is required'})
            
            if not total_images or total_images <= 0:
                return jsonify({'success': False, 'error': 'Total images must be greater than 0'})
            
            # Start the session
            success = self.session_controller.start_session(
                name=name,
                total_images=total_images,
                use_current_settings=use_current_settings,
                enable_tracking=enable_tracking
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
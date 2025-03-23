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
from camera.controller import CameraController
from mount.controller import MountController

logger = logging.getLogger(__name__)

class WandaApp:
    """Web application for controlling the Wanda system."""
    
    def __init__(self):
        """Initialize the web application with controllers."""
        # Create Flask app with proper template and static folders
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        
        self.app = Flask(__name__, 
                         template_folder=template_dir,
                         static_folder=static_dir)
                         
        self.camera = CameraController()
        self.mount = MountController()
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
        
        # Mount routes
        self.app.route('/start_tracking', methods=['POST'])(self.start_tracking)
        self.app.route('/stop_tracking', methods=['POST'])(self.stop_tracking)
    
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
            self.camera.exposure_us = self.camera.slider_to_us(slider_value)
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
        current_shutter = self.camera.us_to_shutter_string(self.camera.exposure_us)
        current_iso = self.camera.gain_to_iso(self.camera.gain)
        
        # Calculate slider value from exposure time
        min_us = 100
        max_us = 200_000_000
        slider_max = 1000
        log_range = math.log(max_us / min_us)
        slider_value = int(1000 * math.log(self.camera.exposure_us / min_us) / log_range)
        slider_value = max(0, min(slider_value, slider_max))
        
        # Get current exposure time in seconds for the countdown
        exposure_seconds = self.camera.get_exposure_seconds()
        
        # Convert performance setting to text
        performance_labels = ['High Quality', 'Good Quality', 'Balanced', 'Moderate', 'Low CPU', 'Lowest CPU']
        performance_text = performance_labels[min(self.camera.skip_frames, len(performance_labels) - 1)]
        
        return {
            'current_shutter': current_shutter,
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
    
    # Camera route handlers
    def capture_still(self):
        """Capture a still image."""
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
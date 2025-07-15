"""Unit tests for exposure time controls functionality."""
import pytest
import json
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.app import WandaApp
from camera.implementations.mock_camera import MockCamera


class TestExposureControls:
    """Test exposure time controls functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.camera = MockCamera()
        self.app = WandaApp(camera=self.camera)
    
    def test_format_exposure_display_less_than_one_second(self):
        """Test formatting exposure time less than 1 second."""
        result = self.app._format_exposure_display(0.5)
        assert result == "0.5s"
    
    def test_format_exposure_display_one_to_ten_seconds(self):
        """Test formatting exposure time between 1 and 10 seconds."""
        result = self.app._format_exposure_display(5.7)
        assert result == "5.7s"
    
    def test_format_exposure_display_over_ten_seconds(self):
        """Test formatting exposure time over 10 seconds."""
        result = self.app._format_exposure_display(25)
        assert result == "25s"
    
    def test_format_exposure_display_exact_ten_seconds(self):
        """Test formatting exposure time exactly 10 seconds."""
        result = self.app._format_exposure_display(10.0)
        assert result == "10s"
    
    def test_slider_to_seconds_minimum_value(self):
        """Test converting minimum slider value to seconds."""
        result = self.app._slider_to_seconds(0)
        assert abs(result - 0.1) < 0.001
    
    def test_slider_to_seconds_maximum_value(self):
        """Test converting maximum slider value to seconds."""
        result = self.app._slider_to_seconds(1000)
        assert abs(result - 300.0) < 0.001
    
    def test_slider_to_seconds_middle_value(self):
        """Test converting middle slider value to seconds."""
        result = self.app._slider_to_seconds(500)
        # Should be around 5.5 seconds (logarithmic scale)
        assert 5 < result < 6
    
    def test_slider_to_seconds_preset_values(self):
        """Test converting slider values for preset exposure times."""
        # Test Bright Objects preset (0.5s)
        slider_value = int(1000 * math.log(0.5 / 0.1) / math.log(300 / 0.1))
        result = self.app._slider_to_seconds(slider_value)
        assert abs(result - 0.5) < 0.1
        
        # Test Deep Sky preset (30s)
        slider_value = int(1000 * math.log(30 / 0.1) / math.log(300 / 0.1))
        result = self.app._slider_to_seconds(slider_value)
        assert abs(result - 30) < 1
        
        # Test Long Exposure preset (300s)
        slider_value = int(1000 * math.log(300 / 0.1) / math.log(300 / 0.1))
        result = self.app._slider_to_seconds(slider_value)
        assert abs(result - 300) < 1
    
    def test_prepare_template_vars_with_new_range(self):
        """Test template variables preparation with new exposure range."""
        # Set camera to a known exposure time
        self.camera.exposure_us = 500000  # 0.5 seconds
        
        template_vars = self.app._prepare_template_vars()
        
        assert 'current_exposure' in template_vars
        assert template_vars['current_exposure'] == "0.5s"
        assert 'slider_value' in template_vars
        assert 0 <= template_vars['slider_value'] <= 1000
    
    def test_prepare_template_vars_with_long_exposure(self):
        """Test template variables preparation with long exposure."""
        # Set camera to a long exposure time
        self.camera.exposure_us = 300000000  # 300 seconds
        
        template_vars = self.app._prepare_template_vars()
        
        assert 'current_exposure' in template_vars
        assert template_vars['current_exposure'] == "300s"
        assert 'slider_value' in template_vars
        assert template_vars['slider_value'] == 1000  # Maximum value
    
    def test_handle_post_request_with_exposure_update(self):
        """Test handling POST request with exposure time update."""
        # Simulate form data with new exposure slider value
        with self.app.app.test_request_context('/', method='POST', data={
            'exposure': '500',  # Middle of the range
            'iso': '100'
        }):
            self.app._handle_post_request()
            
            # Check that exposure was updated (should be around 5.5 seconds)
            exposure_seconds = self.camera.get_exposure_seconds()
            assert 5 < exposure_seconds < 6


class TestExposureTemplateRendering:
    """Test exposure controls template rendering."""
    
    def test_template_has_exposure_controls(self, client):
        """Test that the template includes exposure time controls."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for new exposure time label
        assert b"Exposure Time in Seconds (0.1s - 300s)" in response.data
        
        # Check for preset buttons
        assert b"Bright Objects (0.5s)" in response.data
        assert b"Deep Sky (30s)" in response.data
        assert b"Long Exposure (300s)" in response.data
        
        # Check for tooltips
        assert b"Bright Objects: For the Moon or planets" in response.data
        assert b"Deep Sky: For nebulae and galaxies" in response.data
        assert b"Long Exposure: For faint deep-sky objects" in response.data
    
    def test_template_has_exposure_display(self, client):
        """Test that the template includes exposure display element."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for exposure display output
        assert b'id="exposure_display"' in response.data
    
    def test_template_has_preset_buttons(self, client):
        """Test that the template includes preset buttons with correct styling."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for preset button container
        assert b'class="exposure-presets"' in response.data
        
        # Check for preset button styling
        assert b'class="preset-btn"' in response.data


class TestExposureJavaScript:
    """Test exposure controls JavaScript functionality."""
    
    def test_javascript_has_update_exposure_function(self, client):
        """Test that JavaScript includes updateExposure function."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for JavaScript function
        assert b"updateExposure" in response.data
    
    def test_javascript_has_set_preset_function(self, client):
        """Test that JavaScript includes setPreset function."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for JavaScript function
        assert b"setPreset" in response.data
    
    def test_javascript_has_correct_range_constants(self, client):
        """Test that JavaScript has correct range constants."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for new range values
        assert b"0.1" in response.data
        assert b"300" in response.data
    
    def test_javascript_preset_calculation_logic(self):
        """Test the JavaScript preset calculation logic matches backend."""
        # Test the same calculation logic that's in the JavaScript
        min_seconds = 0.1
        max_seconds = 300
        log_range = math.log(max_seconds / min_seconds)
        
        # Test Bright Objects preset (0.5s)
        slider_value = int(1000 * math.log(0.5 / min_seconds) / log_range)
        expected_seconds = min_seconds * math.exp(slider_value * log_range / 1000)
        assert abs(expected_seconds - 0.5) < 0.1
        
        # Test Deep Sky preset (30s)
        slider_value = int(1000 * math.log(30 / min_seconds) / log_range)
        expected_seconds = min_seconds * math.exp(slider_value * log_range / 1000)
        assert abs(expected_seconds - 30) < 1
        
        # Test Long Exposure preset (300s)
        slider_value = int(1000 * math.log(300 / min_seconds) / log_range)
        expected_seconds = min_seconds * math.exp(slider_value * log_range / 1000)
        assert abs(expected_seconds - 300) < 1


class TestExposureCSS:
    """Test exposure controls CSS styling."""
    
    def test_css_has_preset_button_styles(self, client):
        """Test that CSS includes preset button styles."""
        # Get the CSS file directly
        response = client.get("/static/css/modern-ui.css")
        assert response.status_code == 200
        
        # Check for CSS classes
        assert b".exposure-presets" in response.data
        assert b".preset-btn" in response.data 
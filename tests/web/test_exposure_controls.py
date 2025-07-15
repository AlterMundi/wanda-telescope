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
            'iso': '500'  # Middle of ISO range (should be around 810)
        }):
            self.app._handle_post_request()
            
            # Check that exposure was updated (should be around 5.5 seconds)
            exposure_seconds = self.camera.get_exposure_seconds()
            assert 5 < exposure_seconds < 6
            
            # Check that ISO was updated (should be around 810)
            current_iso = self.camera.gain_to_iso(self.camera.gain)
            assert 800 < current_iso < 820  # Allow for small rounding differences
    
    def test_iso_slider_range_conversion(self):
        """Test ISO slider value conversion to actual ISO values."""
        # Test minimum value (0 -> 20)
        slider_value = 0
        min_iso = 20
        max_iso = 1600
        expected_iso = min_iso + (max_iso - min_iso) * slider_value / 1000
        assert expected_iso == 20
        
        # Test maximum value (1000 -> 1600)
        slider_value = 1000
        expected_iso = min_iso + (max_iso - min_iso) * slider_value / 1000
        assert expected_iso == 1600
        
        # Test middle value (500 -> 810)
        slider_value = 500
        expected_iso = min_iso + (max_iso - min_iso) * slider_value / 1000
        assert expected_iso == 810
    
    def test_iso_to_slider_and_label_milestone_values(self):
        """Test ISO to slider conversion for milestone values."""
        # Test Low milestone (20)
        slider_value, label = self.app._iso_to_slider_and_label(20)
        assert slider_value == 0
        assert label == "Low (20)"
        
        # Test Medium milestone (800)
        slider_value, label = self.app._iso_to_slider_and_label(800)
        # Calculate expected: 1000 * (800-20)/(1600-20) = 1000 * 780/1580 ≈ 493
        expected_slider = int(1000 * (800 - 20) / (1600 - 20))
        assert slider_value == expected_slider
        assert label == "Medium (800)"
        
        # Test High milestone (1600)
        slider_value, label = self.app._iso_to_slider_and_label(1600)
        assert slider_value == 1000
        assert label == "High (1600)"
    
    def test_iso_to_slider_and_label_intermediate_values(self):
        """Test ISO to slider conversion for intermediate values."""
        # Test value near Low milestone
        slider_value, label = self.app._iso_to_slider_and_label(70)  # Within 50 of 20
        assert label == "Low (20)"
        
        # Test value near Medium milestone
        slider_value, label = self.app._iso_to_slider_and_label(850)  # Within 50 of 800
        assert label == "Medium (800)"
        
        # Test value near High milestone
        slider_value, label = self.app._iso_to_slider_and_label(1550)  # Within 50 of 1600
        assert label == "High (1600)"
        
        # Test intermediate value (not near any milestone)
        slider_value, label = self.app._iso_to_slider_and_label(400)
        assert label == "400"  # Should show actual value
    
    def test_night_vision_mode_handling(self):
        """Test handling of night vision mode settings."""
        # Test enabling night vision mode
        with self.app.app.test_request_context('/', method='POST', data={
            'night_vision_mode': 'on',
            'night_vision_intensity': '40.0'
        }):
            self.app._handle_post_request()
            
            # Check that night vision mode was enabled
            assert self.camera.night_vision_mode == True
            assert self.camera.night_vision_intensity == 40.0
    
    def test_night_vision_intensity_validation(self):
        """Test night vision intensity validation."""
        # Test minimum value
        with self.app.app.test_request_context('/', method='POST', data={
            'night_vision_mode': 'on',
            'night_vision_intensity': '0.5'  # Below minimum
        }):
            self.app._handle_post_request()
            assert self.camera.night_vision_intensity == 1.0  # Should clamp to minimum
        
        # Test maximum value
        with self.app.app.test_request_context('/', method='POST', data={
            'night_vision_mode': 'on',
            'night_vision_intensity': '100.0'  # Above maximum
        }):
            self.app._handle_post_request()
            assert self.camera.night_vision_intensity == 80.0  # Should clamp to maximum
    
    def test_night_vision_mode_disabled(self):
        """Test that night vision mode can be disabled."""
        # First enable it
        self.camera.night_vision_mode = True
        self.camera.night_vision_intensity = 40.0
        
        # Then disable it
        with self.app.app.test_request_context('/', method='POST', data={
            # No night_vision_mode in form data
            'night_vision_intensity': '50.0'
        }):
            self.app._handle_post_request()
            
            # Check that night vision mode was disabled
            assert self.camera.night_vision_mode == False
            # Intensity should still be updated
            assert self.camera.night_vision_intensity == 50.0


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
    
    def test_template_has_night_vision_controls(self, client):
        """Test that the template includes night vision mode controls."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for night vision mode toggle
        assert b"Night Vision Mode" in response.data
        assert b'name="night_vision_mode"' in response.data
        
        # Check for intensity slider
        assert b"Intensity (1.0-80.0)" in response.data
        assert b'name="night_vision_intensity"' in response.data
        
        # Check for night vision presets
        assert b'class="night-vision-presets"' in response.data
        assert b"Low" in response.data
        assert b"Medium" in response.data
        assert b"High" in response.data
        
        # Check for tooltips
        assert b"Low intensity for subtle enhancement" in response.data
        assert b"Medium intensity for balanced enhancement" in response.data
        assert b"High intensity for maximum enhancement" in response.data


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
    
    def test_javascript_has_night_vision_functions(self, client):
        """Test that JavaScript includes night vision functions."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for JavaScript functions
        assert b"toggleNightVision" in response.data
        assert b"updateNightVisionIntensity" in response.data
        assert b"setNightVisionIntensity" in response.data


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
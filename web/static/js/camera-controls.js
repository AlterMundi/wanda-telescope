/**
 * Camera controls functionality
 */
const CameraControls = {
    /**
     * Update exposure time display based on slider value
     * @param {number} sliderValue - Value from the exposure slider (0-1000)
     */
    updateExposure: function(sliderValue) {
        const minSeconds = 0.1;
        const maxSeconds = 300;
        const seconds = minSeconds * Math.pow(maxSeconds / minSeconds, sliderValue / 1000);
        
        // Format the display: show as decimal for < 1s, otherwise as whole seconds
        let display;
        if (seconds < 1) {
            display = seconds.toFixed(1) + 's';
        } else if (seconds < 10) {
            display = seconds.toFixed(1) + 's';
        } else {
            display = Math.round(seconds) + 's';
        }
        
        document.getElementById('exposure_display').value = display;
    },
    
    /**
     * Set exposure time to a preset value
     * @param {number} seconds - Exposure time in seconds
     */
    setPreset: function(seconds) {
        const minSeconds = 0.1;
        const maxSeconds = 300;
        const logRange = Math.log(maxSeconds / minSeconds);
        const sliderValue = Math.round(1000 * Math.log(seconds / minSeconds) / logRange);
        
        // Update the slider
        const slider = document.querySelector('input[name="exposure"]');
        slider.value = sliderValue;
        
        // Update the display
        this.updateExposure(sliderValue);
        
        // Trigger form submission to apply the setting
        const form = slider.closest('form');
        if (form) {
            form.submit();
        }
    },
    
    /**
     * Monitor capture progress without starting a separate countdown
     * @param {number} expectedSeconds - Expected exposure time in seconds
     */
    monitorCapture: function(expectedSeconds) {
        // Start polling for status immediately
        this.pollCaptureStatus();
    },
    
    /**
     * Poll for capture status until completion
     */
    pollCaptureStatus: function() {
        const countdownElement = document.getElementById('countdown');
        const statusElement = document.getElementById('status_display');
        let lastStatus = '';
        let hasStartedCapture = false;
        
        // Poll every 500ms to check capture status
        let statusCheck = setInterval(function() {
            fetch('/capture_status', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Only update if status has changed
                if (lastStatus !== data.capture_status) {
                    lastStatus = data.capture_status;
                    
                    // Update status display
                    if (statusElement) {
                        statusElement.textContent = data.capture_status;
                    }
                    
                    // Handle countdown display based on status
                    if (countdownElement) {
                        if (data.capture_status.includes("Capturing")) {
                            // Just started capturing
                            hasStartedCapture = true;
                        } 
                        else if (data.capture_status.includes("saved as")) {
                            // Capture complete
                            countdownElement.textContent = '';
                            clearInterval(statusCheck);
                        } 
                        else if (hasStartedCapture) {
                            // In progress, show appropriate message
                            countdownElement.textContent = 'Processing...';
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error checking capture status:', error);
            });
        }, 300);
    },
    
    /**
     * Toggle digital gain controls
     * @param {HTMLElement} checkbox - The digital gain checkbox
     */
    toggleDigitalGain: function(checkbox) {
        const slider = document.querySelector('input[name="digital_gain"]');
        const container = document.getElementById('digital-gain-container');
        
        slider.disabled = !checkbox.checked;
        container.style.opacity = checkbox.checked ? '1.0' : '0.5';
    }
};

// Initialize controls when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Set up event handler for digital gain checkbox
    const checkbox = document.querySelector('input[name="use_digital_gain"]');
    if (checkbox) {
        checkbox.addEventListener('change', function() {
            CameraControls.toggleDigitalGain(this);
        });
    }
    
    // Set up capture form with status monitoring
    const captureForm = document.getElementById('capture-form');
    if (captureForm) {
        captureForm.addEventListener('submit', function(event) {
            // Get exposure seconds from data attribute
            const seconds = parseInt(this.getAttribute('data-exposure-seconds'), 10);
            if (!isNaN(seconds)) {
                CameraControls.monitorCapture(seconds);
            }
            // Allow form submission to continue
            return true;
        });
    }
});
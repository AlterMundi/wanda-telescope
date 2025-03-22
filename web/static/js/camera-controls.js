/**
 * Camera controls functionality
 */
const CameraControls = {
    /**
     * Update shutter speed display based on slider value
     * @param {number} sliderValue - Value from the exposure slider (0-1000)
     */
    updateShutter: function(sliderValue) {
        const minUs = 100;
        const maxUs = 200000000;
        const us = minUs * Math.pow(maxUs / minUs, sliderValue / 1000);
        const seconds = us / 1000000;
        const display = seconds < 1 ? 
            '1/' + Math.round(1/seconds) + 's' : 
            Math.round(seconds) + 's';
        
        document.getElementById('shutter_display').value = display;
    },
    
    /**
     * Start countdown timer for exposure
     * @param {number} seconds - Exposure time in seconds
     */
    startCountdown: function(seconds) {
        // Get the countdown element
        const countdownElement = document.getElementById('countdown');
        const statusElement = document.getElementById('status_display');
        
        // Set initial text
        statusElement.textContent = 'Capturing...';
        countdownElement.textContent = 'Exposure: ' + seconds + 's remaining';
        
        // Start the countdown
        let timer = setInterval(function() {
            seconds--;
            
            if (seconds <= 0) {
                clearInterval(timer);
                countdownElement.textContent = 'Processing...';
            } else {
                countdownElement.textContent = 'Exposure: ' + seconds + 's remaining';
            }
        }, 1000);
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
    
    // Set up capture form with countdown
    const captureForm = document.getElementById('capture-form');
    if (captureForm) {
        captureForm.addEventListener('submit', function(event) {
            // Get exposure seconds from data attribute
            const seconds = parseInt(this.getAttribute('data-exposure-seconds'), 10);
            if (!isNaN(seconds)) {
                CameraControls.startCountdown(seconds);
            }
            // Allow form submission to continue
            return true;
        });
    }
});
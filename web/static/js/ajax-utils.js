/**
 * AJAX utilities for Wanda UI to prevent page reloads
 * Updated for the modern interface
 */
const AjaxUtils = {
    /**
     * Submit a form via AJAX instead of regular submission
     * @param {HTMLFormElement} form - The form to submit
     * @param {Function} callback - Optional callback function after successful submission
     */
    submitForm: function(form, callback) {
        const formData = new FormData(form);
        const url = form.action;
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Update status displays in the status bar
            if (data.capture_status) {
                const statusDisplay = document.getElementById('status_display');
                if (statusDisplay) {
                    statusDisplay.textContent = data.capture_status;
                }
            }
            
            if (data.mount_status) {
                // Update mount status in the status bar
                const mountStatus = document.querySelector('.status-bar #mount_status');
                if (mountStatus) {
                    mountStatus.textContent = data.mount_status;
                }
            }
            
            // Update UI based on recording state
            if (data.hasOwnProperty('recording')) {
                const captureBtn = document.querySelector('form#capture-form input[type="submit"]');
                const startVideoBtn = document.querySelector('form[action*="start_video"] input[type="submit"]');
                const stopVideoBtn = document.querySelector('form[action*="stop_video"] input[type="submit"]');
                
                if (captureBtn) captureBtn.disabled = data.recording;
                if (startVideoBtn) startVideoBtn.disabled = data.recording;
                if (stopVideoBtn) stopVideoBtn.disabled = !data.recording;
            }
            
            // Update UI based on tracking state
            if (data.hasOwnProperty('mount_tracking')) {
                const startTrackingBtn = document.querySelector('form[action*="start_tracking"] input[type="submit"]');
                const stopTrackingBtn = document.querySelector('form[action*="stop_tracking"] input[type="submit"]');
                
                if (startTrackingBtn) startTrackingBtn.disabled = data.mount_tracking;
                if (stopTrackingBtn) stopTrackingBtn.disabled = !data.mount_tracking;
            }
            
            // If countdown is needed for photo capture
            if (data.exposure_seconds && data.capture_initiated) {
                CameraControls.startCountdown(data.exposure_seconds);
            }
            
            // Run callback if provided
            if (typeof callback === 'function') {
                callback(data);
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
        });
        
        // Prevent default form submission
        return false;
    },
    
    /**
     * Initialize AJAX form handling for all forms
     */
    initForms: function() {
        // Get all forms in the document
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            if (form.dataset.ajax === "false") {
                return;
            }
            form.addEventListener('submit', function(event) {
                event.preventDefault();
                AjaxUtils.submitForm(this);
            });
        });
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    AjaxUtils.initForms();
});
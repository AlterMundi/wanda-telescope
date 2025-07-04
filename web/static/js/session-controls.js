/**
 * Session controls functionality for Wanda Telescope
 */
const SessionControls = {
    /**
     * Initialize session controls
     */
    init: function() {
        this.setupEventListeners();
        this.startStatusPolling();
        console.log('Session controls initialized');
    },
    
    /**
     * Set up event listeners for session controls
     */
    setupEventListeners: function() {
        // Session form submission
        const sessionForm = document.getElementById('session-form');
        if (sessionForm) {
            sessionForm.addEventListener('submit', function(event) {
                event.preventDefault();
                SessionControls.startSession(this);
            });
        }
        
        // Stop session form submission
        const stopSessionForm = document.getElementById('stop-session-form');
        if (stopSessionForm) {
            stopSessionForm.addEventListener('submit', function(event) {
                event.preventDefault();
                SessionControls.stopSession();
            });
        }
        
        // Toggle checkboxes
        const checkboxes = document.querySelectorAll('#session-form input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                SessionControls.updateToggleStatus(this);
            });
        });
    },
    
    /**
     * Start a capture session
     * @param {HTMLFormElement} form - The session form
     */
    startSession: function(form) {
        const formData = new FormData(form);
        
        // Show loading state
        const startBtn = document.getElementById('start-session-btn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.value = 'Starting...';
        }
        
        fetch('/start_session', {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                SessionControls.updateUIForRunningSession(data.session_status);
                SessionControls.updateStatus('Session started successfully');
            } else {
                SessionControls.updateStatus('Error: ' + (data.error || 'Failed to start session'));
            }
        })
        .catch(error => {
            console.error('Error starting session:', error);
            SessionControls.updateStatus('Error: Failed to start session');
        })
        .finally(() => {
            // Reset button state
            if (startBtn) {
                startBtn.disabled = false;
                startBtn.value = 'Start Session';
            }
        });
    },
    
    /**
     * Stop the current session
     */
    stopSession: function() {
        const stopBtn = document.getElementById('stop-session-btn');
        if (stopBtn) {
            stopBtn.disabled = true;
            stopBtn.value = 'Stopping...';
        }
        
        fetch('/stop_session', {
            method: 'POST',
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                SessionControls.updateUIForIdleSession();
                SessionControls.updateStatus('Session stopped successfully');
            } else {
                SessionControls.updateStatus('Error: ' + (data.error || 'Failed to stop session'));
            }
        })
        .catch(error => {
            console.error('Error stopping session:', error);
            SessionControls.updateStatus('Error: Failed to stop session');
        })
        .finally(() => {
            // Reset button state
            if (stopBtn) {
                stopBtn.disabled = false;
                stopBtn.value = 'Stop Session';
            }
        });
    },
    
    /**
     * Update UI for running session
     * @param {Object} sessionStatus - Session status data
     */
    updateUIForRunningSession: function(sessionStatus) {
        // Hide start form, show stop form and progress
        const sessionForm = document.getElementById('session-form');
        const stopSessionForm = document.getElementById('stop-session-form');
        const sessionProgress = document.getElementById('session-progress');
        
        if (sessionForm) sessionForm.style.display = 'none';
        if (stopSessionForm) stopSessionForm.style.display = 'block';
        if (sessionProgress) sessionProgress.style.display = 'block';
        
        // Update progress display
        this.updateProgressDisplay(sessionStatus);
    },
    
    /**
     * Update UI for idle session
     */
    updateUIForIdleSession: function() {
        // Show start form, hide stop form and progress
        const sessionForm = document.getElementById('session-form');
        const stopSessionForm = document.getElementById('stop-session-form');
        const sessionProgress = document.getElementById('session-progress');
        
        if (sessionForm) sessionForm.style.display = 'block';
        if (stopSessionForm) stopSessionForm.style.display = 'none';
        if (sessionProgress) sessionProgress.style.display = 'none';
    },
    
    /**
     * Update progress display
     * @param {Object} sessionStatus - Session status data
     */
    updateProgressDisplay: function(sessionStatus) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const sessionName = document.getElementById('session-name');
        const sessionCount = document.getElementById('session-count');
        const sessionTime = document.getElementById('session-time');
        
        if (progressFill) {
            progressFill.style.width = sessionStatus.progress + '%';
        }
        
        if (progressText) {
            progressText.textContent = sessionStatus.progress + '%';
        }
        
        if (sessionName) {
            sessionName.textContent = 'Session: ' + sessionStatus.name;
        }
        
        if (sessionCount) {
            sessionCount.textContent = sessionStatus.images_captured + ' / ' + sessionStatus.total_images + ' images';
        }
        
        if (sessionTime) {
            sessionTime.textContent = 'Elapsed: ' + this.formatTime(sessionStatus.elapsed_time);
        }
    },
    
    /**
     * Format time in seconds to human readable format
     * @param {number} seconds - Time in seconds
     * @returns {string} Formatted time string
     */
    formatTime: function(seconds) {
        if (seconds < 60) {
            return seconds + 's';
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return minutes + 'm ' + remainingSeconds + 's';
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const remainingSeconds = seconds % 60;
            return hours + 'h ' + minutes + 'm ' + remainingSeconds + 's';
        }
    },
    
    /**
     * Update toggle status display
     * @param {HTMLInputElement} checkbox - The checkbox element
     */
    updateToggleStatus: function(checkbox) {
        const statusSpan = checkbox.closest('.toggle-container').querySelector('.toggle-status');
        if (statusSpan) {
            statusSpan.textContent = checkbox.checked ? ' (Enabled)' : ' (Disabled)';
        }
    },
    
    /**
     * Update session status display
     * @param {string} message - Status message
     */
    updateStatus: function(message) {
        const statusElement = document.getElementById('session-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    },
    
    /**
     * Start polling for session status
     */
    startStatusPolling: function() {
        // Poll every 2 seconds for session status
        setInterval(() => {
            this.pollSessionStatus();
        }, 2000);
    },
    
    /**
     * Poll for session status
     */
    pollSessionStatus: function() {
        fetch('/session_status', {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                // Session is running, update UI
                this.updateUIForRunningSession(data);
                this.updateStatus('Session running: ' + data.images_captured + '/' + data.total_images + ' images');
            } else if (data.status === 'completed') {
                // Session completed
                this.updateUIForIdleSession();
                this.updateStatus('Session completed successfully');
            } else if (data.status === 'error') {
                // Session error
                this.updateUIForIdleSession();
                this.updateStatus('Session error occurred');
            } else if (!data.running && data.images_captured >= data.total_images) {
                // Session finished naturally but status hasn't been updated yet
                this.updateUIForIdleSession();
                this.updateStatus('Session completed successfully');
            }
        })
        .catch(error => {
            console.error('Error polling session status:', error);
        });
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    SessionControls.init();
}); 
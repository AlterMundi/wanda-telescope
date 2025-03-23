/**
 * Modern UI functionality for Wanda Telescope interface
 */
const ModernUI = {
    /**
     * Initialize the modern UI components
     */
    init: function() {
        // Set up tab icons click handlers
        this.setupTabs();
        
        // Initialize panel states
        this.initPanelStates();
        
        // Adjust viewport size when window is resized
        window.addEventListener('resize', this.adjustViewport);
        
        // Initial viewport adjustment
        this.adjustViewport();
    },
    
    /**
     * Set up the tab click handlers
     */
    setupTabs: function() {
        const tabIcons = document.querySelectorAll('.tab-icon');
        
        tabIcons.forEach(icon => {
            icon.addEventListener('click', function() {
                const panelId = this.getAttribute('data-panel');
                const parentTab = this.closest('.panel-tab');
                
                // Toggle active state
                if (parentTab.classList.contains('active')) {
                    parentTab.classList.remove('active');
                } else {
                    // Close any open tabs
                    document.querySelectorAll('.panel-tab.active').forEach(tab => {
                        tab.classList.remove('active');
                    });
                    
                    // Open this tab
                    parentTab.classList.add('active');
                }
            });
        });
        
        // Close tab when clicking outside
        document.addEventListener('click', function(event) {
            // If click is outside any panel or tab icon
            if (!event.target.closest('.panel-tab')) {
                document.querySelectorAll('.panel-tab.active').forEach(tab => {
                    tab.classList.remove('active');
                });
            }
        });
    },
    
    /**
     * Adjust the viewport size based on window dimensions
     * to maximize the viewport area for the camera feed
     */
    adjustViewport: function() {
        const viewport = document.querySelector('.fixed-viewport');
        const viewportInner = document.querySelector('.fixed-viewport-inner');
        if (!viewport || !viewportInner) return;
        
        // Calculate optimal dimensions for the viewport
        const headerHeight = 50;
        const statusBarHeight = 40;
        const availableHeight = window.innerHeight - headerHeight - statusBarHeight;
        
        viewport.style.height = `${availableHeight}px`;
        
        // Make the inner viewport fill the entire container
        viewportInner.style.width = '100%';
        viewportInner.style.height = '100%';
    },
    
    /**
     * Initialize panel states (open/closed)
     */
    initPanelStates: function() {
        // Optional: Start with a specific panel open
        // const defaultPanel = document.getElementById('camera-tab');
        // if (defaultPanel) defaultPanel.classList.add('active');
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    ModernUI.init();
});
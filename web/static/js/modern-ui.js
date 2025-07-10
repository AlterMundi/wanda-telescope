/**
 * Modern UI functionality for Wanda Telescope interface
 */
const ModernUI = {
    /**
     * Initialize the modern UI components
     */
    init: function() {
        // Set up menu tab click handlers for new layout
        this.setupMenuTabs();
    },

    /**
     * Set up the menu tab click handlers for the new always-visible menu
     */
    setupMenuTabs: function() {
        const tabs = document.querySelectorAll('.menu-tab');
        const tabContents = document.querySelectorAll('.tab-content');
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                // Hide all tab contents
                tabContents.forEach(tc => tc.classList.remove('active'));
                // Activate this tab and its content
                tab.classList.add('active');
                const tabName = tab.getAttribute('data-tab');
                document.getElementById('tab-' + tabName).classList.add('active');
            });
        });
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    ModernUI.init();
});
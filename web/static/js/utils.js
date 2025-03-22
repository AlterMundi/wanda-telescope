/**
 * Utility functions for Wanda UI
 */
const Utils = {
    /**
     * Format performance level into human-readable labels
     * @param {number} value - Performance slider value (0-5)
     * @return {string} - Human-readable performance label
     */
    performanceLabel: function(value) {
        const labels = ['High Quality', 'Good Quality', 'Balanced', 'Moderate', 'Low CPU', 'Lowest CPU'];
        return labels[parseInt(value)] || 'Balanced';
    }
};
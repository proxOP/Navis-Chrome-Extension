/**
 * Element Highlighter - Visual highlighting of page elements
 */

class ElementHighlighter {
    constructor() {
        this.currentHighlight = null;
        this.highlightTimeout = null;
        this.defaultDuration = 3000; // 3 seconds
        
        // Inject CSS styles
        this.injectStyles();
    }
    
    /**
     * Inject CSS styles for highlighting
     */
    injectStyles() {
        if (document.getElementById('navis-highlight-styles')) {
            return; // Already injected
        }
        
        const style = document.createElement('style');
        style.id = 'navis-highlight-styles';
        style.textContent = `
            .navis-highlight {
                outline: 3px solid #4CAF50 !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.6) !important;
                position: relative !important;
                z-index: 999999 !important;
                animation: navis-pulse 1.5s ease-in-out infinite !important;
            }
            
            @keyframes navis-pulse {
                0%, 100% {
                    box-shadow: 0 0 15px rgba(76, 175, 80, 0.6);
                }
                50% {
                    box-shadow: 0 0 25px rgba(76, 175, 80, 0.9);
                }
            }
            
            .navis-highlight-overlay {
                position: absolute !important;
                pointer-events: none !important;
                z-index: 999998 !important;
                border: 3px solid #4CAF50 !important;
                background: rgba(76, 175, 80, 0.1) !important;
                box-sizing: border-box !important;
                animation: navis-fade-in 0.3s ease-out !important;
            }
            
            @keyframes navis-fade-in {
                from {
                    opacity: 0;
                    transform: scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: scale(1);
                }
            }
            
            .navis-highlight-label {
                position: absolute !important;
                top: -30px !important;
                left: 0 !important;
                background: #4CAF50 !important;
                color: white !important;
                padding: 4px 8px !important;
                border-radius: 4px !important;
                font-size: 12px !important;
                font-family: Arial, sans-serif !important;
                font-weight: bold !important;
                white-space: nowrap !important;
                z-index: 1000000 !important;
                pointer-events: none !important;
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * Highlight an element
     * @param {string} selector - CSS selector for element
     * @param {number} duration - Duration in milliseconds (0 = permanent)
     * @param {string} label - Optional label text
     * @returns {boolean} Success status
     */
    highlightElement(selector, duration = null, label = null) {
        try {
            // Remove any existing highlight
            this.removeHighlight();
            
            // Find element
            const element = document.querySelector(selector);
            if (!element) {
                console.error('[ElementHighlighter] Element not found:', selector);
                return false;
            }
            
            // Scroll element into view
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'nearest'
            });
            
            // Add highlight class
            element.classList.add('navis-highlight');
            
            // Create overlay for better visibility
            const overlay = this.createOverlay(element, label);
            
            this.currentHighlight = {
                element: element,
                overlay: overlay,
                selector: selector
            };
            
            // Set timeout to remove highlight
            const highlightDuration = duration !== null ? duration : this.defaultDuration;
            if (highlightDuration > 0) {
                this.highlightTimeout = setTimeout(() => {
                    this.removeHighlight();
                }, highlightDuration);
            }
            
            console.log('[ElementHighlighter] Highlighted element:', selector);
            return true;
            
        } catch (error) {
            console.error('[ElementHighlighter] Error highlighting element:', error);
            return false;
        }
    }
    
    /**
     * Create overlay for highlighted element
     */
    createOverlay(element, label) {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        const overlay = document.createElement('div');
        overlay.className = 'navis-highlight-overlay';
        overlay.style.top = (rect.top + scrollTop) + 'px';
        overlay.style.left = (rect.left + scrollLeft) + 'px';
        overlay.style.width = rect.width + 'px';
        overlay.style.height = rect.height + 'px';
        
        // Add label if provided
        if (label) {
            const labelElement = document.createElement('div');
            labelElement.className = 'navis-highlight-label';
            labelElement.textContent = label;
            overlay.appendChild(labelElement);
        }
        
        document.body.appendChild(overlay);
        
        return overlay;
    }
    
    /**
     * Remove current highlight
     */
    removeHighlight() {
        if (this.highlightTimeout) {
            clearTimeout(this.highlightTimeout);
            this.highlightTimeout = null;
        }
        
        if (this.currentHighlight) {
            // Remove class from element
            if (this.currentHighlight.element) {
                this.currentHighlight.element.classList.remove('navis-highlight');
            }
            
            // Remove overlay
            if (this.currentHighlight.overlay && this.currentHighlight.overlay.parentNode) {
                this.currentHighlight.overlay.parentNode.removeChild(this.currentHighlight.overlay);
            }
            
            this.currentHighlight = null;
            console.log('[ElementHighlighter] Highlight removed');
        }
    }
    
    /**
     * Update overlay position (for dynamic content)
     */
    updateOverlayPosition() {
        if (!this.currentHighlight || !this.currentHighlight.element) {
            return;
        }
        
        const element = this.currentHighlight.element;
        const overlay = this.currentHighlight.overlay;
        
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        overlay.style.top = (rect.top + scrollTop) + 'px';
        overlay.style.left = (rect.left + scrollLeft) + 'px';
        overlay.style.width = rect.width + 'px';
        overlay.style.height = rect.height + 'px';
    }
    
    /**
     * Check if element is currently highlighted
     */
    isHighlighted() {
        return this.currentHighlight !== null;
    }
    
    /**
     * Get currently highlighted element
     */
    getCurrentHighlight() {
        return this.currentHighlight;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ElementHighlighter;
}

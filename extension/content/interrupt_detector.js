/**
 * Interrupt Detector - Monitors mouse/cursor activity
 * Sends interrupt signals when user interacts with the page
 */

class InterruptDetector {
    constructor() {
        this.isMonitoring = false;
        this.lastMouseMove = 0;
        this.mouseMoveThreshold = 10; // pixels
        this.lastMousePosition = { x: 0, y: 0 };
        this.interruptCallback = null;
        
        // Bind methods
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleMouseDown = this.handleMouseDown.bind(this);
        this.handleClick = this.handleClick.bind(this);
        this.handleKeyPress = this.handleKeyPress.bind(this);
    }
    
    /**
     * Start monitoring for interrupts
     * @param {Function} callback - Function to call when interrupt detected
     */
    startMonitoring(callback) {
        if (this.isMonitoring) {
            console.log('[InterruptDetector] Already monitoring');
            return;
        }
        
        this.interruptCallback = callback;
        this.isMonitoring = true;
        
        // Add event listeners with passive flag for performance
        document.addEventListener('mousemove', this.handleMouseMove, { passive: true });
        document.addEventListener('mousedown', this.handleMouseDown, { passive: true });
        document.addEventListener('click', this.handleClick, { passive: true });
        document.addEventListener('keydown', this.handleKeyPress, { passive: true });
        
        console.log('[InterruptDetector] Started monitoring');
    }
    
    /**
     * Stop monitoring for interrupts
     */
    stopMonitoring() {
        if (!this.isMonitoring) {
            return;
        }
        
        this.isMonitoring = false;
        
        // Remove event listeners
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mousedown', this.handleMouseDown);
        document.removeEventListener('click', this.handleClick);
        document.removeEventListener('keydown', this.handleKeyPress);
        
        console.log('[InterruptDetector] Stopped monitoring');
    }
    
    /**
     * Handle mouse movement
     */
    handleMouseMove(event) {
        const currentPosition = { x: event.clientX, y: event.clientY };
        
        // Calculate distance moved
        const distance = Math.sqrt(
            Math.pow(currentPosition.x - this.lastMousePosition.x, 2) +
            Math.pow(currentPosition.y - this.lastMousePosition.y, 2)
        );
        
        // Only trigger if moved beyond threshold
        if (distance > this.mouseMoveThreshold) {
            this.lastMousePosition = currentPosition;
            this.triggerInterrupt('mouse_movement', {
                position: currentPosition,
                distance: distance
            });
        }
    }
    
    /**
     * Handle mouse down event
     */
    handleMouseDown(event) {
        this.triggerInterrupt('mouse_down', {
            button: event.button,
            position: { x: event.clientX, y: event.clientY }
        });
    }
    
    /**
     * Handle click event
     */
    handleClick(event) {
        this.triggerInterrupt('click', {
            target: event.target.tagName,
            position: { x: event.clientX, y: event.clientY }
        });
    }
    
    /**
     * Handle key press event
     */
    handleKeyPress(event) {
        // Only interrupt on certain keys (not modifier keys)
        if (!['Shift', 'Control', 'Alt', 'Meta'].includes(event.key)) {
            this.triggerInterrupt('key_press', {
                key: event.key
            });
        }
    }
    
    /**
     * Trigger interrupt callback
     */
    triggerInterrupt(type, data) {
        if (!this.isMonitoring || !this.interruptCallback) {
            return;
        }
        
        const interruptData = {
            type: type,
            timestamp: Date.now(),
            data: data
        };
        
        console.log('[InterruptDetector] Interrupt detected:', type);
        
        // Call the callback
        this.interruptCallback(interruptData);
    }
    
    /**
     * Reset detector state
     */
    reset() {
        this.lastMouseMove = 0;
        this.lastMousePosition = { x: 0, y: 0 };
    }
    
    /**
     * Check if currently monitoring
     */
    isActive() {
        return this.isMonitoring;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InterruptDetector;
}

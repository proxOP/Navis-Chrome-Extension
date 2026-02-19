/**
 * Navigation Controller - Handles page navigation and scrolling
 */

class NavigationController {
    constructor() {
        this.isScrolling = false;
        this.scrollAnimationFrame = null;
    }
    
    /**
     * Navigate back in history
     */
    async goBack() {
        try {
            if (window.history.length > 1) {
                window.history.back();
                console.log('[NavigationController] Navigated back');
                return {
                    success: true,
                    action: 'navigate_back',
                    message: 'Successfully navigated back'
                };
            } else {
                console.log('[NavigationController] No history to go back');
                return {
                    success: false,
                    action: 'navigate_back',
                    message: 'No previous page in history'
                };
            }
        } catch (error) {
            console.error('[NavigationController] Error navigating back:', error);
            return {
                success: false,
                action: 'navigate_back',
                message: 'Navigation failed',
                error: error.message
            };
        }
    }
    
    /**
     * Navigate forward in history
     */
    async goForward() {
        try {
            window.history.forward();
            console.log('[NavigationController] Navigated forward');
            return {
                success: true,
                action: 'navigate_forward',
                message: 'Successfully navigated forward'
            };
        } catch (error) {
            console.error('[NavigationController] Error navigating forward:', error);
            return {
                success: false,
                action: 'navigate_forward',
                message: 'Navigation failed',
                error: error.message
            };
        }
    }
    
    /**
     * Scroll up smoothly
     * @param {number} amount - Pixels to scroll (default: 500)
     */
    async scrollUp(amount = 500) {
        try {
            const currentPosition = window.pageYOffset || document.documentElement.scrollTop;
            
            if (currentPosition <= 0) {
                console.log('[NavigationController] Already at top');
                return {
                    success: false,
                    action: 'scroll_up',
                    message: 'Already at top of page',
                    current_position: currentPosition
                };
            }
            
            this.isScrolling = true;
            
            window.scrollBy({
                top: -amount,
                left: 0,
                behavior: 'smooth'
            });
            
            // Wait for scroll to complete
            await this.waitForScrollEnd();
            
            const newPosition = window.pageYOffset || document.documentElement.scrollTop;
            
            console.log('[NavigationController] Scrolled up from', currentPosition, 'to', newPosition);
            
            this.isScrolling = false;
            
            return {
                success: true,
                action: 'scroll_up',
                message: 'Successfully scrolled up',
                previous_position: currentPosition,
                current_position: newPosition,
                pixels_scrolled: currentPosition - newPosition
            };
            
        } catch (error) {
            this.isScrolling = false;
            console.error('[NavigationController] Error scrolling up:', error);
            return {
                success: false,
                action: 'scroll_up',
                message: 'Scroll failed',
                error: error.message
            };
        }
    }
    
    /**
     * Scroll down smoothly
     * @param {number} amount - Pixels to scroll (default: 500)
     */
    async scrollDown(amount = 500) {
        try {
            const currentPosition = window.pageYOffset || document.documentElement.scrollTop;
            const maxScroll = Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            ) - window.innerHeight;
            
            if (currentPosition >= maxScroll) {
                console.log('[NavigationController] Already at bottom');
                return {
                    success: false,
                    action: 'scroll_down',
                    message: 'Already at bottom of page',
                    current_position: currentPosition,
                    max_position: maxScroll
                };
            }
            
            this.isScrolling = true;
            
            window.scrollBy({
                top: amount,
                left: 0,
                behavior: 'smooth'
            });
            
            // Wait for scroll to complete
            await this.waitForScrollEnd();
            
            const newPosition = window.pageYOffset || document.documentElement.scrollTop;
            
            console.log('[NavigationController] Scrolled down from', currentPosition, 'to', newPosition);
            
            this.isScrolling = false;
            
            return {
                success: true,
                action: 'scroll_down',
                message: 'Successfully scrolled down',
                previous_position: currentPosition,
                current_position: newPosition,
                pixels_scrolled: newPosition - currentPosition,
                at_bottom: newPosition >= maxScroll
            };
            
        } catch (error) {
            this.isScrolling = false;
            console.error('[NavigationController] Error scrolling down:', error);
            return {
                success: false,
                action: 'scroll_down',
                message: 'Scroll failed',
                error: error.message
            };
        }
    }
    
    /**
     * Scroll to a specific element
     * @param {string} selector - CSS selector for target element
     */
    async scrollToElement(selector) {
        try {
            const element = document.querySelector(selector);
            
            if (!element) {
                console.error('[NavigationController] Element not found:', selector);
                return {
                    success: false,
                    action: 'scroll_to_element',
                    message: 'Element not found',
                    selector: selector
                };
            }
            
            const currentPosition = window.pageYOffset || document.documentElement.scrollTop;
            
            this.isScrolling = true;
            
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'nearest'
            });
            
            // Wait for scroll to complete
            await this.waitForScrollEnd();
            
            const newPosition = window.pageYOffset || document.documentElement.scrollTop;
            
            console.log('[NavigationController] Scrolled to element:', selector);
            
            this.isScrolling = false;
            
            return {
                success: true,
                action: 'scroll_to_element',
                message: 'Successfully scrolled to element',
                selector: selector,
                previous_position: currentPosition,
                current_position: newPosition
            };
            
        } catch (error) {
            this.isScrolling = false;
            console.error('[NavigationController] Error scrolling to element:', error);
            return {
                success: false,
                action: 'scroll_to_element',
                message: 'Scroll to element failed',
                selector: selector,
                error: error.message
            };
        }
    }
    
    /**
     * Wait for scroll animation to end
     */
    waitForScrollEnd() {
        return new Promise((resolve) => {
            let lastPosition = window.pageYOffset || document.documentElement.scrollTop;
            let samePositionCount = 0;
            
            const checkScroll = () => {
                const currentPosition = window.pageYOffset || document.documentElement.scrollTop;
                
                if (currentPosition === lastPosition) {
                    samePositionCount++;
                    if (samePositionCount >= 3) {
                        // Position stable for 3 checks (~150ms)
                        resolve();
                        return;
                    }
                } else {
                    samePositionCount = 0;
                    lastPosition = currentPosition;
                }
                
                this.scrollAnimationFrame = requestAnimationFrame(checkScroll);
            };
            
            checkScroll();
            
            // Timeout after 2 seconds
            setTimeout(() => {
                if (this.scrollAnimationFrame) {
                    cancelAnimationFrame(this.scrollAnimationFrame);
                }
                resolve();
            }, 2000);
        });
    }
    
    /**
     * Stop any ongoing scroll
     */
    stopScroll() {
        if (this.scrollAnimationFrame) {
            cancelAnimationFrame(this.scrollAnimationFrame);
            this.scrollAnimationFrame = null;
        }
        this.isScrolling = false;
        
        // Stop smooth scroll by scrolling to current position
        const currentPosition = window.pageYOffset || document.documentElement.scrollTop;
        window.scrollTo(0, currentPosition);
        
        console.log('[NavigationController] Scroll stopped');
    }
    
    /**
     * Get current scroll position
     */
    getScrollPosition() {
        return {
            x: window.pageXOffset || document.documentElement.scrollLeft,
            y: window.pageYOffset || document.documentElement.scrollTop
        };
    }
    
    /**
     * Get maximum scroll position
     */
    getMaxScrollPosition() {
        return {
            x: Math.max(
                document.body.scrollWidth,
                document.documentElement.scrollWidth
            ) - window.innerWidth,
            y: Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            ) - window.innerHeight
        };
    }
    
    /**
     * Check if currently scrolling
     */
    isCurrentlyScrolling() {
        return this.isScrolling;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NavigationController;
}

/**
 * Navis Content Script - Main coordinator for page interactions
 */

// Initialize components
const interruptDetector = new InterruptDetector();
const elementHighlighter = new ElementHighlighter();
const navigationController = new NavigationController();
const feedbackCollector = new FeedbackCollector();

// State
let isActionRunning = false;
let currentAction = null;
const BACKEND_URL = 'http://127.0.0.1:8000';

/**
 * Initialize Navis content script
 */
function initializeNavis() {
    console.log('[Navis] Content script initialized');
    
    // Listen for messages from background script
    chrome.runtime.onMessage.addListener(handleMessage);
    
    // Notify background that content script is ready
    chrome.runtime.sendMessage({
        type: 'content_ready',
        url: window.location.href,
        title: document.title
    });
}

/**
 * Handle messages from background script
 */
async function handleMessage(message, sender, sendResponse) {
    console.log('[Navis] Received message:', message.type);
    
    try {
        switch (message.type) {
            case 'start_action':
                await startAction(message.action);
                break;
                
            case 'stop_action':
                await stopAction();
                break;
                
            case 'show_candidates':
                await showCandidateSelection(message.candidates, message.intent, message.page_context);
                break;
                
            case 'show_feedback_form':
                await showFeedbackForm(message.action, message.result);
                break;
                
            case 'navigate_back':
                await executeNavigateBack();
                break;
                
            case 'navigate_forward':
                await executeNavigateForward();
                break;
                
            case 'scroll_up':
                await executeScrollUp(message.amount);
                break;
                
            case 'scroll_down':
                await executeScrollDown(message.amount);
                break;
                
            case 'highlight_element':
                await executeHighlight(message.selector, message.duration, message.label);
                break;
                
            case 'click_element':
                await executeClick(message.selector);
                break;
                
            case 'get_page_info':
                sendResponse(getPageInfo());
                return true;
                
            default:
                console.warn('[Navis] Unknown message type:', message.type);
        }
        
        sendResponse({ success: true });
    } catch (error) {
        console.error('[Navis] Error handling message:', error);
        sendResponse({ success: false, error: error.message });
    }
    
    return true; // Keep message channel open for async response
}

/**
 * Start an action with interrupt monitoring
 */
async function startAction(action) {
    if (isActionRunning) {
        console.warn('[Navis] Action already running');
        return;
    }
    
    isActionRunning = true;
    currentAction = action;
    
    // Start interrupt monitoring
    interruptDetector.startMonitoring(handleInterrupt);
    
    console.log('[Navis] Action started:', action.type);
}

/**
 * Stop current action
 */
async function stopAction() {
    if (!isActionRunning) {
        return;
    }
    
    isActionRunning = false;
    currentAction = null;
    
    // Stop interrupt monitoring
    interruptDetector.stopMonitoring();
    
    // Stop any ongoing scroll
    navigationController.stopScroll();
    
    // Remove any highlights
    elementHighlighter.removeHighlight();
    
    console.log('[Navis] Action stopped');
}

/**
 * Handle interrupt from user
 */
async function handleInterrupt(interruptData) {
    console.log('[Navis] Interrupt detected:', interruptData.type);
    
    // Stop current action
    await stopAction();
    
    // Notify backend
    try {
        await fetch(`${BACKEND_URL}/state/pause`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: interruptData.type })
        });
    } catch (error) {
        console.error('[Navis] Error notifying backend of interrupt:', error);
    }
    
    // Notify background script
    chrome.runtime.sendMessage({
        type: 'action_interrupted',
        interrupt: interruptData
    });
}

/**
 * Execute navigate back
 */
async function executeNavigateBack() {
    console.log('[Navis] Executing navigate back');
    const result = await navigationController.goBack();
    
    // Notify background script
    chrome.runtime.sendMessage({
        type: 'action_completed',
        action: 'navigate_back',
        result: result
    });
    
    return result;
}

/**
 * Execute navigate forward
 */
async function executeNavigateForward() {
    console.log('[Navis] Executing navigate forward');
    const result = await navigationController.goForward();
    
    // Notify background script
    chrome.runtime.sendMessage({
        type: 'action_completed',
        action: 'navigate_forward',
        result: result
    });
    
    return result;
}

/**
 * Execute scroll up
 */
async function executeScrollUp(amount = 500) {
    console.log('[Navis] Executing scroll up');
    const result = await navigationController.scrollUp(amount);
    
    // Notify background script
    chrome.runtime.sendMessage({
        type: 'action_completed',
        action: 'scroll_up',
        result: result
    });
    
    return result;
}

/**
 * Execute scroll down
 */
async function executeScrollDown(amount = 500) {
    console.log('[Navis] Executing scroll down');
    const result = await navigationController.scrollDown(amount);
    
    // Notify background script
    chrome.runtime.sendMessage({
        type: 'action_completed',
        action: 'scroll_down',
        result: result
    });
    
    return result;
}

/**
 * Execute element highlight
 */
async function executeHighlight(selector, duration = 3000, label = null) {
    console.log('[Navis] Executing highlight:', selector);
    const success = elementHighlighter.highlightElement(selector, duration, label);
    
    const result = {
        success: success,
        action: 'highlight',
        selector: selector,
        message: success ? 'Element highlighted' : 'Failed to highlight element'
    };
    
    // Notify background script
    chrome.runtime.sendMessage({
        type: 'action_completed',
        action: 'highlight',
        result: result
    });
    
    return result;
}

/**
 * Execute element click
 */
async function executeClick(selector) {
    console.log('[Navis] Executing click:', selector);
    
    try {
        const element = document.querySelector(selector);
        
        if (!element) {
            throw new Error('Element not found');
        }
        
        // Scroll into view
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
        });
        
        // Wait a bit for scroll
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Highlight before clicking
        elementHighlighter.highlightElement(selector, 1000, 'Clicking...');
        
        // Wait a bit to show highlight
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Click the element
        element.click();
        
        const result = {
            success: true,
            action: 'click',
            selector: selector,
            message: 'Element clicked successfully'
        };
        
        // Notify background script
        chrome.runtime.sendMessage({
            type: 'action_completed',
            action: 'click',
            result: result
        });
        
        return result;
        
    } catch (error) {
        console.error('[Navis] Error clicking element:', error);
        
        const result = {
            success: false,
            action: 'click',
            selector: selector,
            message: 'Click failed',
            error: error.message
        };
        
        // Notify background script
        chrome.runtime.sendMessage({
            type: 'action_completed',
            action: 'click',
            result: result
        });
        
        return result;
    }
}

/**
 * Show candidate selection UI
 */
async function showCandidateSelection(candidates, intent, pageContext) {
    console.log('[Navis] Showing candidate selection:', candidates.length);
    
    return new Promise((resolve) => {
        feedbackCollector.showCandidates(candidates, async (selectedCandidate) => {
            console.log('[Navis] User selected candidate:', selectedCandidate);
            
            // Notify backend of user selection
            try {
                await fetch(`${BACKEND_URL}/rl/record-user-selection`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        candidates: candidates,
                        selected_candidate: selectedCandidate,
                        intent: intent,
                        page_context: pageContext
                    })
                });
            } catch (error) {
                console.error('[Navis] Error recording user selection:', error);
            }
            
            // Notify background script
            chrome.runtime.sendMessage({
                type: 'user_selected_candidate',
                candidate: selectedCandidate,
                intent: intent
            });
            
            resolve(selectedCandidate);
        });
    });
}

/**
 * Show feedback form after action
 */
async function showFeedbackForm(action, result) {
    console.log('[Navis] Showing feedback form for action:', action.type);
    
    return new Promise((resolve) => {
        feedbackCollector.showFeedbackForm(action, result, async (feedback) => {
            console.log('[Navis] User provided feedback:', feedback);
            
            // Notify backend of feedback
            try {
                await fetch(`${BACKEND_URL}/rl/record-action-result`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: action,
                        intent: feedback.intent || {},
                        page_context: getPageInfo(),
                        success: feedback.success,
                        feedback: feedback
                    })
                });
            } catch (error) {
                console.error('[Navis] Error recording feedback:', error);
            }
            
            // Notify background script
            chrome.runtime.sendMessage({
                type: 'user_provided_feedback',
                action: action,
                feedback: feedback
            });
            
            resolve(feedback);
        });
    });
}

/**
 * Get current page information
 */
function getPageInfo() {
    return {
        url: window.location.href,
        title: document.title,
        scroll_position: navigationController.getScrollPosition(),
        max_scroll: navigationController.getMaxScrollPosition(),
        viewport: {
            width: window.innerWidth,
            height: window.innerHeight
        }
    };
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNavis);
} else {
    initializeNavis();
}

console.log('[Navis] Content script loaded');

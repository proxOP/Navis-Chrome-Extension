/**
 * Feedback Collector - Human-in-the-loop learning
 * Shows candidate options and collects user feedback
 */

class FeedbackCollector {
    constructor() {
        this.isShowing = false;
        this.currentCandidates = [];
        this.selectionCallback = null;
        this.feedbackCallback = null;
        
        // Inject styles
        this.injectStyles();
    }
    
    /**
     * Inject CSS styles for feedback UI
     */
    injectStyles() {
        if (document.getElementById('navis-feedback-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'navis-feedback-styles';
        style.textContent = `
            .navis-feedback-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                z-index: 999999;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: navis-fade-in 0.3s ease-out;
            }
            
            .navis-feedback-panel {
                background: white;
                border-radius: 12px;
                padding: 24px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                animation: navis-slide-up 0.3s ease-out;
            }
            
            .navis-feedback-header {
                margin-bottom: 20px;
            }
            
            .navis-feedback-title {
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin: 0 0 8px 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            .navis-feedback-subtitle {
                font-size: 14px;
                color: #666;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            .navis-candidate-list {
                list-style: none;
                padding: 0;
                margin: 0 0 20px 0;
            }
            
            .navis-candidate-item {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            .navis-candidate-item:hover {
                border-color: #4CAF50;
                background: #f5f5f5;
                transform: translateX(4px);
            }
            
            .navis-candidate-item.recommended {
                border-color: #4CAF50;
                background: #e8f5e9;
            }
            
            .navis-candidate-rank {
                display: inline-block;
                width: 24px;
                height: 24px;
                background: #4CAF50;
                color: white;
                border-radius: 50%;
                text-align: center;
                line-height: 24px;
                font-weight: bold;
                font-size: 12px;
                margin-right: 12px;
            }
            
            .navis-candidate-text {
                font-size: 16px;
                color: #333;
                font-weight: 500;
                margin-bottom: 4px;
            }
            
            .navis-candidate-details {
                font-size: 12px;
                color: #666;
                margin-top: 8px;
            }
            
            .navis-candidate-score {
                display: inline-block;
                background: #e3f2fd;
                color: #1976d2;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                margin-right: 8px;
            }
            
            .navis-candidate-confidence {
                display: inline-block;
                background: #fff3e0;
                color: #f57c00;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            
            .navis-feedback-actions {
                display: flex;
                gap: 12px;
                justify-content: flex-end;
            }
            
            .navis-feedback-button {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            .navis-feedback-button-primary {
                background: #4CAF50;
                color: white;
            }
            
            .navis-feedback-button-primary:hover {
                background: #45a049;
            }
            
            .navis-feedback-button-secondary {
                background: #f5f5f5;
                color: #333;
            }
            
            .navis-feedback-button-secondary:hover {
                background: #e0e0e0;
            }
            
            .navis-feedback-form {
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
            }
            
            .navis-feedback-question {
                font-size: 14px;
                color: #333;
                margin-bottom: 12px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            .navis-feedback-options {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .navis-feedback-option {
                padding: 8px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                color: #333;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            .navis-feedback-option:hover {
                border-color: #4CAF50;
                background: #e8f5e9;
            }
            
            .navis-feedback-option.selected {
                border-color: #4CAF50;
                background: #4CAF50;
                color: white;
            }
            
            @keyframes navis-fade-in {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes navis-slide-up {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * Show candidate selection UI
     * @param {Array} candidates - List of candidate elements
     * @param {Object} options - Display options
     * @param {Function} callback - Selection callback
     */
    showCandidates(candidates, options = {}, callback) {
        if (this.isShowing) {
            console.warn('[FeedbackCollector] Already showing candidates');
            return;
        }
        
        this.isShowing = true;
        this.currentCandidates = candidates;
        this.selectionCallback = callback;
        
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'navis-feedback-overlay';
        overlay.id = 'navis-feedback-overlay';
        
        // Create panel
        const panel = document.createElement('div');
        panel.className = 'navis-feedback-panel';
        
        // Header
        const header = document.createElement('div');
        header.className = 'navis-feedback-header';
        header.innerHTML = `
            <h2 class="navis-feedback-title">
                ${options.title || 'Select Target Element'}
            </h2>
            <p class="navis-feedback-subtitle">
                ${options.subtitle || 'I found multiple options. Which one should I use?'}
            </p>
        `;
        
        // Candidate list
        const list = document.createElement('ul');
        list.className = 'navis-candidate-list';
        
        candidates.forEach((candidate, index) => {
            const item = document.createElement('li');
            item.className = 'navis-candidate-item';
            if (index === 0) {
                item.classList.add('recommended');
            }
            
            const text = candidate.text || candidate.aria_label || candidate.title || 'Unnamed element';
            const score = candidate.total_score || candidate.combined_score || 0;
            const confidence = candidate.confidence || 0;
            
            item.innerHTML = `
                <div>
                    <span class="navis-candidate-rank">${index + 1}</span>
                    <span class="navis-candidate-text">${text.substring(0, 50)}</span>
                    ${index === 0 ? '<span style="color: #4CAF50; font-size: 12px;"> (Recommended)</span>' : ''}
                </div>
                <div class="navis-candidate-details">
                    <span class="navis-candidate-score">Score: ${(score * 100).toFixed(0)}%</span>
                    <span class="navis-candidate-confidence">Confidence: ${(confidence * 100).toFixed(0)}%</span>
                    <span style="color: #999; margin-left: 8px;">${candidate.tag || 'unknown'}</span>
                </div>
            `;
            
            item.addEventListener('click', () => {
                this.handleSelection(candidate, index);
            });
            
            list.appendChild(item);
        });
        
        // Actions
        const actions = document.createElement('div');
        actions.className = 'navis-feedback-actions';
        actions.innerHTML = `
            <button class="navis-feedback-button navis-feedback-button-secondary" id="navis-cancel-btn">
                Cancel
            </button>
        `;
        
        // Assemble panel
        panel.appendChild(header);
        panel.appendChild(list);
        panel.appendChild(actions);
        overlay.appendChild(panel);
        
        // Add to page
        document.body.appendChild(overlay);
        
        // Event listeners
        document.getElementById('navis-cancel-btn').addEventListener('click', () => {
            this.hide();
            if (callback) callback(null);
        });
        
        console.log('[FeedbackCollector] Showing candidates');
    }
    
    /**
     * Handle candidate selection
     */
    handleSelection(candidate, index) {
        console.log('[FeedbackCollector] Candidate selected:', index);
        
        this.hide();
        
        if (this.selectionCallback) {
            this.selectionCallback(candidate, index);
        }
    }
    
    /**
     * Show feedback form after action execution
     * @param {Object} action - Executed action
     * @param {Function} callback - Feedback callback
     */
    showFeedbackForm(action, callback) {
        if (this.isShowing) {
            return;
        }
        
        this.isShowing = true;
        this.feedbackCallback = callback;
        
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'navis-feedback-overlay';
        overlay.id = 'navis-feedback-overlay';
        
        // Create panel
        const panel = document.createElement('div');
        panel.className = 'navis-feedback-panel';
        
        panel.innerHTML = `
            <div class="navis-feedback-header">
                <h2 class="navis-feedback-title">How did I do?</h2>
                <p class="navis-feedback-subtitle">
                    I clicked: "${(action.text || 'element').substring(0, 50)}"
                </p>
            </div>
            
            <div class="navis-feedback-form">
                <div class="navis-feedback-question">Was this the correct action?</div>
                <div class="navis-feedback-options">
                    <button class="navis-feedback-option" data-feedback="correct">
                        ✓ Yes, correct
                    </button>
                    <button class="navis-feedback-option" data-feedback="wrong">
                        ✗ No, wrong element
                    </button>
                    <button class="navis-feedback-option" data-feedback="better">
                        ~ There was a better option
                    </button>
                </div>
            </div>
            
            <div class="navis-feedback-actions" style="margin-top: 20px;">
                <button class="navis-feedback-button navis-feedback-button-secondary" id="navis-skip-feedback">
                    Skip
                </button>
            </div>
        `;
        
        overlay.appendChild(panel);
        document.body.appendChild(overlay);
        
        // Event listeners
        panel.querySelectorAll('[data-feedback]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const feedbackType = e.target.dataset.feedback;
                this.handleFeedback(feedbackType);
            });
        });
        
        document.getElementById('navis-skip-feedback').addEventListener('click', () => {
            this.hide();
            if (callback) callback(null);
        });
        
        console.log('[FeedbackCollector] Showing feedback form');
    }
    
    /**
     * Handle feedback submission
     */
    handleFeedback(feedbackType) {
        console.log('[FeedbackCollector] Feedback received:', feedbackType);
        
        const feedbackMap = {
            'correct': 'correct_action',
            'wrong': 'wrong_action',
            'better': 'better_alternative'
        };
        
        this.hide();
        
        if (this.feedbackCallback) {
            this.feedbackCallback({
                type: feedbackMap[feedbackType],
                timestamp: Date.now()
            });
        }
    }
    
    /**
     * Hide feedback UI
     */
    hide() {
        const overlay = document.getElementById('navis-feedback-overlay');
        if (overlay) {
            overlay.remove();
        }
        
        this.isShowing = false;
        this.currentCandidates = [];
        this.selectionCallback = null;
        this.feedbackCallback = null;
        
        console.log('[FeedbackCollector] Hidden');
    }
    
    /**
     * Check if currently showing
     */
    isActive() {
        return this.isShowing;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeedbackCollector;
}

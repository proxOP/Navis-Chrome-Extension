// Navis Extension Popup - Communicates with Python Backend

const BACKEND_URL = 'http://127.0.0.1:8000';

class NavisPopup {
    constructor() {
        this.isListening = false;
        this.currentPlan = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkBackendConnection();
    }
    
    initializeElements() {
        this.voiceButton = document.getElementById('voiceButton');
        this.status = document.getElementById('status');
        this.planSection = document.getElementById('planSection');
        this.planSteps = document.getElementById('planSteps');
        this.executeBtn = document.getElementById('executeBtn');
        this.cancelBtn = document.getElementById('cancelBtn');
        this.backendStatus = document.getElementById('backendStatus');
    }
    
    setupEventListeners() {
        this.voiceButton.addEventListener('click', () => this.handleVoiceInput());
        this.executeBtn.addEventListener('click', () => this.executePlan());
        this.cancelBtn.addEventListener('click', () => this.cancelPlan());
    }
    
    async checkBackendConnection() {
        try {
            const response = await fetch(`${BACKEND_URL}/health`);
            if (response.ok) {
                this.backendStatus.textContent = '✅ Backend connected';
                this.backendStatus.className = 'backend-status connected';
            } else {
                throw new Error('Backend not responding');
            }
        } catch (error) {
            this.backendStatus.textContent = '❌ Backend disconnected - Start Python server';
            this.backendStatus.className = 'backend-status disconnected';
            this.voiceButton.disabled = true;
        }
    }
    
    async handleVoiceInput() {
        if (this.isListening) {
            this.stopListening();
        } else {
            await this.startListening();
        }
    }
    
    async startListening() {
        try {
            this.isListening = true;
            this.voiceButton.textContent = '🛑 Stop Listening';
            this.showStatus('🎤 Listening... Speak your goal', 'listening');
            
            // Get microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Set up MediaRecorder
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                await this.processAudio(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start();
            
            // Auto-stop after 10 seconds
            setTimeout(() => {
                if (this.isListening) {
                    this.stopListening();
                }
            }, 10000);
            
        } catch (error) {
            console.error('Error starting voice input:', error);
            this.showStatus('❌ Microphone access denied', 'error');
            this.resetVoiceButton();
        }
    }
    
    stopListening() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        this.isListening = false;
        this.showStatus('🔄 Processing your request...', 'processing');
    }
    
    async processAudio(audioBlob) {
        try {
            // Convert audio to base64
            const audioBase64 = await this.blobToBase64(audioBlob);
            
            // Get current page info
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            // Send to Python backend
            const response = await fetch(`${BACKEND_URL}/voice/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audio_data: audioBase64.split(',')[1], // Remove data:audio/wav;base64, prefix
                    page_url: tab.url,
                    page_title: tab.title
                })
            });
            
            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }
            
            const intent = await response.json();
            await this.createNavigationPlan(intent, tab);
            
        } catch (error) {
            console.error('Error processing audio:', error);
            this.showStatus('❌ Failed to process voice input', 'error');
            this.resetVoiceButton();
        }
    }
    
    async createNavigationPlan(intent, tab) {
        try {
            this.showStatus('🧠 Creating navigation plan...', 'processing');
            
            // Analyze current page
            const pageAnalysis = await fetch(`${BACKEND_URL}/dom/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    page_url: tab.url
                })
            });
            
            if (!pageAnalysis.ok) {
                throw new Error('Failed to analyze page');
            }
            
            const pageContext = await pageAnalysis.json();
            
            // Create execution plan
            const planResponse = await fetch(`${BACKEND_URL}/plan/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    intent: intent,
                    page_context: pageContext
                })
            });
            
            if (!planResponse.ok) {
                throw new Error('Failed to create plan');
            }
            
            this.currentPlan = await planResponse.json();
            this.displayPlan(this.currentPlan);
            this.hideStatus();
            this.resetVoiceButton();
            
        } catch (error) {
            console.error('Error creating plan:', error);
            this.showStatus('❌ Failed to create navigation plan', 'error');
            this.resetVoiceButton();
        }
    }
    
    displayPlan(plan) {
        this.planSteps.innerHTML = '';
        
        plan.steps.forEach((step, index) => {
            const stepElement = document.createElement('div');
            stepElement.className = `plan-step ${step.requiresConfirmation ? 'confirmation' : ''}`;
            stepElement.innerHTML = `
                <strong>Step ${index + 1}:</strong> ${step.description}
                ${step.requiresConfirmation ? '<br><small>⚠️ Requires confirmation</small>' : ''}
            `;
            this.planSteps.appendChild(stepElement);
        });
        
        this.planSection.style.display = 'block';
    }
    
    async executePlan() {
        if (!this.currentPlan) return;
        
        try {
            this.executeBtn.disabled = true;
            this.executeBtn.textContent = 'Executing...';
            
            // Send plan to content script for execution
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            await chrome.tabs.sendMessage(tab.id, {
                action: 'executePlan',
                plan: this.currentPlan
            });
            
            // Close popup after starting execution
            window.close();
            
        } catch (error) {
            console.error('Error executing plan:', error);
            this.executeBtn.disabled = false;
            this.executeBtn.textContent = 'Execute Plan';
        }
    }
    
    cancelPlan() {
        this.currentPlan = null;
        this.planSection.style.display = 'none';
        this.hideStatus();
    }
    
    showStatus(message, type) {
        this.status.textContent = message;
        this.status.className = `status ${type}`;
        this.status.style.display = 'block';
    }
    
    hideStatus() {
        this.status.style.display = 'none';
    }
    
    resetVoiceButton() {
        this.isListening = false;
        this.voiceButton.textContent = '🎤 Tell me your goal';
        this.voiceButton.disabled = false;
    }
    
    async blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NavisPopup();
});
# Navis - Design Specification

## Architecture Overview

### High-Level Semantic + RL Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Voice Input   │───▶│  Intent Parser   │───▶│  Semantic       │
│   (Speech-to-   │    │  (Single LLM     │    │  Requirements   │
│   Text)         │    │   Call)          │    │  Extractor      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   UI Controller │    │   DOM Analyzer   │    │   Semantic      │
│   (Visual       │    │   (Local, Fast   │    │   Element       │
│   Feedback)     │    │   Element        │    │   Scorer        │
└─────────────────┘    │   Extraction)    │    │   (Intent-aware)│
         ▲              └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌──────────────────┐    ┌─────────────────┐
         │              │   Vision Model   │    │   RL Agent      │
         │              │   (Fallback      │    │   (Learning     │
         │              │   Only)          │    │   from Feedback)│
         │              └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         └──────────────────────────────────────┌─────────────────┐
                                                │   Action        │
                                                │   Selector      │
                                                │   (Confidence   │
                                                │   Based)        │
                                                └─────────────────┘
```

### Component Architecture

#### 1. Chrome Extension Structure
```
navis-extension/
├── manifest.json           # Extension configuration
├── background/
│   ├── service-worker.js   # Background script coordinator
│   ├── intent-parser.js    # LLM integration for intent parsing
│   ├── semantic-scorer.js  # Element relevance scoring engine
│   ├── rl-agent.js         # Reinforcement learning model
│   └── vision-fallback.js  # Vision model integration
├── content/
│   ├── content-script.js   # Main coordinator
│   ├── dom-analyzer.js     # DOM element extraction
│   ├── semantic-analyzer.js # Intent-aware element analysis
│   ├── action-selector.js  # Confidence-based action selection
│   ├── feedback-collector.js # Human feedback collection
│   └── action-executor.js  # Action execution with learning
├── popup/
│   ├── popup.html          # Extension popup UI
│   ├── popup.js            # Popup logic
│   └── popup.css           # Popup styling
├── ui/
│   ├── overlay.js          # Page overlay components
│   ├── voice-input.js      # Voice interface
│   ├── visual-feedback.js  # Highlighting and confidence display
│   ├── feedback-ui.js      # Human feedback collection interface
│   └── learning-progress.js # RL learning progress display
└── assets/
    ├── icons/              # Extension icons
    └── sounds/             # Audio feedback
```

## Core Components Design

### 1. Voice Input System

#### Speech-to-Text Integration
```javascript
class VoiceInputManager {
  constructor() {
    this.recognition = new webkitSpeechRecognition();
    this.isListening = false;
    this.confidenceThreshold = 0.7;
  }
  
  startListening() {
    // Configure speech recognition for goal capture
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';
    
    return new Promise((resolve, reject) => {
      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const confidence = event.results[0][0].confidence;
        resolve({ transcript, confidence });
      };
      
      this.recognition.start();
    });
  }
}
```

### 2. Intent Parser + Semantic Requirements

#### Python Backend - Intent Parser
```python
class IntentParser:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def parse_user_goal(self, voice_input, page_context):
        prompt = f"""
        You are a web navigation intent parser. Parse the user's goal and extract semantic requirements.
        
        User Goal: "{voice_input}"
        Current Page: {page_context['title']}
        Current URL: {page_context['url']}
        
        Return JSON with:
        {{
          "goal": "clear, specific goal statement",
          "action_type": "navigate|search|fill_form|purchase|contact|click|select",
          "target_semantics": {{
            "keywords": ["relevant", "keywords", "from", "goal"],
            "element_types": ["button", "link", "input", "select"],
            "context_clues": ["nearby", "text", "indicators"],
            "visual_hints": ["color", "position", "size", "prominence"]
          }},
          "urgency": "low|medium|high",
          "requires_confirmation": bool,
          "confidence": 0.0-1.0
        }}
        """
        
        response = await self.llm.call(prompt)
        return json.loads(response)
```

#### JavaScript Frontend - Communication Layer
```javascript
class IntentParserClient {
  constructor() {
    this.backendUrl = 'http://localhost:8000';
  }
  
  async parseUserGoal(voiceInput, pageContext) {
    const response = await fetch(`${this.backendUrl}/parse-intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        voice_input: voiceInput,
        page_context: pageContext
      })
    });
    
    return await response.json();
  }
}
```

### 3. Python Backend - Semantic Element Analysis Engine

#### Intent-Aware Element Scoring
```python
class SemanticAnalyzer:
    def __init__(self):
        self.scoring_weights = {
            'text_match': 0.3,
            'semantic_relevance': 0.25,
            'contextual_position': 0.2,
            'visual_prominence': 0.15,
            'interaction_history': 0.1
        }
    
    def analyze_elements(self, elements, intent):
        scored_elements = []
        
        for element in elements:
            scores = {
                'text_match': self.calculate_text_match(element, intent['target_semantics']['keywords']),
                'semantic_relevance': self.calculate_semantic_relevance(element, intent),
                'contextual_position': self.calculate_contextual_score(element, intent),
                'visual_prominence': self.calculate_visual_score(element),
                'interaction_history': self.get_historical_score(element, intent['action_type'])
            }
            
            total_score = sum(score * self.scoring_weights[key] 
                            for key, score in scores.items())
            
            scored_elements.append({
                **element,
                'scores': scores,
                'total_score': total_score,
                'confidence': self.calculate_confidence(scores, total_score)
            })
        
        return sorted(scored_elements, key=lambda x: x['total_score'], reverse=True)
    
    def calculate_text_match(self, element, keywords):
        element_text = (element.get('text', '') + ' ' + element.get('aria_label', '')).lower()
        matches = [kw for kw in keywords if kw.lower() in element_text]
        return len(matches) / len(keywords) if keywords else 0
    
    def calculate_semantic_relevance(self, element, intent):
        # Check if element type matches expected types
        type_match = 0.5 if element.get('type') in intent['target_semantics']['element_types'] else 0
        
        # Check for context clues in nearby elements
        context_match = self.check_context_clues(element, intent['target_semantics']['context_clues'])
        
        return type_match + context_match
    
    def calculate_contextual_score(self, element, intent):
        # Score based on element position and surrounding context
        position_score = self.get_position_relevance(element, intent['action_type'])
        proximity_score = self.get_proximity_to_relevant_elements(element, intent)
        
        return (position_score + proximity_score) / 2
```

#### JavaScript Frontend - Element Analysis Client
```javascript
class SemanticAnalyzerClient {
  constructor() {
    this.backendUrl = 'http://localhost:8000';
  }
  
  async analyzeElements(elements, intent) {
    const response = await fetch(`${this.backendUrl}/analyze-elements`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        elements: elements,
        intent: intent
      })
    });
    
    return await response.json();
  }
}
```

### 4. Python Backend - Reinforcement Learning Agent

#### Learning from Human Feedback
```python
import numpy as np
import json
from datetime import datetime

class RLAgent:
    def __init__(self):
        self.model = self.initialize_model()
        self.experience_buffer = []
        self.learning_rate = 0.01
        self.exploration_rate = 0.1
    
    def select_action(self, candidates, intent, page_context):
        # Epsilon-greedy action selection
        if np.random.random() < self.exploration_rate:
            # Explore: select random high-confidence candidate
            top_candidates = candidates[:3]
            return np.random.choice(top_candidates)
        else:
            # Exploit: use learned policy
            features = self.extract_features(candidates, intent, page_context)
            predictions = self.model.predict(features)
            
            # Combine semantic scores with RL predictions
            combined_candidates = []
            for i, candidate in enumerate(candidates):
                combined_score = candidate['total_score'] * 0.7 + predictions[i] * 0.3
                combined_candidates.append({
                    **candidate,
                    'rl_score': predictions[i],
                    'combined_score': combined_score
                })
            
            return max(combined_candidates, key=lambda x: x['combined_score'])
    
    def record_experience(self, state, action, reward, feedback=None):
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        }
        
        self.experience_buffer.append(experience)
        
        # Learn from experience batch
        if len(self.experience_buffer) >= 10:
            self.update_model()
    
    def update_model(self):
        batch = self.experience_buffer[-10:]
        
        # Convert experiences to training data
        training_data = []
        for exp in batch:
            features = self.extract_features([exp['action']], exp['state']['intent'], exp['state']['page_context'])
            target = self.calculate_target(exp['reward'], exp['feedback'])
            training_data.append({'features': features, 'target': target})
        
        # Update model weights
        self.model.train(training_data)
        
        # Decay exploration rate
        self.exploration_rate = max(0.01, self.exploration_rate * 0.995)
    
    def calculate_target(self, reward, feedback):
        # Combine success/failure with human feedback
        target = reward  # 1 for success, -1 for failure, 0 for neutral
        
        if feedback:
            feedback_adjustments = {
                'correct_action': 0.5,
                'wrong_action': -0.5,
                'better_alternative': -0.2
            }
            target += feedback_adjustments.get(feedback.get('type'), 0)
        
        return max(-1, min(1, target))
    
    def extract_features(self, candidates, intent, page_context):
        # Extract numerical features for ML model
        features = []
        for candidate in candidates:
            feature_vector = [
                candidate.get('total_score', 0),
                len(candidate.get('text', '')),
                candidate.get('position', {}).get('x', 0),
                candidate.get('position', {}).get('y', 0),
                1 if candidate.get('type') in intent.get('target_semantics', {}).get('element_types', []) else 0
            ]
            features.append(feature_vector)
        return np.array(features)
```

#### JavaScript Frontend - RL Client
```javascript
class RLAgentClient {
  constructor() {
    this.backendUrl = 'http://localhost:8000';
  }
  
  async selectAction(candidates, intent, pageContext) {
    const response = await fetch(`${this.backendUrl}/select-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        candidates: candidates,
        intent: intent,
        page_context: pageContext
      })
    });
    
    return await response.json();
  }
  
  async recordExperience(state, action, reward, feedback = null) {
    await fetch(`${this.backendUrl}/record-experience`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        state: state,
        action: action,
        reward: reward,
        feedback: feedback
      })
    });
  }
}
```

### 5. JavaScript Frontend - Action Selector with Confidence

#### Smart Action Selection with Human Feedback
```javascript
class ActionSelector {
  constructor() {
    this.rlAgentClient = new RLAgentClient();
    this.confidenceThreshold = 0.7;
  }
  
  async selectBestAction(candidates, intent, pageContext) {
    // Get RL agent's recommendation from Python backend
    const selectedAction = await this.rlAgentClient.selectAction(candidates, intent, pageContext);
    
    // Check confidence level
    if (selectedAction.confidence < this.confidenceThreshold) {
      // Present top candidates to user for selection
      return await this.requestUserSelection(candidates.slice(0, 3), intent);
    }
    
    return selectedAction;
  }
  
  async requestUserSelection(topCandidates, intent) {
    return new Promise((resolve) => {
      // Show candidates with confidence scores
      this.showCandidateSelection(topCandidates, intent, async (selectedCandidate, feedback) => {
        // Record user's choice for learning
        await this.rlAgentClient.recordExperience(
          { intent, candidates: topCandidates },
          selectedCandidate,
          1, // User selection is positive reward
          { type: 'user_selection', alternative: selectedCandidate }
        );
        
        resolve(selectedCandidate);
      });
    });
  }
  
  async executeAction(action, intent) {
    try {
      const result = await this.performAction(action);
      
      // Record successful execution
      await this.rlAgentClient.recordExperience(
        { intent, action },
        action,
        1 // Success reward
      );
      
      // Collect user feedback
      setTimeout(() => this.collectFeedback(action, intent), 2000);
      
      return result;
    } catch (error) {
      // Record failure
      await this.rlAgentClient.recordExperience(
        { intent, action },
        action,
        -1 // Failure penalty
      );
      
      // Trigger vision fallback
      return await this.triggerVisionFallback(action, error);
    }
  }
  
  async collectFeedback(action, intent) {
    // Show feedback UI
    this.showFeedbackUI(action, intent, async (feedback) => {
      await this.rlAgentClient.recordExperience(
        { intent, action },
        action,
        0, // Neutral reward for feedback
        feedback
      );
    });
  }
}
```

### 6. Vision Fallback System

#### Computer Vision for Edge Cases
```javascript
class VisionFallback {
  constructor(visionModel) {
    this.vision = visionModel;
    this.isActive = false;
  }
  
  async handleFailedAction(step, error, pageContext) {
    console.log(`DOM action failed: ${error.message}. Activating vision fallback.`);
    
    // Capture current page state
    const screenshot = await this.captureScreenshot();
    
    // Use vision model to understand the page
    const visionAnalysis = await this.vision.analyzeScreenshot({
      image: screenshot,
      goal: step.description,
      failedAction: step.action,
      context: pageContext
    });
    
    // Execute vision-guided action
    return await this.executeVisionAction(visionAnalysis);
  }
  
  async executeVisionAction(analysis) {
    // Convert vision coordinates to DOM actions
    const coordinates = analysis.targetCoordinates;
    const element = document.elementFromPoint(coordinates.x, coordinates.y);
    
    if (element) {
      // Try to execute action on discovered element
      element.click();
      return { success: true, method: 'vision_fallback' };
    }
    
    throw new Error('Vision fallback could not complete action');
  }
}

## User Interface Design

### 1. Extension Popup Interface
```html
<!-- popup.html -->
<div class="navis-popup">
  <header>
    <h1>Navis</h1>
    <p>Don't just browse. Arrive.</p>
  </header>
  
  <main>
    <div class="voice-controls">
      <button id="start-voice" class="voice-button">
        🎤 Tell me your goal
      </button>
      <div id="voice-status" class="status-indicator"></div>
    </div>
    
    <div class="current-plan" id="current-plan" hidden>
      <h3>Navigation Plan:</h3>
      <div id="plan-steps" class="plan-steps"></div>
      <div class="plan-actions">
        <button id="execute-plan">Execute Plan</button>
        <button id="modify-plan">Modify</button>
        <button id="cancel-plan">Cancel</button>
      </div>
    </div>
    
    <div class="execution-progress" id="execution-progress" hidden>
      <h3>Progress:</h3>
      <div class="progress-bar">
        <div id="progress-fill" class="progress-fill"></div>
      </div>
      <p id="current-step-description"></p>
      <button id="pause-execution">Pause</button>
    </div>
  </main>
</div>
```

### 2. Plan Visualization System
```javascript
class PlanDisplay {
  showPlan(plan) {
    const planContainer = document.getElementById('plan-steps');
    planContainer.innerHTML = '';
    
    plan.steps.forEach((step, index) => {
      const stepElement = this.createStepElement(step, index);
      planContainer.appendChild(stepElement);
    });
    
    this.showEstimatedTime(plan.estimatedTime);
    this.highlightConfirmationSteps(plan.steps);
  }
  
  createStepElement(step, index) {
    return `
      <div class="plan-step ${step.requiresConfirmation ? 'requires-confirmation' : ''}">
        <span class="step-number">${index + 1}</span>
        <span class="step-description">${step.description}</span>
        ${step.requiresConfirmation ? '<span class="confirmation-badge">⚠️ Confirmation Required</span>' : ''}
      </div>
    `;
  }
}
```

### 3. Enhanced Visual Feedback
```css
/* Hybrid approach visual styles */
.navis-highlight {
  position: absolute;
  border: 3px solid #007bff;
  border-radius: 4px;
  background: rgba(0, 123, 255, 0.1);
  pointer-events: none;
  z-index: 10000;
  animation: pulse 2s infinite;
}

.navis-plan-preview {
  position: fixed;
  top: 20px;
  right: 20px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 10002;
  max-width: 300px;
}

.plan-step {
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.plan-step.requires-confirmation {
  border-left-color: #ffc107;
  background-color: #fff3cd;
}

.plan-step.completed {
  border-left-color: #28a745;
  background-color: #d4edda;
}

.vision-fallback-indicator {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #ff6b35;
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  z-index: 10003;
}
```

## Data Flow Design

### 1. Hybrid Processing Flow
```
Voice Input → Intent Parser → DOM Analyzer → Structured Planner → Action Executor
     ↓             ↓              ↓               ↓               ↓
User Speaks → Goal Structure → Page Context → Execution Plan → Guided Actions
                                                    ↓
                                            Vision Fallback (if needed)
```

### 2. Performance-Optimized Flow
```
Page Load → DOM Analysis (local) → Element Mapping → Context Caching
     ↓           ↓                      ↓               ↓
New Content → Interactive Elements → Semantic IDs → Ready for Planning
```

### 3. Error Handling with Fallback
```
DOM Action Failure → Vision Fallback → Screenshot Analysis → Alternative Action
      ↓                    ↓                 ↓                    ↓
Element Missing → Computer Vision → Visual Element ID → Coordinate Click
```

### 4. Cost-Optimized API Usage
```
User Goal → Intent Parse (LLM Call 1) → Plan Generation (LLM Call 2) → Local Execution
    ↓              ↓                           ↓                          ↓
Single Voice → Structured Intent → Complete Action Plan → DOM-based Actions
                                                              ↓
                                                    Vision API (only if DOM fails)
```

## LLM Architecture Design

### Architecture Comparison Analysis

#### 1. Rejected: Dynamic Agent Creation (LangChain DeepAgent)
```javascript
// This approach was considered but rejected
class RejectedDeepAgent {
  async handleUserCommand(voiceInput) {
    // Creates new agent for each goal - INEFFICIENT
    const agent = create_agent(
      llm=this.llm,
      tools=this.select_relevant_tools(voiceInput), // UNPREDICTABLE
      system_prompt=this.build_context_prompt(voiceInput)
    );
    
    // Agent creates own routine - UNRELIABLE
    return agent.run(voiceInput); // 5-10 LLM calls, 15+ seconds
  }
}
```

**Rejection Reasons:**
- Unpredictable tool selection
- 5-10x more expensive (multiple LLM calls)
- 10-15 second latency from reasoning loops
- Difficult to debug and control

#### 2. Rejected: Pure Vision Approach (Mariner-style)
```javascript
// This approach was considered but rejected for primary use
class RejectedVisionFirst {
  async processGoal(userGoal) {
    while (!this.goalAchieved()) {
      const screenshot = await this.captureScreen(); // EXPENSIVE
      const analysis = await this.visionModel.analyze(screenshot); // SLOW
      await this.executeAction(analysis.nextAction);
    }
  }
}
```

**Rejection Reasons:**
- 10-20x more expensive than text APIs
- 3-5 second latency per action
- Vision hallucination risks
- High bandwidth requirements

#### 3. Chosen: Hybrid DOM + Structured Planning
```javascript
// Our chosen architecture
class HybridNavisAgent {
  async processVoiceGoal(voiceInput) {
    // STEP 1: Parse intent (1 LLM call, ~2 seconds)
    const intent = await this.intentParser.parse(voiceInput);
    
    // STEP 2: Analyze page structure (LOCAL, ~1 second)
    const pageContext = this.domAnalyzer.getPageContext();
    
    // STEP 3: Create execution plan (1 LLM call, ~2 seconds)
    const plan = await this.structuredPlanner.createPlan(intent, pageContext);
    
    // STEP 4: Execute with confirmations (LOCAL, fast)
    return await this.executeWithConfirmation(plan);
  }
}
```

**Selection Reasons:**
- Only 2 LLM calls total
- DOM analysis is local and fast
- Predictable, structured behavior
- 90% cost reduction vs alternatives

### Detailed Component Architecture

#### Intent Parser Design
```javascript
class IntentParser {
  async parse(voiceInput, pageContext) {
    const systemPrompt = `
    You are a web navigation intent parser. Convert user goals into structured format.
    
    Rules:
    - Output valid JSON only
    - Classify action type accurately
    - Determine confirmation requirements
    - Keep goals specific and actionable
    `;
    
    const userPrompt = `
    User Goal: "${voiceInput}"
    Current Page: ${pageContext.title}
    URL: ${pageContext.url}
    
    Parse into JSON:
    {
      "goal": "specific goal statement",
      "actionType": "navigate|search|fillForm|purchase|contact|read",
      "target": "what user seeks",
      "urgency": "low|medium|high",
      "requiresConfirmation": boolean,
      "confidence": 0.0-1.0
    }
    `;
    
    // Single LLM call with structured output
    return await this.llm.generateStructured(systemPrompt, userPrompt);
  }
}
```

#### Structured Planner Design
```javascript
class StructuredPlanner {
  async createPlan(intent, pageContext) {
    const systemPrompt = `
    You are a web navigation planner. Create efficient, step-by-step plans.
    
    Available Tools:
    - click(elementId): Click interactive element
    - scroll(direction, pixels): Scroll page
    - fillField(elementId, value): Fill form field
    - selectOption(elementId, option): Select dropdown
    - navigate(url): Go to different page
    - wait(seconds): Wait for loading
    
    Rules:
    - Use ONLY available tools
    - Maximum 8 steps per plan
    - Include confirmation for sensitive actions
    - Provide clear descriptions
    - Include fallback options
    `;
    
    const userPrompt = `
    Intent: ${JSON.stringify(intent)}
    Page Elements: ${JSON.stringify(pageContext.interactiveElements)}
    Page Structure: ${JSON.stringify(pageContext.landmarks)}
    
    Create JSON plan:
    {
      "planId": "unique_id",
      "goal": "${intent.goal}",
      "estimatedTime": "seconds",
      "confidence": 0.0-1.0,
      "steps": [
        {
          "stepId": 1,
          "action": "tool_name",
          "target": "element_id",
          "description": "human readable",
          "requiresConfirmation": boolean,
          "expectedOutcome": "what happens next"
        }
      ],
      "fallbackOptions": ["alternative approaches"]
    }
    `;
    
    // Single LLM call with structured output
    return await this.llm.generateStructured(systemPrompt, userPrompt);
  }
}
```

#### Vision Fallback Integration
```javascript
class VisionFallback {
  async handleDOMFailure(step, error, pageContext) {
    // Only activate when DOM approach fails
    console.log(`DOM failed: ${error}. Activating vision fallback.`);
    
    const screenshot = await this.captureScreenshot();
    
    const visionPrompt = `
    The DOM-based action failed. Analyze this screenshot to complete the action.
    
    Failed Action: ${step.action}
    Target Description: ${step.description}
    Error: ${error.message}
    
    Find the target element and provide coordinates or alternative approach.
    `;
    
    const analysis = await this.visionModel.analyze(screenshot, visionPrompt);
    return await this.executeVisionAction(analysis);
  }
}
```

### Performance Optimization Strategy

#### API Call Minimization
```javascript
// Efficient call pattern
const processUserGoal = async (voiceInput) => {
  // Call 1: Intent parsing (required)
  const intent = await intentParser.parse(voiceInput, pageContext);
  
  // Call 2: Plan generation (required)
  const plan = await planner.createPlan(intent, pageContext);
  
  // Call 3: Vision fallback (only if DOM fails - <10% of cases)
  // const visionResult = await visionFallback.handle(failedStep);
  
  // Total: 2 calls normally, 3 calls in edge cases
};
```

#### Cost Comparison
```
Traditional ReAct Agent:
- 8-12 LLM calls per goal
- $0.10-0.30 per navigation
- 15-25 seconds total time

Vision-First Approach:
- 3-8 vision API calls
- $0.50-2.00 per navigation  
- 10-20 seconds total time

Our Hybrid Approach:
- 2 LLM calls normally
- $0.01-0.05 per navigation
- 5-8 seconds total time
- 90% cost reduction
```

### Error Handling and Reliability

#### Graceful Degradation Strategy
```javascript
class ReliabilityManager {
  async executeWithFallbacks(plan) {
    for (const step of plan.steps) {
      try {
        // Primary: DOM-based execution
        const result = await this.domExecutor.execute(step);
        if (result.success) continue;
      } catch (domError) {
        try {
          // Fallback: Vision-based execution
          const result = await this.visionFallback.execute(step, domError);
          if (result.success) continue;
        } catch (visionError) {
          // Final fallback: User intervention
          await this.requestUserHelp(step, [domError, visionError]);
        }
      }
    }
  }
}
```

## Security & Privacy Design

### 1. Permission Model
```json
{
  "permissions": [
    "activeTab",
    "scripting",
    "storage"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

### 2. Data Handling
- **No Persistent Storage**: All data cleared on tab close
- **Local Processing**: DOM analysis happens locally
- **API Calls**: Only for LLM intent understanding
- **User Control**: All actions require explicit confirmation

### 3. Content Script Isolation
```javascript
// Isolated execution context
(function() {
  'use strict';
  
  // Navis functionality wrapped in IIFE
  // No global variable pollution
  // Clean event listener management
  
})();
```

## Performance Considerations

### 1. Lazy Loading Strategy
- Load components only when needed
- Defer heavy DOM analysis until user activation
- Cache frequently accessed elements

### 2. Memory Management
- Clean up event listeners on navigation
- Limit stored navigation history
- Garbage collect unused DOM references

### 3. Optimization Targets (Updated for Hybrid Architecture)
- Intent parsing latency < 2s (single LLM call)
- DOM analysis completion < 1s (local processing)
- Plan generation < 2s (single LLM call)
- Visual feedback response < 100ms
- Total goal-to-execution time < 6s
- Memory usage < 50MB per tab
- Vision fallback activation < 10% of cases
- API cost reduction > 90% vs vision-only approaches

## Testing Strategy

### 1. Component Testing
- Voice input accuracy testing
- Intent parsing validation (structured output)
- DOM analysis validation (element detection accuracy)
- Structured plan generation testing
- Pre-defined tool execution testing
- Vision fallback activation and accuracy
- Visual feedback rendering and timing

### 2. Integration Testing
- End-to-end hybrid flow testing
- DOM-to-vision fallback scenarios
- Cross-browser compatibility (Chrome focus)
- Website compatibility testing (top 1000 sites)
- Accessibility compliance validation
- Performance benchmarking (API calls, latency)

### 3. User Testing
- Usability testing with target accessibility users
- Voice command accuracy in real environments
- Plan comprehension and confirmation flow
- Accessibility testing with assistive technologies
- Performance testing on various devices and networks
- Real-world navigation scenario validation
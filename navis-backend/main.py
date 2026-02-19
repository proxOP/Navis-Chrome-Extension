#!/usr/bin/env python3
"""
Navis Backend - Python FastAPI Server
Handles all core logic for the Chrome extension
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn

from voice.voice_manager import VoiceManager
from ai.intent_parser import IntentParser
from ai.semantic_scorer import SemanticScorer
from ai.rl_agent import get_rl_agent
from ai.vision_fallback import VisionFallback
from dom.analyzer import DOMAnalyzer
from state.state_manager import get_state_manager, ActionState, InterruptReason
from execution.navigation_actions import NavigationActions
from execution.scroll_actions import ScrollActions
from execution.click_actions import ClickActions
from execution.action_selector import get_action_selector
from aws.bedrock_client import BedrockClient
from aws.session_manager import SessionManager
from aws.experience_storage import ExperienceStorage

app = FastAPI(title="Navis Backend", version="2.0.0")

# Enable CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
voice_manager = VoiceManager()
intent_parser = IntentParser(use_bedrock=True)  # Use AWS Bedrock for 10-120x cost savings
semantic_scorer = SemanticScorer()
rl_agent = get_rl_agent()
action_selector = get_action_selector()
dom_analyzer = DOMAnalyzer()
state_manager = get_state_manager()

# Initialize AWS components
bedrock_client = BedrockClient()
session_manager = SessionManager()
experience_storage = ExperienceStorage()
vision_fallback = VisionFallback()

# Initialize action executors with shared driver
navigation_actions = NavigationActions(dom_analyzer.driver)
scroll_actions = ScrollActions(dom_analyzer.driver)
click_actions = ClickActions(dom_analyzer.driver)

# Request/Response Models
class VoiceInputRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    page_url: str
    page_title: str

class IntentResponse(BaseModel):
    goal: str
    action_type: str
    target: str
    urgency: str
    requires_confirmation: bool
    confidence: float

class PlanRequest(BaseModel):
    intent: Dict
    page_context: Dict

class ExecutionPlan(BaseModel):
    plan_id: str
    goal: str
    estimated_time: int
    steps: List[Dict]
    fallback_options: List[str]

class ActionRequest(BaseModel):
    step: Dict
    user_confirmed: bool = False

@app.get("/")
async def root():
    return {"message": "Navis Backend is running"}

@app.post("/voice/process", response_model=IntentResponse)
async def process_voice_input(request: VoiceInputRequest):
    """Process voice input and return parsed intent"""
    try:
        # Convert audio to text
        transcript = await voice_manager.speech_to_text(request.audio_data)
        
        # Parse intent
        page_context = {
            "url": request.page_url,
            "title": request.page_title
        }
        
        intent = await intent_parser.parse_user_goal(transcript, page_context)
        return IntentResponse(**intent)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dom/analyze")
async def analyze_page(page_url: str):
    """Analyze page DOM structure"""
    try:
        analysis = await dom_analyzer.analyze_page(page_url)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# State Management Endpoints
@app.get("/state/current")
async def get_current_state():
    """Get current action state"""
    return state_manager.get_current_state()

@app.post("/state/pause")
async def pause_action(reason: str = "user_request"):
    """Pause current action"""
    try:
        interrupt_reason = InterruptReason(reason) if reason in [r.value for r in InterruptReason] else InterruptReason.USER_REQUEST
        success = state_manager.pause_action(interrupt_reason)
        return {
            "success": success,
            "state": state_manager.get_current_state()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/state/resume")
async def resume_action():
    """Resume paused action"""
    try:
        success = state_manager.resume_action()
        return {
            "success": success,
            "state": state_manager.get_current_state()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/state/block")
async def block_action(reason: str):
    """Block current action (requires user intervention)"""
    try:
        success = state_manager.block_action(reason)
        return {
            "success": success,
            "state": state_manager.get_current_state()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Navigation Action Endpoints
@app.post("/action/navigate/back")
async def navigate_back():
    """Navigate to previous page"""
    try:
        if not state_manager.is_action_allowed():
            raise HTTPException(status_code=403, detail="Action not allowed in current state")
        
        result = await navigation_actions.navigate_back()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/action/navigate/forward")
async def navigate_forward():
    """Navigate to next page"""
    try:
        if not state_manager.is_action_allowed():
            raise HTTPException(status_code=403, detail="Action not allowed in current state")
        
        result = await navigation_actions.navigate_forward()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Scroll Action Endpoints
@app.post("/action/scroll/up")
async def scroll_up(amount: Optional[int] = None):
    """Scroll page upward"""
    try:
        if not state_manager.is_action_allowed():
            raise HTTPException(status_code=403, detail="Action not allowed in current state")
        
        result = await scroll_actions.scroll_up(amount)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/action/scroll/down")
async def scroll_down(amount: Optional[int] = None):
    """Scroll page downward"""
    try:
        if not state_manager.is_action_allowed():
            raise HTTPException(status_code=403, detail="Action not allowed in current state")
        
        result = await scroll_actions.scroll_down(amount)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Element Action Endpoints
class HighlightRequest(BaseModel):
    selector: str
    duration: Optional[int] = 3000
    label: Optional[str] = None

class ClickRequest(BaseModel):
    selector: str
    wait_for_element: bool = True

class AnalyzeElementsRequest(BaseModel):
    elements: List[Dict[str, Any]]
    intent: Dict[str, Any]
    interaction_history: Optional[Dict[str, float]] = None

class SelectActionRequest(BaseModel):
    candidates: List[Dict[str, Any]]
    intent: Dict[str, Any]
    page_context: Dict[str, Any]

class RecordExperienceRequest(BaseModel):
    state: Dict[str, Any]
    action: Dict[str, Any]
    reward: float
    next_state: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None

class RecordUserSelectionRequest(BaseModel):
    candidates: List[Dict[str, Any]]
    selected_candidate: Dict[str, Any]
    intent: Dict[str, Any]
    page_context: Dict[str, Any]

class RecordActionResultRequest(BaseModel):
    action: Dict[str, Any]
    intent: Dict[str, Any]
    page_context: Dict[str, Any]
    success: bool
    feedback: Optional[Dict[str, Any]] = None

@app.post("/action/highlight")
async def highlight_element(request: HighlightRequest):
    """Highlight an element (handled by frontend)"""
    return {
        "success": True,
        "action": "highlight",
        "message": "Highlight request received",
        "selector": request.selector,
        "duration": request.duration,
        "label": request.label
    }

@app.post("/action/click")
async def click_element(request: ClickRequest):
    """Click an element"""
    try:
        if not state_manager.is_action_allowed():
            raise HTTPException(status_code=403, detail="Action not allowed in current state")
        
        result = await click_actions.click_element(request.selector, request.wait_for_element)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Semantic + RL Endpoints
@app.post("/semantic/analyze-elements")
async def analyze_elements(request: AnalyzeElementsRequest):
    """Score elements using semantic analysis"""
    try:
        scored_elements = semantic_scorer.score_elements(
            elements=request.elements,
            intent=request.intent,
            interaction_history=request.interaction_history
        )
        
        return {
            "success": True,
            "scored_elements": scored_elements,
            "count": len(scored_elements)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rl/select-action")
async def select_action(request: SelectActionRequest):
    """Select best action using RL agent"""
    try:
        result = await action_selector.select_best_action(
            candidates=request.candidates,
            intent=request.intent,
            page_context=request.page_context
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rl/record-experience")
async def record_experience(request: RecordExperienceRequest):
    """Record experience for RL learning"""
    try:
        # Record in RL agent (in-memory)
        rl_agent.record_experience(
            state=request.state,
            action=request.action,
            reward=request.reward,
            next_state=request.next_state,
            feedback=request.feedback
        )
        
        # Also store in S3 for durable training data
        session_id = request.state.get("session_id", "unknown")
        await experience_storage.store_experience(
            session_id=session_id,
            experience_data={
                "state": request.state,
                "action": request.action,
                "reward": request.reward,
                "next_state": request.next_state,
                "feedback": request.feedback,
                "timestamp": request.state.get("timestamp")
            }
        )
        
        return {
            "success": True,
            "message": "Experience recorded in memory and S3",
            "statistics": rl_agent.get_statistics()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rl/record-user-selection")
async def record_user_selection(request: RecordUserSelectionRequest):
    """Record user's selection for learning"""
    try:
        await action_selector.record_user_selection(
            candidates=request.candidates,
            selected_candidate=request.selected_candidate,
            intent=request.intent,
            page_context=request.page_context
        )
        
        return {
            "success": True,
            "message": "User selection recorded"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rl/record-action-result")
async def record_action_result(request: RecordActionResultRequest):
    """Record action execution result"""
    try:
        await action_selector.record_action_result(
            action=request.action,
            intent=request.intent,
            page_context=request.page_context,
            success=request.success,
            feedback=request.feedback
        )
        
        return {
            "success": True,
            "message": "Action result recorded"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rl/statistics")
async def get_rl_statistics():
    """Get RL agent statistics"""
    return {
        "rl_agent": rl_agent.get_statistics(),
        "action_selector": action_selector.get_statistics()
    }

# AWS Session Management Endpoints
@app.post("/session/create")
async def create_session(session_data: Dict[str, Any]):
    """Create new session in DynamoDB"""
    try:
        session_id = await session_manager.create_session(session_data)
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session from DynamoDB"""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/session/{session_id}")
async def update_session(session_id: str, updates: Dict[str, Any]):
    """Update session in DynamoDB"""
    try:
        success = await session_manager.update_session(session_id, updates)
        return {
            "success": success,
            "message": "Session updated" if success else "Session not found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete session from DynamoDB"""
    try:
        success = await session_manager.delete_session(session_id)
        return {
            "success": success,
            "message": "Session deleted" if success else "Session not found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AWS Experience Storage Endpoints
class StoreExperienceRequest(BaseModel):
    session_id: str
    experience_data: Dict[str, Any]

@app.post("/experience/store")
async def store_experience(request: StoreExperienceRequest):
    """Store RL experience in S3"""
    try:
        success = await experience_storage.store_experience(
            session_id=request.session_id,
            experience_data=request.experience_data
        )
        return {
            "success": success,
            "message": "Experience stored in S3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/experience/store-batch")
async def store_batch_experiences(session_id: str, experiences: List[Dict[str, Any]]):
    """Store batch of RL experiences in S3"""
    try:
        success = await experience_storage.store_batch(
            session_id=session_id,
            experiences=experiences
        )
        return {
            "success": success,
            "count": len(experiences),
            "message": "Batch experiences stored in S3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experience/{session_id}")
async def get_session_experiences(session_id: str):
    """Get all experiences for a session from S3"""
    try:
        experiences = await experience_storage.get_session_experiences(session_id)
        return {
            "success": True,
            "session_id": session_id,
            "count": len(experiences),
            "experiences": experiences
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vision Fallback Endpoints
class VisionFallbackRequest(BaseModel):
    screenshot_base64: str
    intent: Dict[str, Any]
    page_context: Dict[str, Any]
    failed_action: Optional[Dict[str, Any]] = None

@app.post("/vision/analyze")
async def analyze_with_vision(request: VisionFallbackRequest):
    """Use vision fallback when DOM-based actions fail"""
    try:
        result = await vision_fallback.analyze_screenshot(
            screenshot_base64=request.screenshot_base64,
            intent=request.intent,
            page_context=request.page_context,
            failed_action=request.failed_action
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/find-elements")
async def find_elements_with_vision(request: VisionFallbackRequest):
    """Find clickable elements using vision"""
    try:
        elements = await vision_fallback.find_clickable_elements(
            screenshot_base64=request.screenshot_base64,
            intent=request.intent
        )
        return {
            "success": True,
            "count": len(elements),
            "elements": elements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "voice_manager": voice_manager.is_ready(),
            "intent_parser": intent_parser.is_ready(),
            "semantic_scorer": True,
            "rl_agent": True,
            "action_selector": True,
            "dom_analyzer": dom_analyzer.is_ready(),
            "navigation_actions": navigation_actions.is_ready(),
            "scroll_actions": scroll_actions.is_ready(),
            "click_actions": click_actions.is_ready(),
            "bedrock_client": bedrock_client.is_ready(),
            "session_manager": session_manager.is_ready(),
            "experience_storage": experience_storage.is_ready(),
            "vision_fallback": vision_fallback.is_ready()
        },
        "state": state_manager.get_current_state(),
        "rl_statistics": rl_agent.get_statistics()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
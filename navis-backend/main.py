#!/usr/bin/env python3
"""
Navis Backend - Python FastAPI Server
Handles all core logic for the Chrome extension
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn

from voice.voice_manager import VoiceManager
from ai.intent_parser import IntentParser
from ai.structured_planner import StructuredPlanner
from dom.analyzer import DOMAnalyzer
from execution.action_executor import ActionExecutor

app = FastAPI(title="Navis Backend", version="1.0.0")

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
intent_parser = IntentParser()
structured_planner = StructuredPlanner()
dom_analyzer = DOMAnalyzer()
action_executor = ActionExecutor()

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

@app.post("/plan/create", response_model=ExecutionPlan)
async def create_execution_plan(request: PlanRequest):
    """Create structured execution plan"""
    try:
        plan = await structured_planner.create_execution_plan(
            request.intent, 
            request.page_context
        )
        return ExecutionPlan(**plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/action/execute")
async def execute_action(request: ActionRequest):
    """Execute a single action step"""
    try:
        result = await action_executor.execute_step(
            request.step, 
            request.user_confirmed
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "voice_manager": voice_manager.is_ready(),
            "intent_parser": intent_parser.is_ready(),
            "dom_analyzer": dom_analyzer.is_ready(),
            "action_executor": action_executor.is_ready()
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
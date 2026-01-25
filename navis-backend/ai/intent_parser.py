"""
Intent Parser - Uses LLM to understand user goals
"""

import json
import os
from typing import Dict, Any
from openai import OpenAI
from loguru import logger

class IntentParser:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._ready = bool(os.getenv("OPENAI_API_KEY"))
        
    def is_ready(self) -> bool:
        """Check if intent parser is ready"""
        return self._ready
    
    async def parse_user_goal(self, voice_input: str, page_context: Dict) -> Dict[str, Any]:
        """
        Parse user's voice input into structured intent
        
        Args:
            voice_input: Transcribed user speech
            page_context: Current page information
            
        Returns:
            Structured intent dictionary
        """
        try:
            system_prompt = """
            You are a web navigation intent parser. Parse the user's goal into a structured format.
            
            Rules:
            - Output valid JSON only
            - Classify action type accurately  
            - Determine if confirmation is needed for sensitive actions
            - Keep goals specific and actionable
            - Confidence should reflect how clear the intent is
            """
            
            user_prompt = f"""
            User Goal: "{voice_input}"
            Current Page: {page_context.get('title', 'Unknown')}
            Current URL: {page_context.get('url', 'Unknown')}
            
            Parse into JSON format:
            {{
                "goal": "clear, specific goal statement",
                "action_type": "navigate|search|fill_form|purchase|contact|read|click",
                "target": "what user is looking for",
                "urgency": "low|medium|high", 
                "requires_confirmation": boolean,
                "confidence": 0.0-1.0
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse the JSON response
            intent_text = response.choices[0].message.content.strip()
            logger.info(f"Raw LLM response: {intent_text}")
            
            # Clean up the response (remove markdown formatting if present)
            if intent_text.startswith("```json"):
                intent_text = intent_text.replace("```json", "").replace("```", "").strip()
            
            intent = json.loads(intent_text)
            
            # Validate required fields
            required_fields = ["goal", "action_type", "target", "urgency", "requires_confirmation", "confidence"]
            for field in required_fields:
                if field not in intent:
                    raise ValueError(f"Missing required field: {field}")
            
            logger.info(f"Parsed intent: {intent}")
            return intent
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {intent_text}")
            raise ValueError("Failed to parse intent - invalid JSON response")
            
        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            raise ValueError(f"Intent parsing failed: {str(e)}")
    
    def validate_intent(self, intent: Dict) -> bool:
        """Validate intent structure"""
        required_fields = ["goal", "action_type", "target", "urgency", "requires_confirmation", "confidence"]
        
        # Check all required fields exist
        for field in required_fields:
            if field not in intent:
                return False
        
        # Validate action_type values
        valid_actions = ["navigate", "search", "fill_form", "purchase", "contact", "read", "click"]
        if intent["action_type"] not in valid_actions:
            return False
            
        # Validate urgency values
        valid_urgency = ["low", "medium", "high"]
        if intent["urgency"] not in valid_urgency:
            return False
            
        # Validate confidence range
        if not (0.0 <= intent["confidence"] <= 1.0):
            return False
            
        return True
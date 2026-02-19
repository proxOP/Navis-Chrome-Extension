"""
Action Selector - Confidence-based action selection
Decides whether to execute directly or ask user for selection
"""

from typing import Dict, List, Any, Optional
from loguru import logger
from ai.rl_agent import get_rl_agent


class ActionSelector:
    """Selects best action with confidence-based decision making"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.rl_agent = get_rl_agent()
        logger.info(f"ActionSelector initialized with threshold={confidence_threshold}")
    
    async def select_best_action(
        self,
        candidates: List[Dict[str, Any]],
        intent: Dict[str, Any],
        page_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Select best action with confidence checking
        
        Args:
            candidates: List of scored candidate elements
            intent: User intent
            page_context: Current page context
            
        Returns:
            Selection result with action or candidate list
        """
        if not candidates:
            logger.warning("No candidates provided for selection")
            return {
                'requires_user_selection': True,
                'reason': 'no_candidates',
                'top_candidates': [],
                'recommended': None
            }
        
        logger.info(f"Selecting from {len(candidates)} candidates")
        
        # Use RL agent to select action
        selected_action = self.rl_agent.select_action(
            candidates=candidates,
            intent=intent,
            page_context=page_context
        )
        
        # Get confidence
        confidence = selected_action.get('confidence', 0.0)
        combined_score = selected_action.get('combined_score', selected_action.get('total_score', 0.0))
        
        logger.info(
            f"Selected action: {selected_action.get('text', 'unknown')[:30]}, "
            f"confidence={confidence:.2f}, score={combined_score:.2f}"
        )
        
        # Check if confidence is high enough
        if confidence >= self.confidence_threshold and combined_score >= 0.6:
            # High confidence - execute directly
            return {
                'requires_user_selection': False,
                'selected_action': selected_action,
                'confidence': confidence,
                'reason': 'high_confidence',
                'alternatives': candidates[1:4] if len(candidates) > 1 else []
            }
        else:
            # Low confidence - ask user to select
            top_candidates = candidates[:3]
            
            return {
                'requires_user_selection': True,
                'reason': 'low_confidence',
                'confidence': confidence,
                'top_candidates': top_candidates,
                'recommended': selected_action,
                'explanation': self._generate_explanation(selected_action, confidence)
            }
    
    async def record_user_selection(
        self,
        candidates: List[Dict[str, Any]],
        selected_candidate: Dict[str, Any],
        intent: Dict[str, Any],
        page_context: Dict[str, Any]
    ):
        """
        Record user's selection for learning
        
        Args:
            candidates: List of candidates shown to user
            selected_candidate: Candidate user selected
            intent: User intent
            page_context: Page context
        """
        logger.info(f"Recording user selection: {selected_candidate.get('text', 'unknown')[:30]}")
        
        # Create state
        state = {
            'intent': intent,
            'page_context': page_context,
            'candidates': candidates
        }
        
        # Record as positive experience (user selection is implicit approval)
        self.rl_agent.record_experience(
            state=state,
            action=selected_candidate,
            reward=1.0,  # User selection is positive
            feedback={
                'type': 'user_selection',
                'alternative': selected_candidate,
                'was_recommended': selected_candidate == candidates[0]
            }
        )
    
    async def record_action_result(
        self,
        action: Dict[str, Any],
        intent: Dict[str, Any],
        page_context: Dict[str, Any],
        success: bool,
        feedback: Optional[Dict[str, Any]] = None
    ):
        """
        Record action execution result
        
        Args:
            action: Action that was executed
            intent: User intent
            page_context: Page context
            success: Whether action succeeded
            feedback: Optional human feedback
        """
        reward = 1.0 if success else -1.0
        
        logger.info(
            f"Recording action result: success={success}, "
            f"reward={reward}, has_feedback={feedback is not None}"
        )
        
        # Create state
        state = {
            'intent': intent,
            'page_context': page_context,
            'action': action
        }
        
        # Record experience
        self.rl_agent.record_experience(
            state=state,
            action=action,
            reward=reward,
            feedback=feedback
        )
    
    async def record_feedback(
        self,
        action: Dict[str, Any],
        intent: Dict[str, Any],
        page_context: Dict[str, Any],
        feedback_type: str,
        alternative_action: Optional[Dict[str, Any]] = None
    ):
        """
        Record human feedback
        
        Args:
            action: Action that was taken
            intent: User intent
            page_context: Page context
            feedback_type: Type of feedback (correct_action, wrong_action, better_alternative)
            alternative_action: Better alternative if provided
        """
        logger.info(f"Recording feedback: type={feedback_type}")
        
        feedback = {
            'type': feedback_type,
            'alternative': alternative_action,
            'timestamp': None  # Will be set by RL agent
        }
        
        # Determine reward based on feedback
        reward_map = {
            'correct_action': 1.0,
            'wrong_action': -1.0,
            'better_alternative': 0.0  # Neutral, but learn from alternative
        }
        
        reward = reward_map.get(feedback_type, 0.0)
        
        # Create state
        state = {
            'intent': intent,
            'page_context': page_context,
            'action': action
        }
        
        # Record experience
        self.rl_agent.record_experience(
            state=state,
            action=action,
            reward=reward,
            feedback=feedback
        )
        
        # If alternative provided, record it as positive
        if alternative_action and feedback_type == 'better_alternative':
            self.rl_agent.record_experience(
                state=state,
                action=alternative_action,
                reward=1.0,
                feedback={'type': 'user_correction'}
            )
    
    def _generate_explanation(self, action: Dict[str, Any], confidence: float) -> str:
        """
        Generate explanation for why confidence is low
        
        Args:
            action: Selected action
            confidence: Confidence score
            
        Returns:
            Human-readable explanation
        """
        if confidence < 0.3:
            return "Very uncertain - multiple similar options found"
        elif confidence < 0.5:
            return "Uncertain - please verify this is the correct element"
        elif confidence < 0.7:
            return "Moderately confident - please confirm"
        else:
            return "Confident in this selection"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get selector statistics"""
        rl_stats = self.rl_agent.get_statistics()
        
        return {
            'confidence_threshold': self.confidence_threshold,
            'rl_agent': rl_stats
        }
    
    def set_confidence_threshold(self, threshold: float):
        """Update confidence threshold"""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"Confidence threshold updated to {threshold}")
        else:
            logger.warning(f"Invalid threshold: {threshold}, must be between 0 and 1")


# Global action selector instance
_action_selector = None


def get_action_selector() -> ActionSelector:
    """Get or create global action selector instance"""
    global _action_selector
    if _action_selector is None:
        _action_selector = ActionSelector()
    return _action_selector

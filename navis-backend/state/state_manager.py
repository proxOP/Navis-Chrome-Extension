"""
State Manager - Tracks and manages action states
Handles pause/resume logic and blocking conditions
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
import asyncio


class ActionState(str, Enum):
    """Possible states for an action"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class InterruptReason(str, Enum):
    """Reasons for action interruption"""
    MOUSE_MOVEMENT = "mouse_movement"
    CURSOR_ACTIVITY = "cursor_activity"
    USER_REQUEST = "user_request"
    BLOCKING_DETECTED = "blocking_detected"
    ERROR = "error"


class StateManager:
    """Manages action execution state and transitions"""
    
    def __init__(self):
        self.current_state = ActionState.IDLE
        self.current_action: Optional[Dict[str, Any]] = None
        self.interrupt_reason: Optional[str] = None
        self.blocking_reason: Optional[str] = None
        self.state_history: list = []
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Initially not paused
        
        logger.info("StateManager initialized")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state information"""
        return {
            "state": self.current_state.value,
            "action": self.current_action,
            "interrupt_reason": self.interrupt_reason,
            "blocking_reason": self.blocking_reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def start_action(self, action: Dict[str, Any]) -> bool:
        """
        Start a new action
        
        Args:
            action: Action details
            
        Returns:
            True if action started successfully
        """
        if self.current_state not in [ActionState.IDLE, ActionState.COMPLETED, ActionState.FAILED]:
            logger.warning(f"Cannot start action in state: {self.current_state}")
            return False
        
        self.current_action = action
        self._transition_to(ActionState.RUNNING)
        self.interrupt_reason = None
        self.blocking_reason = None
        self.pause_event.set()  # Ensure not paused
        
        logger.info(f"Action started: {action.get('action_type', 'unknown')}")
        return True
    
    def pause_action(self, reason: InterruptReason) -> bool:
        """
        Pause the current action
        
        Args:
            reason: Reason for pausing
            
        Returns:
            True if action paused successfully
        """
        if self.current_state != ActionState.RUNNING:
            logger.warning(f"Cannot pause action in state: {self.current_state}")
            return False
        
        self.interrupt_reason = reason.value
        self._transition_to(ActionState.PAUSED)
        self.pause_event.clear()  # Set pause flag
        
        logger.info(f"Action paused: {reason.value}")
        return True
    
    def resume_action(self) -> bool:
        """
        Resume a paused action
        
        Returns:
            True if action resumed successfully
        """
        if self.current_state != ActionState.PAUSED:
            logger.warning(f"Cannot resume action in state: {self.current_state}")
            return False
        
        self._transition_to(ActionState.RUNNING)
        self.interrupt_reason = None
        self.pause_event.set()  # Clear pause flag
        
        logger.info("Action resumed")
        return True
    
    def block_action(self, reason: str) -> bool:
        """
        Block the current action (requires user intervention)
        
        Args:
            reason: Reason for blocking
            
        Returns:
            True if action blocked successfully
        """
        if self.current_state not in [ActionState.RUNNING, ActionState.PAUSED]:
            logger.warning(f"Cannot block action in state: {self.current_state}")
            return False
        
        self.blocking_reason = reason
        self._transition_to(ActionState.BLOCKED)
        self.pause_event.clear()  # Set pause flag
        
        logger.warning(f"Action blocked: {reason}")
        return True
    
    def unblock_action(self) -> bool:
        """
        Unblock a blocked action (user completed intervention)
        
        Returns:
            True if action unblocked successfully
        """
        if self.current_state != ActionState.BLOCKED:
            logger.warning(f"Cannot unblock action in state: {self.current_state}")
            return False
        
        self._transition_to(ActionState.PAUSED)
        self.blocking_reason = None
        
        logger.info("Action unblocked, now paused awaiting resume")
        return True
    
    def complete_action(self, success: bool = True) -> bool:
        """
        Mark current action as completed
        
        Args:
            success: Whether action completed successfully
            
        Returns:
            True if state updated successfully
        """
        if self.current_state not in [ActionState.RUNNING, ActionState.PAUSED]:
            logger.warning(f"Cannot complete action in state: {self.current_state}")
            return False
        
        new_state = ActionState.COMPLETED if success else ActionState.FAILED
        self._transition_to(new_state)
        self.pause_event.set()  # Clear any pause
        
        logger.info(f"Action {'completed' if success else 'failed'}")
        return True
    
    def is_action_allowed(self) -> bool:
        """
        Check if action execution is currently allowed
        
        Returns:
            True if action can proceed
        """
        return self.current_state == ActionState.RUNNING and self.pause_event.is_set()
    
    def is_paused(self) -> bool:
        """Check if currently paused"""
        return self.current_state == ActionState.PAUSED
    
    def is_blocked(self) -> bool:
        """Check if currently blocked"""
        return self.current_state == ActionState.BLOCKED
    
    def is_running(self) -> bool:
        """Check if currently running"""
        return self.current_state == ActionState.RUNNING
    
    async def wait_if_paused(self):
        """Wait if action is paused (for use in async action execution)"""
        await self.pause_event.wait()
    
    def reset(self):
        """Reset state manager to idle"""
        self.current_state = ActionState.IDLE
        self.current_action = None
        self.interrupt_reason = None
        self.blocking_reason = None
        self.pause_event.set()
        
        logger.info("StateManager reset to idle")
    
    def _transition_to(self, new_state: ActionState):
        """
        Internal method to transition to a new state
        
        Args:
            new_state: Target state
        """
        old_state = self.current_state
        self.current_state = new_state
        
        # Record state transition
        self.state_history.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.now().isoformat(),
            "action": self.current_action.get("action_type") if self.current_action else None
        })
        
        # Keep history limited
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]
        
        logger.debug(f"State transition: {old_state.value} -> {new_state.value}")
    
    def get_state_history(self, limit: int = 10) -> list:
        """
        Get recent state history
        
        Args:
            limit: Number of recent transitions to return
            
        Returns:
            List of recent state transitions
        """
        return self.state_history[-limit:]


# Global state manager instance
_state_manager = None


def get_state_manager() -> StateManager:
    """Get or create global state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager

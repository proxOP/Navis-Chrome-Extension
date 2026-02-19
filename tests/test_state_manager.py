"""
Tests for State Manager
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'navis-backend'))

from state.state_manager import StateManager, ActionState, InterruptReason


class TestStateManager:
    """Test StateManager functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.state_manager = StateManager()
    
    def test_initial_state(self):
        """Test initial state is IDLE"""
        assert self.state_manager.current_state == ActionState.IDLE
        assert self.state_manager.current_action is None
    
    def test_start_action(self):
        """Test starting an action"""
        action = {"action_type": "scroll_down", "amount": 500}
        success = self.state_manager.start_action(action)
        
        assert success is True
        assert self.state_manager.current_state == ActionState.RUNNING
        assert self.state_manager.current_action == action
    
    def test_pause_action(self):
        """Test pausing an action"""
        # Start action first
        action = {"action_type": "scroll_down"}
        self.state_manager.start_action(action)
        
        # Pause it
        success = self.state_manager.pause_action(InterruptReason.MOUSE_MOVEMENT)
        
        assert success is True
        assert self.state_manager.current_state == ActionState.PAUSED
        assert self.state_manager.interrupt_reason == InterruptReason.MOUSE_MOVEMENT.value
    
    def test_resume_action(self):
        """Test resuming a paused action"""
        # Start and pause action
        action = {"action_type": "scroll_down"}
        self.state_manager.start_action(action)
        self.state_manager.pause_action(InterruptReason.USER_REQUEST)
        
        # Resume it
        success = self.state_manager.resume_action()
        
        assert success is True
        assert self.state_manager.current_state == ActionState.RUNNING
        assert self.state_manager.interrupt_reason is None
    
    def test_block_action(self):
        """Test blocking an action"""
        # Start action first
        action = {"action_type": "click"}
        self.state_manager.start_action(action)
        
        # Block it
        success = self.state_manager.block_action("Login required")
        
        assert success is True
        assert self.state_manager.current_state == ActionState.BLOCKED
        assert self.state_manager.blocking_reason == "Login required"
    
    def test_unblock_action(self):
        """Test unblocking an action"""
        # Start and block action
        action = {"action_type": "click"}
        self.state_manager.start_action(action)
        self.state_manager.block_action("Login required")
        
        # Unblock it
        success = self.state_manager.unblock_action()
        
        assert success is True
        assert self.state_manager.current_state == ActionState.PAUSED
        assert self.state_manager.blocking_reason is None
    
    def test_complete_action_success(self):
        """Test completing an action successfully"""
        # Start action
        action = {"action_type": "scroll_down"}
        self.state_manager.start_action(action)
        
        # Complete it
        success = self.state_manager.complete_action(success=True)
        
        assert success is True
        assert self.state_manager.current_state == ActionState.COMPLETED
    
    def test_complete_action_failure(self):
        """Test completing an action with failure"""
        # Start action
        action = {"action_type": "click"}
        self.state_manager.start_action(action)
        
        # Complete with failure
        success = self.state_manager.complete_action(success=False)
        
        assert success is True
        assert self.state_manager.current_state == ActionState.FAILED
    
    def test_is_action_allowed(self):
        """Test action allowed check"""
        # Initially not allowed (IDLE)
        assert self.state_manager.is_action_allowed() is False
        
        # Start action - should be allowed
        action = {"action_type": "scroll"}
        self.state_manager.start_action(action)
        assert self.state_manager.is_action_allowed() is True
        
        # Pause - should not be allowed
        self.state_manager.pause_action(InterruptReason.MOUSE_MOVEMENT)
        assert self.state_manager.is_action_allowed() is False
    
    def test_state_history(self):
        """Test state history tracking"""
        action = {"action_type": "test"}
        
        # Perform state transitions
        self.state_manager.start_action(action)
        self.state_manager.pause_action(InterruptReason.USER_REQUEST)
        self.state_manager.resume_action()
        self.state_manager.complete_action(success=True)
        
        # Check history
        history = self.state_manager.get_state_history()
        assert len(history) >= 4
        assert history[-1]["to"] == ActionState.COMPLETED.value
    
    def test_reset(self):
        """Test resetting state manager"""
        # Start action and modify state
        action = {"action_type": "test"}
        self.state_manager.start_action(action)
        self.state_manager.pause_action(InterruptReason.MOUSE_MOVEMENT)
        
        # Reset
        self.state_manager.reset()
        
        assert self.state_manager.current_state == ActionState.IDLE
        assert self.state_manager.current_action is None
        assert self.state_manager.interrupt_reason is None
    
    def test_cannot_start_while_running(self):
        """Test cannot start new action while one is running"""
        action1 = {"action_type": "scroll"}
        action2 = {"action_type": "click"}
        
        # Start first action
        success1 = self.state_manager.start_action(action1)
        assert success1 is True
        
        # Try to start second action
        success2 = self.state_manager.start_action(action2)
        assert success2 is False
        assert self.state_manager.current_action == action1
    
    def test_cannot_pause_when_idle(self):
        """Test cannot pause when idle"""
        success = self.state_manager.pause_action(InterruptReason.MOUSE_MOVEMENT)
        assert success is False
    
    def test_cannot_resume_when_not_paused(self):
        """Test cannot resume when not paused"""
        success = self.state_manager.resume_action()
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

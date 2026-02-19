"""
Tests for RL Agent
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'navis-backend'))

from ai.rl_agent import RLAgent


class TestRLAgent:
    """Test RLAgent functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.agent = RLAgent(exploration_rate=0.5)  # Higher for testing
    
    def test_initialization(self):
        """Test agent initializes correctly"""
        assert self.agent is not None
        assert self.agent.exploration_rate == 0.5
        assert len(self.agent.experience_buffer) == 0
        assert len(self.agent.q_table) == 0
    
    def test_select_action_exploration(self):
        """Test action selection during exploration"""
        candidates = [
            {'tag': 'button', 'text': 'Login', 'total_score': 0.9, 'confidence': 0.8},
            {'tag': 'a', 'text': 'Sign in', 'total_score': 0.7, 'confidence': 0.6},
            {'tag': 'button', 'text': 'Submit', 'total_score': 0.5, 'confidence': 0.5}
        ]
        
        intent = {'action_type': 'click', 'goal': 'login'}
        page_context = {'url': 'https://example.com/login'}
        
        selected = self.agent.select_action(candidates, intent, page_context)
        
        assert selected is not None
        assert 'selection_method' in selected
        assert 'rl_metadata' in selected
    
    def test_record_experience(self):
        """Test experience recording"""
        state = {
            'intent': {'action_type': 'click', 'goal': 'login'},
            'page_context': {'url': 'https://example.com'}
        }
        
        action = {
            'tag': 'button',
            'text': 'Login',
            'total_score': 0.9
        }
        
        initial_buffer_size = len(self.agent.experience_buffer)
        
        self.agent.record_experience(
            state=state,
            action=action,
            reward=1.0
        )
        
        assert len(self.agent.experience_buffer) == initial_buffer_size + 1
        assert len(self.agent.q_table) > 0
    
    def test_q_value_update(self):
        """Test Q-value updates"""
        state = {
            'intent': {'action_type': 'click'},
            'page_context': {'url': 'https://example.com'}
        }
        
        action = {'tag': 'button', 'text': 'Login'}
        
        experience = {
            'state': state,
            'action': action,
            'reward': 1.0,
            'next_state': None,
            'feedback': None
        }
        
        initial_q_table_size = len(self.agent.q_table)
        
        self.agent._update_q_value(experience)
        
        assert len(self.agent.q_table) > initial_q_table_size
    
    def test_reward_adjustment(self):
        """Test reward adjustment with feedback"""
        # Positive feedback
        adjusted = self.agent._calculate_adjusted_reward(
            reward=0.5,  # Start lower so boost doesn't get clamped
            feedback={'type': 'correct_action'}
        )
        assert adjusted > 0.5
        
        # Negative feedback
        adjusted = self.agent._calculate_adjusted_reward(
            reward=0.5,
            feedback={'type': 'wrong_action'}
        )
        assert adjusted < 0.5
        
        # No feedback
        adjusted = self.agent._calculate_adjusted_reward(
            reward=0.5,
            feedback=None
        )
        assert adjusted == 0.5
    
    def test_success_history(self):
        """Test success history tracking"""
        action = {'tag': 'button', 'text': 'Login'}
        
        self.agent._update_success_history(action, True)
        self.agent._update_success_history(action, True)
        self.agent._update_success_history(action, False)
        
        action_sig = self.agent._create_action_signature(action)
        success_rate = self.agent.get_success_rate(action_sig)
        
        assert 0.0 <= success_rate <= 1.0
        assert success_rate == pytest.approx(2/3, rel=0.01)
    
    def test_exploration_decay(self):
        """Test exploration rate decay"""
        initial_rate = self.agent.exploration_rate
        
        state = {
            'intent': {'action_type': 'click'},
            'page_context': {'url': 'https://example.com'}
        }
        action = {'tag': 'button', 'text': 'Test'}
        
        # Record multiple experiences
        for _ in range(10):
            self.agent.record_experience(state, action, 1.0)
        
        assert self.agent.exploration_rate < initial_rate
        assert self.agent.exploration_rate >= self.agent.min_exploration_rate
    
    def test_state_signature(self):
        """Test state signature creation"""
        intent = {'action_type': 'click', 'goal': 'login'}
        page_context = {'url': 'https://example.com/login', 'interactive_elements': [1, 2, 3]}
        
        sig = self.agent._create_state_signature(intent, page_context)
        
        assert isinstance(sig, str)
        assert 'click' in sig
    
    def test_action_signature(self):
        """Test action signature creation"""
        action = {
            'tag': 'button',
            'type': 'submit',
            'role': 'button',
            'text': 'Login to account'
        }
        
        sig = self.agent._create_action_signature(action)
        
        assert isinstance(sig, str)
        assert 'button' in sig
        assert 'submit' in sig
    
    def test_statistics(self):
        """Test statistics retrieval"""
        stats = self.agent.get_statistics()
        
        assert 'exploration_rate' in stats
        assert 'experience_count' in stats
        assert 'q_table_size' in stats
        assert 'feature_weights' in stats
    
    def test_batch_update(self):
        """Test batch learning"""
        state = {
            'intent': {'action_type': 'click'},
            'page_context': {'url': 'https://example.com'}
        }
        
        # Record successful experiences
        for i in range(15):
            action = {
                'tag': 'button',
                'text': f'Button{i}',
                'scores': {
                    'text_match': 0.8,
                    'semantic_relevance': 0.9,
                    'contextual_position': 0.7,
                    'visual_prominence': 0.6,
                    'interaction_history': 0.5
                }
            }
            self.agent.record_experience(state, action, 1.0)
        
        # Feature weights should be updated
        assert self.agent.feature_weights is not None
        assert sum(self.agent.feature_weights.values()) == pytest.approx(1.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

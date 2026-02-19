"""
Reinforcement Learning Agent - Learns from feedback and success patterns
Uses epsilon-greedy exploration and experience replay
"""

from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from datetime import datetime
import numpy as np
import json
from collections import deque
import random


class RLAgent:
    """Reinforcement learning agent for action selection"""
    
    def __init__(
        self, 
        learning_rate: float = 0.01,
        exploration_rate: float = 0.1,
        exploration_decay: float = 0.995,
        min_exploration_rate: float = 0.01,
        discount_factor: float = 0.95,
        experience_buffer_size: int = 1000
    ):
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.min_exploration_rate = min_exploration_rate
        self.discount_factor = discount_factor
        
        # Experience replay buffer
        self.experience_buffer = deque(maxlen=experience_buffer_size)
        
        # Q-table: maps (state_signature, action_signature) -> Q-value
        self.q_table: Dict[str, float] = {}
        
        # Success tracking
        self.success_history: Dict[str, List[bool]] = {}
        
        # Feature weights (learned)
        self.feature_weights = {
            'text_match': 0.3,
            'semantic_relevance': 0.25,
            'contextual_position': 0.2,
            'visual_prominence': 0.15,
            'interaction_history': 0.1
        }
        
        logger.info(f"RLAgent initialized with exploration_rate={exploration_rate}")
    
    def select_action(
        self, 
        candidates: List[Dict[str, Any]], 
        intent: Dict[str, Any],
        page_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Select best action using epsilon-greedy strategy
        
        Args:
            candidates: List of scored candidate elements
            intent: User intent
            page_context: Current page context
            
        Returns:
            Selected action with RL score
        """
        if not candidates:
            logger.warning("No candidates provided for action selection")
            return {}
        
        # Create state signature
        state_sig = self._create_state_signature(intent, page_context)
        
        # Epsilon-greedy selection
        if random.random() < self.exploration_rate:
            # EXPLORE: Select random from top candidates
            logger.debug(f"Exploring: selecting random from top {min(3, len(candidates))} candidates")
            selected = random.choice(candidates[:min(3, len(candidates))])
            selected['selection_method'] = 'exploration'
        else:
            # EXPLOIT: Use learned policy
            logger.debug("Exploiting: using learned policy")
            selected = self._exploit_policy(candidates, state_sig)
            selected['selection_method'] = 'exploitation'
        
        # Add RL metadata
        selected['rl_metadata'] = {
            'state_signature': state_sig,
            'exploration_rate': self.exploration_rate,
            'q_value': self._get_q_value(state_sig, self._create_action_signature(selected))
        }
        
        return selected
    
    def _exploit_policy(
        self, 
        candidates: List[Dict[str, Any]], 
        state_sig: str
    ) -> Dict[str, Any]:
        """
        Select action using learned policy (Q-values)
        
        Args:
            candidates: List of candidate elements
            state_sig: State signature
            
        Returns:
            Best action according to policy
        """
        best_candidate = None
        best_combined_score = -float('inf')
        
        for candidate in candidates:
            action_sig = self._create_action_signature(candidate)
            q_value = self._get_q_value(state_sig, action_sig)
            
            # Combine semantic score with Q-value
            semantic_score = candidate.get('total_score', 0)
            combined_score = semantic_score * 0.7 + q_value * 0.3
            
            candidate['rl_score'] = q_value
            candidate['combined_score'] = combined_score
            
            if combined_score > best_combined_score:
                best_combined_score = combined_score
                best_candidate = candidate
        
        return best_candidate if best_candidate else candidates[0]
    
    def record_experience(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float,
        next_state: Optional[Dict[str, Any]] = None,
        feedback: Optional[Dict[str, Any]] = None
    ):
        """
        Record experience for learning
        
        Args:
            state: State before action (intent + page context)
            action: Action taken (selected element)
            reward: Reward received (1 for success, -1 for failure, 0 for neutral)
            next_state: State after action (optional)
            feedback: Human feedback (optional)
        """
        # Adjust reward based on feedback
        adjusted_reward = self._calculate_adjusted_reward(reward, feedback)
        
        # Create experience
        experience = {
            'state': state,
            'action': action,
            'reward': adjusted_reward,
            'next_state': next_state,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to buffer
        self.experience_buffer.append(experience)
        
        # Update Q-value immediately
        self._update_q_value(experience)
        
        # Track success history
        self._update_success_history(action, reward > 0)
        
        # Decay exploration rate
        self.exploration_rate = max(
            self.min_exploration_rate,
            self.exploration_rate * self.exploration_decay
        )
        
        logger.info(
            f"Experience recorded: reward={adjusted_reward:.2f}, "
            f"exploration_rate={self.exploration_rate:.3f}"
        )
        
        # Batch learning every 10 experiences
        if len(self.experience_buffer) % 10 == 0:
            self._batch_update()
    
    def _update_q_value(self, experience: Dict[str, Any]):
        """
        Update Q-value using Q-learning algorithm
        
        Q(s,a) = Q(s,a) + α * [r + γ * max(Q(s',a')) - Q(s,a)]
        """
        state = experience['state']
        action = experience['action']
        reward = experience['reward']
        next_state = experience.get('next_state')
        
        # Create signatures
        state_sig = self._create_state_signature(
            state.get('intent', {}),
            state.get('page_context', {})
        )
        action_sig = self._create_action_signature(action)
        
        # Current Q-value
        current_q = self._get_q_value(state_sig, action_sig)
        
        # Max Q-value for next state (if available)
        max_next_q = 0.0
        if next_state:
            next_state_sig = self._create_state_signature(
                next_state.get('intent', {}),
                next_state.get('page_context', {})
            )
            # Get max Q-value for next state
            next_q_values = [
                q for key, q in self.q_table.items()
                if key.startswith(f"{next_state_sig}:")
            ]
            max_next_q = max(next_q_values) if next_q_values else 0.0
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        # Store updated Q-value
        q_key = f"{state_sig}:{action_sig}"
        self.q_table[q_key] = new_q
        
        logger.debug(f"Q-value updated: {q_key} = {new_q:.3f} (was {current_q:.3f})")
    
    def _batch_update(self):
        """
        Perform batch learning on experience buffer
        
        Updates feature weights based on successful patterns
        """
        if len(self.experience_buffer) < 10:
            return
        
        logger.info("Performing batch update on experience buffer")
        
        # Sample recent experiences
        recent_experiences = list(self.experience_buffer)[-50:]
        
        # Separate successful and failed experiences
        successful = [e for e in recent_experiences if e['reward'] > 0]
        failed = [e for e in recent_experiences if e['reward'] < 0]
        
        if not successful:
            return
        
        # Analyze successful patterns
        successful_features = []
        for exp in successful:
            action = exp['action']
            scores = action.get('scores', {})
            successful_features.append(scores)
        
        # Calculate average feature importance
        if successful_features:
            avg_features = {}
            for key in self.feature_weights.keys():
                values = [f.get(key, 0) for f in successful_features]
                avg_features[key] = sum(values) / len(values) if values else 0
            
            # Adjust weights slightly toward successful patterns
            for key in self.feature_weights.keys():
                current = self.feature_weights[key]
                target = avg_features.get(key, current)
                # Small adjustment (10% toward target)
                self.feature_weights[key] = current * 0.9 + target * 0.1
            
            # Normalize weights
            total = sum(self.feature_weights.values())
            if total > 0:
                self.feature_weights = {
                    k: v / total for k, v in self.feature_weights.items()
                }
            
            logger.info(f"Feature weights updated: {self.feature_weights}")
    
    def _calculate_adjusted_reward(
        self, 
        reward: float, 
        feedback: Optional[Dict[str, Any]]
    ) -> float:
        """
        Adjust reward based on human feedback
        
        Args:
            reward: Base reward (1, 0, or -1)
            feedback: Human feedback dictionary
            
        Returns:
            Adjusted reward
        """
        adjusted = reward
        
        if feedback:
            feedback_type = feedback.get('type')
            
            if feedback_type == 'correct_action':
                adjusted += 0.5  # Boost for correct action
            elif feedback_type == 'wrong_action':
                adjusted -= 0.5  # Penalty for wrong action
            elif feedback_type == 'better_alternative':
                adjusted -= 0.2  # Small penalty, there was a better option
            elif feedback_type == 'user_selection':
                adjusted += 0.3  # User explicitly selected this
        
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, adjusted))
    
    def _update_success_history(self, action: Dict[str, Any], success: bool):
        """Track success history for action types"""
        action_sig = self._create_action_signature(action)
        
        if action_sig not in self.success_history:
            self.success_history[action_sig] = []
        
        self.success_history[action_sig].append(success)
        
        # Keep only recent history (last 20)
        if len(self.success_history[action_sig]) > 20:
            self.success_history[action_sig] = self.success_history[action_sig][-20:]
    
    def get_success_rate(self, action_sig: str) -> float:
        """Get success rate for action signature"""
        if action_sig not in self.success_history:
            return 0.5  # Unknown, neutral
        
        history = self.success_history[action_sig]
        if not history:
            return 0.5
        
        return sum(history) / len(history)
    
    def _get_q_value(self, state_sig: str, action_sig: str) -> float:
        """Get Q-value for state-action pair"""
        q_key = f"{state_sig}:{action_sig}"
        return self.q_table.get(q_key, 0.0)  # Default to 0 for unknown
    
    def _create_state_signature(
        self, 
        intent: Dict[str, Any], 
        page_context: Dict[str, Any]
    ) -> str:
        """
        Create compact state signature for Q-table
        
        Args:
            intent: User intent
            page_context: Page context
            
        Returns:
            State signature string
        """
        parts = [
            intent.get('action_type', 'unknown'),
            page_context.get('url', '')[:50],  # First 50 chars of URL
            str(len(page_context.get('interactive_elements', [])))
        ]
        return ':'.join(parts)
    
    def _create_action_signature(self, action: Dict[str, Any]) -> str:
        """
        Create compact action signature
        
        Args:
            action: Action/element dictionary
            
        Returns:
            Action signature string
        """
        parts = [
            action.get('tag', ''),
            action.get('type', ''),
            action.get('role', ''),
            action.get('text', '')[:20]  # First 20 chars
        ]
        return ':'.join(filter(None, parts)).lower()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'exploration_rate': self.exploration_rate,
            'experience_count': len(self.experience_buffer),
            'q_table_size': len(self.q_table),
            'success_history_size': len(self.success_history),
            'feature_weights': self.feature_weights,
            'avg_q_value': sum(self.q_table.values()) / len(self.q_table) if self.q_table else 0
        }
    
    def save_model(self, filepath: str):
        """Save model to file"""
        model_data = {
            'q_table': self.q_table,
            'success_history': {k: list(v) for k, v in self.success_history.items()},
            'feature_weights': self.feature_weights,
            'exploration_rate': self.exploration_rate,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model from file"""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
            
            self.q_table = model_data.get('q_table', {})
            self.success_history = {
                k: deque(v, maxlen=20) 
                for k, v in model_data.get('success_history', {}).items()
            }
            self.feature_weights = model_data.get('feature_weights', self.feature_weights)
            self.exploration_rate = model_data.get('exploration_rate', self.exploration_rate)
            
            logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")


# Global RL agent instance
_rl_agent = None


def get_rl_agent() -> RLAgent:
    """Get or create global RL agent instance"""
    global _rl_agent
    if _rl_agent is None:
        _rl_agent = RLAgent()
    return _rl_agent

"""
Tests for Semantic Scorer
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'navis-backend'))

from ai.semantic_scorer import SemanticScorer


class TestSemanticScorer:
    """Test SemanticScorer functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.scorer = SemanticScorer()
    
    def test_initialization(self):
        """Test scorer initializes correctly"""
        assert self.scorer is not None
        assert len(self.scorer.scoring_weights) == 5
        assert sum(self.scorer.scoring_weights.values()) == pytest.approx(1.0)
    
    def test_score_elements_empty(self):
        """Test scoring with empty elements"""
        result = self.scorer.score_elements([], {})
        assert result == []
    
    def test_score_elements_basic(self):
        """Test basic element scoring"""
        elements = [
            {
                'tag': 'button',
                'type': 'submit',
                'text': 'Login',
                'aria_label': 'Login button',
                'position': {'x': 100, 'y': 50},
                'size': {'width': 100, 'height': 40},
                'is_displayed': True,
                'is_enabled': True
            },
            {
                'tag': 'a',
                'text': 'Sign in',
                'position': {'x': 200, 'y': 60},
                'size': {'width': 80, 'height': 30},
                'is_displayed': True
            }
        ]
        
        intent = {
            'goal': 'login',
            'action_type': 'click',
            'keywords': ['login', 'sign in']
        }
        
        scored = self.scorer.score_elements(elements, intent)
        
        assert len(scored) == 2
        assert all('total_score' in e for e in scored)
        assert all('confidence' in e for e in scored)
        assert all('scores' in e for e in scored)
        assert all('rank' in e for e in scored)
        
        # First element should score higher (button with "Login")
        assert scored[0]['total_score'] > scored[1]['total_score']
    
    def test_text_matching(self):
        """Test text matching score calculation"""
        element = {
            'text': 'Login to your account',
            'aria_label': 'Login button'
        }
        
        keywords = ['login', 'account']
        score = self.scorer._calculate_text_match(element, keywords)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should match both keywords
    
    def test_semantic_relevance(self):
        """Test semantic relevance calculation"""
        button_element = {
            'tag': 'button',
            'type': 'submit',
            'role': 'button'
        }
        
        intent = {
            'action_type': 'click'
        }
        
        score = self.scorer._calculate_semantic_relevance(button_element, intent)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Button is relevant for click action
    
    def test_contextual_score(self):
        """Test contextual position scoring"""
        header_element = {
            'position': {'x': 100, 'y': 50},  # Near top
            'parent_tags': ['header', 'nav']
        }
        
        intent = {'action_type': 'navigate'}
        
        score = self.scorer._calculate_contextual_score(header_element, intent)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Header elements score higher
    
    def test_visual_score(self):
        """Test visual prominence scoring"""
        prominent_element = {
            'size': {'width': 200, 'height': 50},
            'is_displayed': True,
            'is_enabled': True,
            'z_index': 10
        }
        
        score = self.scorer._calculate_visual_score(prominent_element)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Large, visible element
    
    def test_historical_score(self):
        """Test historical success scoring"""
        element = {
            'tag': 'button',
            'type': 'submit',
            'text': 'Login'
        }
        
        history = {
            'click:button:submit::Login': 0.9  # High success rate
        }
        
        score = self.scorer._get_historical_score(element, 'click', history)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should use historical success
    
    def test_confidence_calculation(self):
        """Test confidence calculation"""
        # High, consistent scores = high confidence
        high_scores = {
            'text_match': 0.9,
            'semantic_relevance': 0.8,
            'contextual_position': 0.85,
            'visual_prominence': 0.9,
            'interaction_history': 0.8
        }
        
        confidence = self.scorer._calculate_confidence(high_scores, 0.85)
        assert confidence > 0.7
        
        # Mixed scores = lower confidence
        mixed_scores = {
            'text_match': 0.9,
            'semantic_relevance': 0.2,
            'contextual_position': 0.8,
            'visual_prominence': 0.3,
            'interaction_history': 0.5
        }
        
        confidence = self.scorer._calculate_confidence(mixed_scores, 0.54)
        assert confidence < 0.7
    
    def test_get_top_candidates(self):
        """Test getting top N candidates"""
        scored_elements = [
            {'total_score': 0.9, 'text': 'A'},
            {'total_score': 0.7, 'text': 'B'},
            {'total_score': 0.5, 'text': 'C'},
            {'total_score': 0.2, 'text': 'D'}
        ]
        
        top_3 = self.scorer.get_top_candidates(scored_elements, n=3, min_score=0.3)
        
        assert len(top_3) == 3
        assert top_3[0]['text'] == 'A'
        assert top_3[2]['text'] == 'C'
    
    def test_explain_score(self):
        """Test score explanation generation"""
        element = {
            'scores': {
                'text_match': 0.8,
                'semantic_relevance': 0.9,
                'contextual_position': 0.7,
                'visual_prominence': 0.6,
                'interaction_history': 0.5
            },
            'total_score': 0.75,
            'confidence': 0.8
        }
        
        explanation = self.scorer.explain_score(element)
        
        assert isinstance(explanation, str)
        assert 'Score:' in explanation
        assert 'Confidence:' in explanation
        assert 'text_match' in explanation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Semantic Element Scorer - Intent-aware element ranking
Scores page elements based on relevance to user's goal
"""

from typing import Dict, List, Any, Optional
from loguru import logger
import re
from difflib import SequenceMatcher


class SemanticScorer:
    """Scores page elements based on semantic relevance to user intent"""
    
    def __init__(self):
        # Scoring weights (sum to 1.0)
        self.scoring_weights = {
            'text_match': 0.30,           # Keyword matching in text
            'semantic_relevance': 0.25,   # Element type and role matching
            'contextual_position': 0.20,  # Position and surrounding context
            'visual_prominence': 0.15,    # Size, visibility, styling
            'interaction_history': 0.10   # Past success with similar elements
        }
        
        # Element type priorities for different actions
        self.action_element_types = {
            'click': ['button', 'a', 'input[type="submit"]', 'input[type="button"]'],
            'navigate': ['a', 'button', 'nav'],
            'fill_form': ['input', 'textarea', 'select'],
            'search': ['input[type="search"]', 'input[type="text"]', 'form'],
            'select': ['select', 'option', 'radio', 'checkbox']
        }
        
        logger.info("SemanticScorer initialized")
    
    def score_elements(
        self, 
        elements: List[Dict[str, Any]], 
        intent: Dict[str, Any],
        interaction_history: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Score all elements based on relevance to intent
        
        Args:
            elements: List of page elements with properties
            intent: Parsed user intent with keywords and action type
            interaction_history: Optional history of successful interactions
            
        Returns:
            List of elements with scores, sorted by relevance
        """
        if not elements:
            logger.warning("No elements to score")
            return []
        
        if not intent:
            logger.warning("No intent provided for scoring")
            return elements
        
        logger.info(f"Scoring {len(elements)} elements for intent: {intent.get('goal', 'unknown')}")
        
        scored_elements = []
        keywords = intent.get('target_semantics', {}).get('keywords', []) or intent.get('keywords', [])
        action_type = intent.get('action_type', 'click')
        
        for element in elements:
            try:
                # Calculate individual scores
                scores = {
                    'text_match': self._calculate_text_match(element, keywords),
                    'semantic_relevance': self._calculate_semantic_relevance(element, intent),
                    'contextual_position': self._calculate_contextual_score(element, intent),
                    'visual_prominence': self._calculate_visual_score(element),
                    'interaction_history': self._get_historical_score(
                        element, action_type, interaction_history
                    )
                }
                
                # Calculate weighted total score
                total_score = sum(
                    score * self.scoring_weights[key] 
                    for key, score in scores.items()
                )
                
                # Calculate confidence based on score distribution
                confidence = self._calculate_confidence(scores, total_score)
                
                scored_elements.append({
                    **element,
                    'scores': scores,
                    'total_score': total_score,
                    'confidence': confidence,
                    'rank': 0  # Will be set after sorting
                })
                
            except Exception as e:
                logger.error(f"Error scoring element: {e}")
                continue
        
        # Sort by total score (descending)
        scored_elements.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Assign ranks
        for i, element in enumerate(scored_elements):
            element['rank'] = i + 1
        
        logger.info(f"Scored {len(scored_elements)} elements, top score: {scored_elements[0]['total_score']:.3f}")
        
        return scored_elements
    
    def _calculate_text_match(self, element: Dict[str, Any], keywords: List[str]) -> float:
        """
        Calculate text matching score
        
        Checks element text, aria-label, title, placeholder for keyword matches
        """
        if not keywords:
            return 0.0
        
        # Gather all text from element
        element_texts = [
            element.get('text', ''),
            element.get('aria_label', ''),
            element.get('title', ''),
            element.get('placeholder', ''),
            element.get('value', '')
        ]
        
        combined_text = ' '.join(filter(None, element_texts)).lower()
        
        if not combined_text:
            return 0.0
        
        # Count keyword matches
        matches = 0
        partial_matches = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Exact match
            if keyword_lower in combined_text:
                matches += 1
            # Partial match (fuzzy)
            elif any(self._fuzzy_match(keyword_lower, word) > 0.8 
                    for word in combined_text.split()):
                partial_matches += 0.5
        
        # Calculate score
        total_matches = matches + partial_matches
        score = min(1.0, total_matches / len(keywords))
        
        return score
    
    def _calculate_semantic_relevance(self, element: Dict[str, Any], intent: Dict[str, Any]) -> float:
        """
        Calculate semantic relevance score
        
        Checks if element type matches expected types for the action
        """
        action_type = intent.get('action_type', 'click')
        element_tag = element.get('tag', '').lower()
        element_type = element.get('type', '').lower()
        element_role = element.get('role', '').lower()
        
        # Get expected element types for this action
        expected_types = self.action_element_types.get(action_type, [])
        
        score = 0.0
        
        # Check tag match
        for expected in expected_types:
            if '[' in expected:
                # Handle input[type="submit"] format
                tag, attr = expected.split('[')
                attr_name, attr_value = attr.rstrip(']').split('=')
                attr_value = attr_value.strip('"\'')
                
                if element_tag == tag and element.get(attr_name) == attr_value:
                    score = 1.0
                    break
            else:
                if element_tag == expected:
                    score = 0.8
                    break
        
        # Check role match
        role_matches = {
            'click': ['button', 'link', 'menuitem'],
            'navigate': ['link', 'navigation'],
            'fill_form': ['textbox', 'searchbox', 'combobox'],
            'search': ['searchbox', 'textbox']
        }
        
        if element_role in role_matches.get(action_type, []):
            score = max(score, 0.7)
        
        # Boost for interactive elements
        if element.get('clickable') or element.get('is_displayed'):
            score = min(1.0, score + 0.1)
        
        return score
    
    def _calculate_contextual_score(self, element: Dict[str, Any], intent: Dict[str, Any]) -> float:
        """
        Calculate contextual position score
        
        Elements in headers, navbars, or prominent positions score higher
        """
        score = 0.5  # Base score
        
        # Check position
        position = element.get('position', {})
        y_pos = position.get('y', 0)
        
        # Elements near top of page (likely in header/nav)
        if y_pos < 200:
            score += 0.3
        elif y_pos < 500:
            score += 0.1
        
        # Check if in semantic containers
        parent_tags = element.get('parent_tags', [])
        if any(tag in ['header', 'nav', 'main'] for tag in parent_tags):
            score += 0.2
        
        # Check context clues from intent
        context_clues = intent.get('target_semantics', {}).get('context_clues', [])
        if context_clues:
            # Check if nearby text contains context clues
            nearby_text = element.get('nearby_text', '').lower()
            if any(clue.lower() in nearby_text for clue in context_clues):
                score += 0.3
        
        return min(1.0, score)
    
    def _calculate_visual_score(self, element: Dict[str, Any]) -> float:
        """
        Calculate visual prominence score
        
        Larger, more visible elements score higher
        """
        score = 0.0
        
        # Check size
        size = element.get('size', {})
        width = size.get('width', 0)
        height = size.get('height', 0)
        area = width * height
        
        # Normalize area score (typical button is ~10,000 px²)
        if area > 0:
            size_score = min(1.0, area / 20000)
            score += size_score * 0.4
        
        # Check visibility
        if element.get('is_displayed', False):
            score += 0.3
        
        if element.get('is_enabled', False):
            score += 0.2
        
        # Check z-index (higher = more prominent)
        z_index = element.get('z_index', 0)
        if z_index > 0:
            score += 0.1
        
        return min(1.0, score)
    
    def _get_historical_score(
        self, 
        element: Dict[str, Any], 
        action_type: str,
        interaction_history: Optional[Dict[str, float]]
    ) -> float:
        """
        Get historical success score
        
        Elements similar to previously successful ones score higher
        """
        if not interaction_history:
            return 0.5  # Neutral score
        
        # Create element signature
        signature = self._create_element_signature(element)
        
        # Check if we have history for this signature
        history_key = f"{action_type}:{signature}"
        
        if history_key in interaction_history:
            return interaction_history[history_key]
        
        # Check for similar elements
        for key, score in interaction_history.items():
            if key.startswith(f"{action_type}:"):
                stored_sig = key.split(':', 1)[1]
                similarity = self._fuzzy_match(signature, stored_sig)
                if similarity > 0.7:
                    return score * similarity
        
        return 0.5  # No history, neutral score
    
    def _calculate_confidence(self, scores: Dict[str, float], total_score: float) -> float:
        """
        Calculate confidence based on score distribution
        
        High confidence when scores are consistently high
        Low confidence when scores are mixed or low
        """
        if not scores:
            return 0.0
        
        # Calculate variance in scores
        score_values = list(scores.values())
        mean_score = sum(score_values) / len(score_values)
        variance = sum((s - mean_score) ** 2 for s in score_values) / len(score_values)
        
        # Low variance + high total = high confidence
        # High variance or low total = low confidence
        
        confidence = total_score * (1 - variance)
        
        return min(1.0, max(0.0, confidence))
    
    def _create_element_signature(self, element: Dict[str, Any]) -> str:
        """Create a signature for element matching"""
        parts = [
            element.get('tag', ''),
            element.get('type', ''),
            element.get('role', ''),
            element.get('text', '')[:20]  # First 20 chars
        ]
        return ':'.join(filter(None, parts)).lower()
    
    def _fuzzy_match(self, str1: str, str2: str) -> float:
        """Calculate fuzzy string similarity (0-1)"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def get_top_candidates(
        self, 
        scored_elements: List[Dict[str, Any]], 
        n: int = 3,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Get top N candidates above minimum score
        
        Args:
            scored_elements: List of scored elements
            n: Number of candidates to return
            min_score: Minimum score threshold
            
        Returns:
            Top N candidates
        """
        # Filter by minimum score
        candidates = [e for e in scored_elements if e['total_score'] >= min_score]
        
        # Return top N
        return candidates[:n]
    
    def explain_score(self, element: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of element score
        
        Args:
            element: Scored element
            
        Returns:
            Explanation string
        """
        scores = element.get('scores', {})
        total = element.get('total_score', 0)
        confidence = element.get('confidence', 0)
        
        explanation = f"Score: {total:.2f} (Confidence: {confidence:.2f})\n"
        explanation += "Breakdown:\n"
        
        for key, value in scores.items():
            weight = self.scoring_weights.get(key, 0)
            contribution = value * weight
            explanation += f"  - {key}: {value:.2f} (weight: {weight:.2f}, contribution: {contribution:.2f})\n"
        
        return explanation

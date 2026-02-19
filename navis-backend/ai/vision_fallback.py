"""
Vision Fallback - Computer vision for edge cases
Uses AWS Rekognition + Bedrock Vision when semantic analysis fails
"""

import base64
import json
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed - Vision fallback will be disabled")


class VisionFallback:
    """Handles vision-based element detection when DOM analysis fails"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.region_name = region_name
        self._ready = False
        self.is_active = False
        
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available - cannot initialize vision fallback")
            return
        
        try:
            # Initialize AWS clients
            self.rekognition = boto3.client('rekognition', region_name=region_name)
            self.bedrock = boto3.client('bedrock-runtime', region_name=region_name)
            self._ready = True
            logger.info("Vision fallback initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize vision fallback: {e}")
            self._ready = False
    
    def is_ready(self) -> bool:
        """Check if vision fallback is ready"""
        return self._ready
    
    async def handle_failed_action(
        self,
        step: Dict[str, Any],
        error: str,
        screenshot_base64: str,
        page_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle failed DOM action using vision
        
        Args:
            step: Failed action step
            error: Error message
            screenshot_base64: Base64 encoded screenshot
            page_context: Page context
            
        Returns:
            Vision analysis result
        """
        if not self._ready:
            return {
                'success': False,
                'error': 'Vision fallback not available'
            }
        
        logger.warning(f"DOM action failed: {error}. Activating vision fallback.")
        self.is_active = True
        
        try:
            # Decode screenshot
            screenshot_bytes = base64.b64decode(screenshot_base64)
            
            # Step 1: Use Rekognition for text detection
            text_elements = await self._detect_text(screenshot_bytes)
            
            # Step 2: Use Bedrock Vision for semantic understanding
            target_element = await self._analyze_with_vision(
                screenshot_bytes=screenshot_bytes,
                goal=step.get('description', ''),
                failed_action=step.get('action', ''),
                text_elements=text_elements,
                page_context=page_context
            )
            
            if target_element:
                return {
                    'success': True,
                    'method': 'vision_fallback',
                    'target_coordinates': target_element.get('coordinates'),
                    'confidence': target_element.get('confidence'),
                    'text': target_element.get('text'),
                    'alternative_action': target_element.get('suggested_action')
                }
            else:
                return {
                    'success': False,
                    'method': 'vision_fallback',
                    'error': 'Could not identify target element visually'
                }
                
        except Exception as e:
            logger.error(f"Vision fallback error: {e}")
            return {
                'success': False,
                'method': 'vision_fallback',
                'error': str(e)
            }
        finally:
            self.is_active = False
    
    async def _detect_text(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Detect text in image using Rekognition
        
        Args:
            image_bytes: Image data
            
        Returns:
            List of detected text elements with positions
        """
        try:
            response = self.rekognition.detect_text(
                Image={'Bytes': image_bytes}
            )
            
            text_elements = []
            for detection in response.get('TextDetections', []):
                if detection['Type'] == 'LINE':  # Only line-level text
                    geometry = detection['Geometry']['BoundingBox']
                    
                    text_elements.append({
                        'text': detection['DetectedText'],
                        'confidence': detection['Confidence'],
                        'bounding_box': {
                            'left': geometry['Left'],
                            'top': geometry['Top'],
                            'width': geometry['Width'],
                            'height': geometry['Height']
                        }
                    })
            
            logger.info(f"Detected {len(text_elements)} text elements")
            return text_elements
            
        except ClientError as e:
            logger.error(f"Rekognition error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error detecting text: {e}")
            return []
    
    async def _analyze_with_vision(
        self,
        screenshot_bytes: bytes,
        goal: str,
        failed_action: str,
        text_elements: List[Dict[str, Any]],
        page_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze screenshot with Bedrock Vision to find target element
        
        Args:
            screenshot_bytes: Screenshot data
            goal: User's goal
            failed_action: Action that failed
            text_elements: Detected text elements
            page_context: Page context
            
        Returns:
            Target element information or None
        """
        try:
            # Encode image for Bedrock
            image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Create prompt for Claude 3 with vision
            prompt = f"""
            The DOM-based action failed. Analyze this screenshot to complete the action.
            
            Failed Action: {failed_action}
            User Goal: {goal}
            Page URL: {page_context.get('url', 'unknown')}
            
            Detected Text Elements:
            {json.dumps(text_elements, indent=2)}
            
            Please identify the target element that matches the user's goal.
            Return JSON with:
            {{
                "text": "text of the target element",
                "coordinates": {{"x": pixel_x, "y": pixel_y}},
                "confidence": 0.0-1.0,
                "suggested_action": "click|type|scroll",
                "reasoning": "why this element matches the goal"
            }}
            
            If you cannot identify a suitable element, return {{"error": "reason"}}.
            """
            
            # Call Bedrock with vision (Claude 3 Sonnet or Opus)
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Use Claude 3 Sonnet with vision
            model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
            
            response = self.bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract and parse response
            if 'content' in response_body and len(response_body['content']) > 0:
                text = response_body['content'][0]['text']
                
                # Clean and parse JSON
                text = text.strip()
                if text.startswith("```json"):
                    text = text.replace("```json", "").replace("```", "").strip()
                
                result = json.loads(text)
                
                if 'error' in result:
                    logger.warning(f"Vision analysis failed: {result['error']}")
                    return None
                
                logger.info(f"Vision identified target: {result.get('text', 'unknown')}")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            return None
    
    def calculate_absolute_coordinates(
        self,
        bounding_box: Dict[str, float],
        image_width: int,
        image_height: int
    ) -> Tuple[int, int]:
        """
        Convert relative bounding box to absolute coordinates
        
        Args:
            bounding_box: Relative bounding box (0-1 scale)
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            (x, y) absolute coordinates
        """
        # Calculate center of bounding box
        center_x = bounding_box['left'] + (bounding_box['width'] / 2)
        center_y = bounding_box['top'] + (bounding_box['height'] / 2)
        
        # Convert to absolute pixels
        abs_x = int(center_x * image_width)
        abs_y = int(center_y * image_height)
        
        return (abs_x, abs_y)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vision fallback statistics"""
        return {
            'is_ready': self._ready,
            'is_active': self.is_active,
            'services': {
                'rekognition': self._ready,
                'bedrock_vision': self._ready
            }
        }


# Global vision fallback instance
_vision_fallback = None


def get_vision_fallback() -> VisionFallback:
    """Get or create global vision fallback instance"""
    global _vision_fallback
    if _vision_fallback is None:
        _vision_fallback = VisionFallback()
    return _vision_fallback

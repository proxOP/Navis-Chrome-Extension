"""
Amazon Bedrock Client - LLM integration with 10-120x cost savings
Replaces OpenAI with AWS Bedrock (Claude 3 Haiku)
"""

import json
import os
from typing import Dict, Any, Optional
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed - AWS features will be disabled")


class BedrockClient:
    """Client for Amazon Bedrock LLM services"""
    
    def __init__(
        self,
        region_name: str = 'us-east-1',
        model_id: str = 'anthropic.claude-3-haiku-20240307-v1:0'
    ):
        self.region_name = region_name
        self.model_id = model_id
        self._ready = False
        
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available - cannot initialize Bedrock client")
            return
        
        try:
            # Initialize Bedrock Runtime client
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region_name
            )
            self._ready = True
            logger.info(f"Bedrock client initialized with model: {model_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self._ready = False
    
    def is_ready(self) -> bool:
        """Check if client is ready"""
        return self._ready
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.1
    ) -> str:
        """
        Generate text using Bedrock
        
        Args:
            system_prompt: System instructions
            user_prompt: User message
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self._ready:
            raise RuntimeError("Bedrock client not initialized")
        
        try:
            # Prepare request body for Claude 3
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            }
            
            logger.debug(f"Calling Bedrock with model: {self.model_id}")
            
            # Invoke model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text from Claude 3 response
            if 'content' in response_body and len(response_body['content']) > 0:
                text = response_body['content'][0]['text']
                logger.debug(f"Bedrock response length: {len(text)} chars")
                return text
            else:
                raise ValueError("Unexpected response format from Bedrock")
                
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise RuntimeError(f"Bedrock API call failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error calling Bedrock: {e}")
            raise
    
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output
        
        Args:
            system_prompt: System instructions
            user_prompt: User message (should request JSON)
            max_tokens: Maximum tokens
            
        Returns:
            Parsed JSON dictionary
        """
        text = await self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.1  # Low temperature for structured output
        )
        
        # Clean up response (remove markdown formatting if present)
        text = text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Bedrock: {e}")
            logger.error(f"Raw response: {text}")
            raise ValueError(f"Invalid JSON response from Bedrock: {str(e)}")
    
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for API call
        
        Claude 3 Haiku pricing (as of 2024):
        - Input: $0.00025 per 1K tokens
        - Output: $0.00125 per 1K tokens
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1000) * 0.00025
        output_cost = (output_tokens / 1000) * 0.00125
        return input_cost + output_cost
    
    def compare_with_openai(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """
        Compare cost with OpenAI GPT-3.5 and GPT-4
        
        Returns:
            Cost comparison dictionary
        """
        bedrock_cost = self.get_cost_estimate(input_tokens, output_tokens)
        
        # OpenAI pricing (as of 2024)
        gpt35_input = (input_tokens / 1000) * 0.0015
        gpt35_output = (output_tokens / 1000) * 0.002
        gpt35_cost = gpt35_input + gpt35_output
        
        gpt4_input = (input_tokens / 1000) * 0.03
        gpt4_output = (output_tokens / 1000) * 0.06
        gpt4_cost = gpt4_input + gpt4_output
        
        return {
            'bedrock_haiku': bedrock_cost,
            'openai_gpt35': gpt35_cost,
            'openai_gpt4': gpt4_cost,
            'savings_vs_gpt35': f"{(1 - bedrock_cost/gpt35_cost) * 100:.1f}%",
            'savings_vs_gpt4': f"{(1 - bedrock_cost/gpt4_cost) * 100:.1f}%"
        }


# Global Bedrock client instance
_bedrock_client = None


def get_bedrock_client() -> BedrockClient:
    """Get or create global Bedrock client instance"""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client

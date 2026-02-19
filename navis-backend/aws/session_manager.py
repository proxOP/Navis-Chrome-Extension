"""
DynamoDB Session Manager - Fast session state storage with TTL
Provides scalable session management with automatic cleanup
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed - DynamoDB features will be disabled")


class SessionManager:
    """Manages session state in DynamoDB"""
    
    def __init__(
        self,
        table_name: str = 'navis-sessions',
        region_name: str = 'us-east-1',
        ttl_hours: int = 24
    ):
        self.table_name = table_name
        self.region_name = region_name
        self.ttl_hours = ttl_hours
        self._ready = False
        
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available - cannot initialize DynamoDB")
            return
        
        try:
            # Initialize DynamoDB resource
            dynamodb = boto3.resource('dynamodb', region_name=region_name)
            self.table = dynamodb.Table(table_name)
            self._ready = True
            logger.info(f"DynamoDB session manager initialized: {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB: {e}")
            self._ready = False
    
    def is_ready(self) -> bool:
        """Check if manager is ready"""
        return self._ready
    
    async def store_session_state(
        self,
        session_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """
        Store session state with TTL
        
        Args:
            session_id: Unique session identifier
            state: Session state dictionary
            
        Returns:
            Success status
        """
        if not self._ready:
            logger.warning("DynamoDB not ready, skipping session storage")
            return False
        
        try:
            # Calculate TTL (Unix timestamp)
            ttl = int((datetime.now() + timedelta(hours=self.ttl_hours)).timestamp())
            
            # Store in DynamoDB
            self.table.put_item(
                Item={
                    'session_id': session_id,
                    'state': json.dumps(state),  # Serialize state
                    'timestamp': datetime.now().isoformat(),
                    'ttl': ttl
                }
            )
            
            logger.debug(f"Session stored: {session_id}")
            return True
            
        except ClientError as e:
            logger.error(f"DynamoDB error storing session: {e}")
            return False
        except Exception as e:
            logger.error(f"Error storing session: {e}")
            return False
    
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session state
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session state or None if not found
        """
        if not self._ready:
            logger.warning("DynamoDB not ready, cannot retrieve session")
            return None
        
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            
            if 'Item' in response:
                state_json = response['Item'].get('state')
                if state_json:
                    state = json.loads(state_json)
                    logger.debug(f"Session retrieved: {session_id}")
                    return state
            
            logger.debug(f"Session not found: {session_id}")
            return None
            
        except ClientError as e:
            logger.error(f"DynamoDB error retrieving session: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving session: {e}")
            return None
    
    async def update_session_state(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update specific fields in session state
        
        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update
            
        Returns:
            Success status
        """
        if not self._ready:
            return False
        
        try:
            # Get current state
            current_state = await self.get_session_state(session_id)
            
            if current_state is None:
                # Create new session
                return await self.store_session_state(session_id, updates)
            
            # Merge updates
            current_state.update(updates)
            
            # Store updated state
            return await self.store_session_state(session_id, current_state)
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Success status
        """
        if not self._ready:
            return False
        
        try:
            self.table.delete_item(Key={'session_id': session_id})
            logger.debug(f"Session deleted: {session_id}")
            return True
            
        except ClientError as e:
            logger.error(f"DynamoDB error deleting session: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    async def list_active_sessions(self, limit: int = 100) -> list:
        """
        List active sessions (for monitoring)
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session IDs
        """
        if not self._ready:
            return []
        
        try:
            response = self.table.scan(Limit=limit)
            
            sessions = []
            for item in response.get('Items', []):
                sessions.append({
                    'session_id': item['session_id'],
                    'timestamp': item.get('timestamp'),
                    'ttl': item.get('ttl')
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    @staticmethod
    def create_table(table_name: str = 'navis-sessions', region_name: str = 'us-east-1'):
        """
        Create DynamoDB table (run once during setup)
        
        Args:
            table_name: Name for the table
            region_name: AWS region
        """
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available")
            return False
        
        try:
            dynamodb = boto3.resource('dynamodb', region_name=region_name)
            
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'session_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'session_id',
                        'AttributeType': 'S'  # String
                    }
                ],
                BillingMode='PAY_PER_REQUEST',  # On-demand pricing
                Tags=[
                    {
                        'Key': 'Application',
                        'Value': 'Navis'
                    }
                ]
            )
            
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            
            # Enable TTL
            dynamodb_client = boto3.client('dynamodb', region_name=region_name)
            dynamodb_client.update_time_to_live(
                TableName=table_name,
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': 'ttl'
                }
            )
            
            logger.info(f"DynamoDB table created: {table_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"Table already exists: {table_name}")
                return True
            else:
                logger.error(f"Error creating table: {e}")
                return False
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            return False


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

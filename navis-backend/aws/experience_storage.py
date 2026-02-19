"""
S3 Experience Storage - Store RL training data
Provides durable storage for learning experiences
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed - S3 features will be disabled")


class ExperienceStorage:
    """Stores RL experiences in S3"""
    
    def __init__(
        self,
        bucket_name: str = 'navis-rl-experiences',
        region_name: str = 'us-east-1'
    ):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self._ready = False
        
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available - cannot initialize S3")
            return
        
        try:
            # Initialize S3 client
            self.s3 = boto3.client('s3', region_name=region_name)
            self._ready = True
            logger.info(f"S3 experience storage initialized: {bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3: {e}")
            self._ready = False
    
    def is_ready(self) -> bool:
        """Check if storage is ready"""
        return self._ready
    
    async def store_experience(
        self,
        user_id: str,
        experience: Dict[str, Any]
    ) -> bool:
        """
        Store a single experience
        
        Args:
            user_id: User identifier
            experience: Experience dictionary
            
        Returns:
            Success status
        """
        if not self._ready:
            logger.warning("S3 not ready, skipping experience storage")
            return False
        
        try:
            # Create key with timestamp for uniqueness
            timestamp = datetime.now().isoformat()
            key = f"experiences/{user_id}/{timestamp}.json"
            
            # Add metadata
            experience_with_meta = {
                **experience,
                'user_id': user_id,
                'stored_at': timestamp
            }
            
            # Store in S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(experience_with_meta, indent=2),
                ContentType='application/json',
                ServerSideEncryption='AES256',  # Encrypt at rest
                Metadata={
                    'user_id': user_id,
                    'timestamp': timestamp
                }
            )
            
            logger.debug(f"Experience stored: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 error storing experience: {e}")
            return False
        except Exception as e:
            logger.error(f"Error storing experience: {e}")
            return False
    
    async def store_batch_experiences(
        self,
        user_id: str,
        experiences: List[Dict[str, Any]]
    ) -> int:
        """
        Store multiple experiences
        
        Args:
            user_id: User identifier
            experiences: List of experience dictionaries
            
        Returns:
            Number of experiences successfully stored
        """
        if not self._ready:
            return 0
        
        success_count = 0
        for experience in experiences:
            if await self.store_experience(user_id, experience):
                success_count += 1
        
        logger.info(f"Stored {success_count}/{len(experiences)} experiences for user {user_id}")
        return success_count
    
    async def load_user_experiences(
        self,
        user_id: str,
        limit: int = 100,
        start_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load experiences for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of experiences to load
            start_date: Optional start date filter (ISO format)
            
        Returns:
            List of experiences
        """
        if not self._ready:
            return []
        
        try:
            prefix = f"experiences/{user_id}/"
            
            # List objects
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            experiences = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                
                # Filter by date if specified
                if start_date:
                    # Extract date from key
                    filename = key.split('/')[-1]
                    file_date = filename.split('.')[0]
                    if file_date < start_date:
                        continue
                
                # Load experience
                try:
                    obj_response = self.s3.get_object(
                        Bucket=self.bucket_name,
                        Key=key
                    )
                    experience = json.loads(obj_response['Body'].read())
                    experiences.append(experience)
                    
                except Exception as e:
                    logger.warning(f"Error loading experience {key}: {e}")
                    continue
            
            logger.info(f"Loaded {len(experiences)} experiences for user {user_id}")
            return experiences
            
        except ClientError as e:
            logger.error(f"S3 error loading experiences: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading experiences: {e}")
            return []
    
    async def get_experience_count(self, user_id: str) -> int:
        """
        Get count of experiences for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of experiences
        """
        if not self._ready:
            return 0
        
        try:
            prefix = f"experiences/{user_id}/"
            
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            return response.get('KeyCount', 0)
            
        except Exception as e:
            logger.error(f"Error counting experiences: {e}")
            return 0
    
    async def export_experiences_for_training(
        self,
        output_key: str = 'training/experiences.jsonl',
        user_ids: Optional[List[str]] = None,
        limit_per_user: int = 1000
    ) -> bool:
        """
        Export experiences in JSONL format for ML training
        
        Args:
            output_key: S3 key for output file
            user_ids: Optional list of user IDs to include
            limit_per_user: Max experiences per user
            
        Returns:
            Success status
        """
        if not self._ready:
            return False
        
        try:
            # Collect experiences
            all_experiences = []
            
            if user_ids:
                # Load for specific users
                for user_id in user_ids:
                    experiences = await self.load_user_experiences(
                        user_id=user_id,
                        limit=limit_per_user
                    )
                    all_experiences.extend(experiences)
            else:
                # Load all experiences (expensive!)
                logger.warning("Loading all experiences - this may be slow")
                # Implementation would scan all user prefixes
                pass
            
            # Convert to JSONL
            jsonl_content = '\n'.join(
                json.dumps(exp) for exp in all_experiences
            )
            
            # Store training file
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=output_key,
                Body=jsonl_content,
                ContentType='application/jsonl',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Exported {len(all_experiences)} experiences to {output_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting experiences: {e}")
            return False
    
    @staticmethod
    def create_bucket(bucket_name: str = 'navis-rl-experiences', region_name: str = 'us-east-1'):
        """
        Create S3 bucket (run once during setup)
        
        Args:
            bucket_name: Name for the bucket
            region_name: AWS region
        """
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available")
            return False
        
        try:
            s3 = boto3.client('s3', region_name=region_name)
            
            # Create bucket
            if region_name == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region_name}
                )
            
            # Enable versioning
            s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Enable encryption
            s3.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )
            
            # Add lifecycle policy (delete after 90 days)
            s3.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration={
                    'Rules': [
                        {
                            'Id': 'DeleteOldExperiences',
                            'Status': 'Enabled',
                            'Prefix': 'experiences/',
                            'Expiration': {'Days': 90}
                        }
                    ]
                }
            )
            
            logger.info(f"S3 bucket created: {bucket_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logger.info(f"Bucket already exists: {bucket_name}")
                return True
            else:
                logger.error(f"Error creating bucket: {e}")
                return False
        except Exception as e:
            logger.error(f"Error creating bucket: {e}")
            return False


# Global experience storage instance
_experience_storage = None


def get_experience_storage() -> ExperienceStorage:
    """Get or create global experience storage instance"""
    global _experience_storage
    if _experience_storage is None:
        _experience_storage = ExperienceStorage()
    return _experience_storage

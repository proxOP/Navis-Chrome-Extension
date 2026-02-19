#!/usr/bin/env python3
"""
AWS Setup Script for Navis
Creates DynamoDB table and S3 bucket for the application
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "navis-backend"))

from aws.session_manager import SessionManager
from aws.experience_storage import ExperienceStorage
from loguru import logger

def setup_aws_resources():
    """Create all required AWS resources"""
    
    logger.info("Starting AWS resource setup for Navis...")
    
    # Check AWS credentials
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        logger.error("AWS credentials not found in environment variables")
        logger.info("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return False
    
    # Setup DynamoDB table
    logger.info("Creating DynamoDB table for session management...")
    session_manager = SessionManager()
    
    try:
        if session_manager.create_table():
            logger.success("✓ DynamoDB table created successfully")
        else:
            logger.warning("DynamoDB table already exists or creation failed")
    except Exception as e:
        logger.error(f"Failed to create DynamoDB table: {e}")
        return False
    
    # Setup S3 bucket
    logger.info("Creating S3 bucket for experience storage...")
    experience_storage = ExperienceStorage()
    
    try:
        if experience_storage.create_bucket():
            logger.success("✓ S3 bucket created successfully")
        else:
            logger.warning("S3 bucket already exists or creation failed")
    except Exception as e:
        logger.error(f"Failed to create S3 bucket: {e}")
        return False
    
    logger.success("\n✓ AWS setup completed successfully!")
    logger.info("\nResources created:")
    logger.info(f"  - DynamoDB Table: {session_manager.table_name}")
    logger.info(f"  - S3 Bucket: {experience_storage.bucket_name}")
    logger.info(f"  - AWS Region: {session_manager.region}")
    
    return True

if __name__ == "__main__":
    success = setup_aws_resources()
    sys.exit(0 if success else 1)

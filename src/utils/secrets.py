import json
import boto3
from typing import Dict, Any, Optional
from functools import lru_cache

from .logger import setup_logger


logger = setup_logger(__name__)
secrets_client = boto3.client('secretsmanager')


class SecretsManager:
    """Secure secrets management using AWS Secrets Manager"""
    
    @staticmethod
    @lru_cache(maxsize=10)
    def get_secret(secret_name: str) -> Dict[str, Any]:
        """Get secret from AWS Secrets Manager with caching"""
        try:
            response = secrets_client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                # Binary secret (shouldn't happen for our use case)
                logger.error(f"Binary secret not supported: {secret_name}")
                raise ValueError("Binary secrets are not supported")
                
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {str(e)[:100]}")
            raise
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_all_secrets() -> Dict[str, Any]:
        """Get all application secrets from Secrets Manager"""
        try:
            secret_name = 'daily-report/credentials'
            secrets = SecretsManager.get_secret(secret_name)
            
            return {
                'slack_bot_token': secrets.get('slack_bot_token'),
                'slack_signing_secret': secrets.get('slack_signing_secret'),
                'slack_channel_id': secrets.get('slack_channel_id'),
                'github_token': secrets.get('github_token'),
                'github_username': secrets.get('github_username'),
                'google_calendar_credentials': secrets.get('google_calendar_credentials'),
                'google_calendar_id': secrets.get('google_calendar_id', 'primary'),
                'openai_api_key': secrets.get('openai_api_key'),
                'openai_model': secrets.get('openai_model', 'gpt-4-turbo-preview'),
                'timezone': secrets.get('timezone', 'Asia/Seoul')
            }
            
        except Exception as e:
            logger.error(f"Error loading application secrets: {str(e)[:100]}")
            raise


def get_secret_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Helper function to get a specific secret value"""
    try:
        secrets = SecretsManager.get_all_secrets()
        return secrets.get(key, default)
    except Exception:
        return default

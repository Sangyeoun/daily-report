import os
from typing import Optional

from .secrets import SecretsManager, get_secret_value


class Config:
    """Configuration management using AWS Secrets Manager"""
    
    _secrets_loaded = False
    _secrets_cache = {}
    
    # Non-sensitive configuration from environment variables
    DAILY_REPORT_GENERATOR_ARN: str = os.environ.get('DAILY_REPORT_GENERATOR_ARN', '')
    USE_SECRETS_MANAGER: str = os.environ.get('USE_SECRETS_MANAGER', 'true')
    ALLOWED_USERS: str = os.environ.get('ALLOWED_USERS', '')  # Comma-separated user IDs
    ALLOWED_CHANNELS: str = os.environ.get('ALLOWED_CHANNELS', '')  # Comma-separated channel IDs
    
    @classmethod
    def _load_secrets(cls):
        """Load secrets from Secrets Manager (lazy loading)"""
        if not cls._secrets_loaded:
            if cls.USE_SECRETS_MANAGER.lower() == 'true':
                cls._secrets_cache = SecretsManager.get_all_secrets()
            cls._secrets_loaded = True
    
    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value (from Secrets Manager or env var)"""
        cls._load_secrets()
        
        # Try Secrets Manager first
        if cls.USE_SECRETS_MANAGER.lower() == 'true':
            value = cls._secrets_cache.get(key)
            if value:
                return value
        
        # Fallback to environment variable (for local dev only)
        env_key = key.upper()
        return os.environ.get(env_key, default)
    
    @classmethod
    def SLACK_BOT_TOKEN(cls) -> str:
        return cls.get('slack_bot_token', '')
    
    @classmethod
    def SLACK_SIGNING_SECRET(cls) -> str:
        return cls.get('slack_signing_secret', '')
    
    @classmethod
    def SLACK_CHANNEL_ID(cls) -> str:
        return cls.get('slack_channel_id', '')
    
    @classmethod
    def GITHUB_TOKEN(cls) -> str:
        return cls.get('github_token', '')
    
    @classmethod
    def GITHUB_USERNAME(cls) -> str:
        return cls.get('github_username', '')
    
    @classmethod
    def GOOGLE_CALENDAR_CREDENTIALS(cls) -> str:
        return cls.get('google_calendar_credentials', '')
    
    @classmethod
    def GOOGLE_CALENDAR_ID(cls) -> str:
        return cls.get('google_calendar_id', 'primary')
    
    @classmethod
    def OPENAI_API_KEY(cls) -> str:
        return cls.get('openai_api_key', '')
    
    @classmethod
    def OPENAI_MODEL(cls) -> str:
        return cls.get('openai_model', 'gpt-4-turbo-preview')
    
    @classmethod
    def TIMEZONE(cls) -> str:
        return cls.get('timezone', 'Asia/Seoul')
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration"""
        cls._load_secrets()
        
        missing = []
        required_keys = [
            'slack_bot_token',
            'slack_signing_secret',
            'slack_channel_id',
            'github_token',
            'github_username',
            'openai_api_key'
        ]
        
        for key in required_keys:
            if not cls.get(key):
                missing.append(key)
        
        return missing
    
    @classmethod
    def get_allowed_users(cls) -> set[str]:
        """Get set of allowed user IDs"""
        if not cls.ALLOWED_USERS:
            return set()
        return set(u.strip() for u in cls.ALLOWED_USERS.split(',') if u.strip())
    
    @classmethod
    def get_allowed_channels(cls) -> set[str]:
        """Get set of allowed channel IDs"""
        if not cls.ALLOWED_CHANNELS:
            return set()
        return set(c.strip() for c in cls.ALLOWED_CHANNELS.split(',') if c.strip())

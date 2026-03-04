import re
from typing import Any, Dict, Union


class LogMasker:
    """Mask sensitive information in logs"""
    
    # Patterns for sensitive data
    PATTERNS = {
        'github_token': (r'ghp_[a-zA-Z0-9]{36,}', 'ghp_***'),
        'slack_bot_token': (r'xoxb-[a-zA-Z0-9\-]+', 'xoxb-***'),
        'slack_user_token': (r'xoxp-[a-zA-Z0-9\-]+', 'xoxp-***'),
        'openai_key': (r'sk-[a-zA-Z0-9]{32,}', 'sk-***'),
        'private_key': (r'-----BEGIN PRIVATE KEY-----[\s\S]*?-----END PRIVATE KEY-----', '-----BEGIN PRIVATE KEY-----\n[MASKED]\n-----END PRIVATE KEY-----'),
        'jwt': (r'eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+', 'jwt.***'),
        'email': (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***@***.***'),
        'url_with_token': (r'(https?://[^\s]+[?&]token=)[^\s&]+', r'\1***'),
        'authorization_header': (r'(Authorization["\']?\s*:\s*["\']?)(Bearer\s+)?[^\s"\']+', r'\1\2***'),
    }
    
    @staticmethod
    def mask_string(text: str) -> str:
        """Mask sensitive patterns in a string"""
        if not isinstance(text, str):
            return text
        
        masked = text
        for pattern_name, (pattern, replacement) in LogMasker.PATTERNS.items():
            masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
        
        return masked
    
    @staticmethod
    def mask_dict(data: Dict[str, Any], sensitive_keys: set = None) -> Dict[str, Any]:
        """Recursively mask sensitive data in dictionaries"""
        if sensitive_keys is None:
            sensitive_keys = {
                'token', 'secret', 'password', 'key', 'credential', 
                'authorization', 'auth', 'private_key', 'api_key',
                'signing_secret', 'client_secret', 'response_url'
            }
        
        masked = {}
        for key, value in data.items():
            # Check if key name suggests sensitive data
            key_lower = key.lower()
            is_sensitive = any(sensitive in key_lower for sensitive in sensitive_keys)
            
            if is_sensitive:
                masked[key] = '***'
            elif isinstance(value, dict):
                masked[key] = LogMasker.mask_dict(value, sensitive_keys)
            elif isinstance(value, list):
                masked[key] = [
                    LogMasker.mask_dict(item, sensitive_keys) if isinstance(item, dict)
                    else LogMasker.mask_string(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            elif isinstance(value, str):
                masked[key] = LogMasker.mask_string(value)
            else:
                masked[key] = value
        
        return masked
    
    @staticmethod
    def safe_log(data: Any) -> Union[str, Dict[str, Any]]:
        """Prepare data for safe logging"""
        if isinstance(data, str):
            return LogMasker.mask_string(data)
        elif isinstance(data, dict):
            return LogMasker.mask_dict(data)
        else:
            return data

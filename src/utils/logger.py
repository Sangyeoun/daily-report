import logging
import json
from typing import Any, Dict


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup structured logger for Lambda functions"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def log_json(logger: logging.Logger, level: int, message: str, **kwargs: Any) -> None:
    """Log structured JSON data with masking"""
    from .log_masker import LogMasker
    
    log_data = {
        'message': message,
        **kwargs
    }
    
    masked_data = LogMasker.safe_log(log_data)
    logger.log(level, json.dumps(masked_data))


def safe_log_error(logger: logging.Logger, message: str, error: Exception) -> None:
    """Safely log error without exposing sensitive data"""
    from .log_masker import LogMasker
    
    error_str = str(error)
    masked_error = LogMasker.mask_string(error_str)
    logger.error(f"{message}: {masked_error}")

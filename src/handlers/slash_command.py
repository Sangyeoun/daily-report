import json
import hmac
import hashlib
import time
from typing import Dict, Any, Tuple
from urllib.parse import parse_qs
import boto3

from ..utils import Config, setup_logger, safe_log_error


logger = setup_logger(__name__)
lambda_client = boto3.client('lambda')


class SlashCommandHandler:
    """Handle Slack slash command requests with security"""
    
    # Prevent replay attacks: reject requests older than 5 minutes
    MAX_REQUEST_AGE_SECONDS = 300
    
    def __init__(self):
        self.signing_secret = Config.SLACK_SIGNING_SECRET()
    
    def verify_slack_request(self, headers: Dict[str, str], body: str) -> Tuple[bool, str]:
        """
        Verify that request came from Slack
        Returns: (is_valid, error_message)
        """
        try:
            timestamp = headers.get('X-Slack-Request-Timestamp', '')
            signature = headers.get('X-Slack-Signature', '')
            
            if not timestamp or not signature:
                logger.warning("Missing Slack signature headers")
                return False, "Missing signature headers"
            
            # Prevent replay attacks: check timestamp
            try:
                request_time = int(timestamp)
                current_time = int(time.time())
                age = abs(current_time - request_time)
                
                if age > self.MAX_REQUEST_AGE_SECONDS:
                    logger.warning(f"Request timestamp too old: {age} seconds")
                    return False, "Request timestamp is too old (possible replay attack)"
            except ValueError:
                logger.warning("Invalid timestamp format")
                return False, "Invalid timestamp format"
            
            # Create signature base string
            sig_basestring = f"v0:{timestamp}:{body}"
            
            # Calculate expected signature
            my_signature = 'v0=' + hmac.new(
                self.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures using constant-time comparison
            if not hmac.compare_digest(my_signature, signature):
                logger.warning("Signature mismatch")
                return False, "Invalid signature"
            
            return True, ""
            
        except Exception as e:
            safe_log_error(logger, "Error verifying Slack request", e)
            return False, "Verification error"
    
    def parse_command(self, body: str) -> Dict[str, str]:
        """Parse Slack slash command body"""
        try:
            parsed = parse_qs(body)
            command_data = {
                'command': parsed.get('command', [''])[0],
                'text': parsed.get('text', [''])[0],
                'user_id': parsed.get('user_id', [''])[0],
                'user_name': parsed.get('user_name', [''])[0],
                'channel_id': parsed.get('channel_id', [''])[0],
                'response_url': parsed.get('response_url', [''])[0]
            }
            
            # Don't log sensitive response_url
            logger.info(f"Command parsed: user={command_data['user_id']}, channel={command_data['channel_id']}")
            return command_data
            
        except Exception as e:
            safe_log_error(logger, "Error parsing command", e)
            raise
    
    def check_authorization(self, user_id: str, channel_id: str) -> Tuple[bool, str]:
        """Check if user and channel are authorized"""
        allowed_users = Config.get_allowed_users()
        allowed_channels = Config.get_allowed_channels()
        
        # If whitelist is empty, allow all
        if allowed_users and user_id not in allowed_users:
            logger.warning(f"Unauthorized user: {user_id}")
            return False, "You are not authorized to use this command"
        
        if allowed_channels and channel_id not in allowed_channels:
            logger.warning(f"Unauthorized channel: {channel_id}")
            return False, "This command cannot be used in this channel"
        
        return True, ""
    
    def invoke_report_generator(self, user_id: str, channel_id: str) -> None:
        """Invoke daily report generator Lambda asynchronously"""
        try:
            payload = {
                'user_id': user_id,
                'channel_id': channel_id
            }
            
            # Invoke asynchronously
            lambda_client.invoke(
                FunctionName=Config.DAILY_REPORT_GENERATOR_ARN,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            
            logger.info(f"Invoked report generator for user {user_id}")
            
        except Exception as e:
            safe_log_error(logger, "Error invoking report generator", e)
            raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Slack slash command with security"""
    try:
        handler = SlashCommandHandler()
        
        # Extract request data
        headers = event.get('headers', {})
        body = event.get('body', '')
        
        # Verify request from Slack (signature + timestamp)
        is_valid, error_msg = handler.verify_slack_request(headers, body)
        if not is_valid:
            logger.warning(f"Slack verification failed: {error_msg}")
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # Parse command
        command_data = handler.parse_command(body)
        
        # Check authorization (user and channel whitelist)
        is_authorized, auth_error = handler.check_authorization(
            command_data['user_id'],
            command_data['channel_id']
        )
        if not is_authorized:
            logger.warning(f"Authorization failed: user={command_data['user_id']}")
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'ephemeral',
                    'text': f'🔒 {auth_error}'
                })
            }
        
        # Invoke report generator asynchronously
        handler.invoke_report_generator(
            command_data['user_id'],
            Config.SLACK_CHANNEL_ID()
        )
        
        # Return immediate response to Slack
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': '⏳ Generating daily report... Please wait.'
            })
        }
        
    except Exception as e:
        safe_log_error(logger, "Slash command handler error", e)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': '❌ An error occurred. Please contact admin.'
            })
        }

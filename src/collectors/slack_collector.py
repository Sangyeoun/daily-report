from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ..utils import Config, setup_logger, safe_log_error, LogMasker


logger = setup_logger(__name__)


class SlackCollector:
    """Collect and analyze Slack activity (excluding DMs)"""
    
    def __init__(self, token: str, user_id: str = None):
        self.client = WebClient(token=token)
        self.user_id = user_id or self._get_bot_user_id()
    
    def _get_bot_user_id(self) -> str:
        """Get authenticated user's ID"""
        try:
            response = self.client.auth_test()
            return response['user_id']
        except SlackApiError as e:
            safe_log_error(logger, "Error getting user ID", e)
            raise
    
    def get_todays_activity(self, timezone: str = 'Asia/Seoul') -> Dict[str, Any]:
        """Get today's Slack activity (excluding DMs)"""
        try:
            tz = pytz.timezone(timezone)
            today = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
            oldest_ts = str(int(today.timestamp()))
            latest_ts = str(int((today + timedelta(days=1)).timestamp()))
            
            # Get user's conversations (channels)
            channels = self._get_public_channels()
            
            messages_sent = 0
            threads_participated = set()
            channels_active = []
            message_details = []
            
            for channel in channels:
                channel_id = channel['id']
                channel_name = channel['name']
                
                # Get user's messages in this channel
                try:
                    response = self.client.conversations_history(
                        channel=channel_id,
                        oldest=oldest_ts,
                        latest=latest_ts
                    )
                    
                    user_messages = [
                        msg for msg in response.get('messages', [])
                        if msg.get('user') == self.user_id
                    ]
                    
                    if user_messages:
                        messages_sent += len(user_messages)
                        channels_active.append({
                            'name': channel_name,
                            'id': channel_id,
                            'message_count': len(user_messages)
                        })
                        
                        for msg in user_messages:
                            # Mask message text to prevent sensitive data in logs
                            text = msg.get('text', '')[:100]
                            masked_text = LogMasker.mask_string(text)
                            
                            message_details.append({
                                'channel': channel_name,
                                'text': masked_text,
                                'timestamp': msg.get('ts'),
                                'thread_ts': msg.get('thread_ts')
                            })
                            
                            if msg.get('thread_ts'):
                                threads_participated.add(msg['thread_ts'])
                
                except SlackApiError as e:
                    logger.warning(f"Could not fetch messages from {channel_name}: {e}")
                    continue
            
            activity = {
                'messages_sent': messages_sent,
                'threads_participated': len(threads_participated),
                'channels_active': channels_active,
                'message_details': message_details
            }
            
            logger.info(f"Collected Slack activity: {messages_sent} messages in {len(channels_active)} channels")
            return activity
            
        except SlackApiError as e:
            safe_log_error(logger, "Slack API error", e)
            raise
        except Exception as e:
            safe_log_error(logger, "Error collecting Slack activity", e)
            raise
    
    def _get_public_channels(self) -> List[Dict[str, str]]:
        """Get list of public channels the user is a member of"""
        try:
            channels = []
            cursor = None
            
            while True:
                response = self.client.conversations_list(
                    types='public_channel',
                    exclude_archived=True,
                    limit=200,
                    cursor=cursor
                )
                
                for channel in response['channels']:
                    if channel.get('is_member'):
                        channels.append({
                            'id': channel['id'],
                            'name': channel['name']
                        })
                
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break
            
            return channels
            
        except SlackApiError as e:
            safe_log_error(logger, "Error fetching channels", e)
            raise
    
    def format_activity_summary(self, activity: Dict[str, Any]) -> str:
        """Format activity as markdown for Slack"""
        if activity['messages_sent'] == 0:
            return "_No Slack activity today_"
        
        summary = [
            f"*Messages sent:* {activity['messages_sent']}",
            f"*Threads participated:* {activity['threads_participated']}",
            f"*Active channels:* {len(activity['channels_active'])}"
        ]
        
        if activity['channels_active']:
            summary.append("\n*Channel breakdown:*")
            for channel in activity['channels_active']:
                summary.append(f"  • #{channel['name']}: {channel['message_count']} messages")
        
        return "\n".join(summary)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Slack activity collection"""
    try:
        target_user_id = event.get('user_id')
        
        collector = SlackCollector(Config.SLACK_BOT_TOKEN(), target_user_id)
        activity = collector.get_todays_activity(Config.TIMEZONE())
        
        return {
            'statusCode': 200,
            'body': {
                'activity': activity,
                'summary': collector.format_activity_summary(activity)
            }
        }
    except Exception as e:
        safe_log_error(logger, "Lambda handler error", e)
        return {
            'statusCode': 500,
            'body': {
                'error': 'Internal server error'
            }
        }

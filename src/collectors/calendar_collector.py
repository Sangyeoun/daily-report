from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import pytz

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils import Config, setup_logger, safe_log_error, LogMasker


logger = setup_logger(__name__)


class CalendarCollector:
    """Collect Google Calendar events for today"""
    
    def __init__(self, credentials_json: str, calendar_id: str = 'primary'):
        self.calendar_id = calendar_id
        self.service = self._build_service(credentials_json)
    
    def _build_service(self, credentials_json: str):
        """Build Google Calendar service"""
        try:
            creds_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/calendar.readonly']
            )
            return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            safe_log_error(logger, "Error building Google Calendar service", e)
            raise
    
    def get_todays_events(self, timezone: str = 'Asia/Seoul') -> List[Dict[str, Any]]:
        """Get today's calendar events"""
        try:
            tz = pytz.timezone(timezone)
            today = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # Convert to RFC3339 format
            time_min = today.isoformat()
            time_max = tomorrow.isoformat()
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Mask attendee emails for privacy
                attendees = event.get('attendees', [])
                attendee_count = len(attendees)
                
                event_data = {
                    'summary': event.get('summary', 'No Title'),
                    'start': start,
                    'end': end,
                    'description': event.get('description', '')[:100],  # Truncate descriptions
                    'location': event.get('location', ''),
                    'attendee_count': attendee_count,  # Don't expose emails
                    'html_link': event.get('htmlLink', '')
                }
                formatted_events.append(event_data)
            
            logger.info(f"Found {len(formatted_events)} events for today")
            return formatted_events
            
        except HttpError as e:
            safe_log_error(logger, "Google Calendar API error", e)
            raise
        except Exception as e:
            safe_log_error(logger, "Error collecting calendar events", e)
            raise
    
    def format_events_summary(self, events: List[Dict[str, Any]]) -> str:
        """Format events as markdown for Slack"""
        if not events:
            return "_No events scheduled for today_"
        
        summary = []
        for event in events:
            start = event['start']
            # Parse datetime or date
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                time_str = start_dt.strftime('%H:%M')
            else:
                time_str = 'All day'
            
            summary.append(f"• *{time_str}* - {event['summary']}")
            if event.get('location'):
                summary.append(f"  _Location:_ {event['location']}")
        
        return "\n".join(summary)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Google Calendar event collection"""
    try:
        collector = CalendarCollector(
            Config.GOOGLE_CALENDAR_CREDENTIALS(),
            Config.GOOGLE_CALENDAR_ID()
        )
        events = collector.get_todays_events(Config.TIMEZONE())
        
        return {
            'statusCode': 200,
            'body': {
                'events': events,
                'summary': collector.format_events_summary(events)
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

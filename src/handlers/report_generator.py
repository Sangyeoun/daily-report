import json
from datetime import datetime
from typing import Dict, Any, List
import pytz

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ..collectors import GitHubCollector, CalendarCollector, SlackCollector
from ..utils import Config, setup_logger, safe_log_error
from ..utils.ai_summarizer import AISummarizer


logger = setup_logger(__name__)


class DailyReportGenerator:
    """Generate and post daily report to Slack"""
    
    def __init__(self):
        self.slack_client = WebClient(token=Config.SLACK_BOT_TOKEN())
        self.github_collector = GitHubCollector(Config.GITHUB_TOKEN(), Config.GITHUB_USERNAME())
        self.calendar_collector = CalendarCollector(
            Config.GOOGLE_CALENDAR_CREDENTIALS(),
            Config.GOOGLE_CALENDAR_ID()
        )
        self.slack_collector = SlackCollector(Config.SLACK_BOT_TOKEN())
        self.ai_summarizer = AISummarizer(Config.OPENAI_API_KEY(), Config.OPENAI_MODEL())
    
    def generate_report(self, user_id: str = None) -> Dict[str, Any]:
        """Generate complete daily report"""
        try:
            logger.info("Starting daily report generation")
            
            # Collect data from all sources
            github_prs = self.github_collector.get_todays_prs(Config.TIMEZONE())
            calendar_events = self.calendar_collector.get_todays_events(Config.TIMEZONE())
            
            # For Slack activity, we need to get the actual user's ID, not the bot's
            if user_id:
                slack_collector_user = SlackCollector(Config.SLACK_BOT_TOKEN(), user_id)
                slack_activity = slack_collector_user.get_todays_activity(Config.TIMEZONE())
            else:
                slack_activity = self.slack_collector.get_todays_activity(Config.TIMEZONE())
            
            # Generate AI summary
            ai_summary = self.ai_summarizer.summarize_daily_activity(
                github_prs,
                calendar_events,
                slack_activity
            )
            
            # Format report
            report = self._format_report(
                github_prs,
                calendar_events,
                slack_activity,
                ai_summary
            )
            
            logger.info("Daily report generated successfully")
            return {
                'report': report,
                'data': {
                    'github_prs': github_prs,
                    'calendar_events': calendar_events,
                    'slack_activity': slack_activity
                }
            }
            
        except Exception as e:
            safe_log_error(logger, "Error generating report", e)
            raise
    
    def _format_report(
        self,
        github_prs: List[Dict[str, Any]],
        calendar_events: List[Dict[str, Any]],
        slack_activity: Dict[str, Any],
        ai_summary: str
    ) -> List[Dict[str, Any]]:
        """Format report as Slack blocks"""
        tz = pytz.timezone(Config.TIMEZONE())
        today = datetime.now(tz).strftime('%Y-%m-%d (%A)')
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Daily Report - {today}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🤖 AI Summary*\n{ai_summary}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📝 GitHub Pull Requests*\n{self.github_collector.format_pr_summary(github_prs)}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📅 Calendar Events*\n{self.calendar_collector.format_events_summary(calendar_events)}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💬 Slack Activity*\n{self.slack_collector.format_activity_summary(slack_activity)}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Generated at {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')}_"
                    }
                ]
            }
        ]
        
        return blocks
    
    def post_to_slack(self, blocks: List[Dict[str, Any]], channel_id: str = None) -> Dict[str, Any]:
        """Post report to Slack channel"""
        try:
            target_channel = channel_id or Config.SLACK_CHANNEL_ID()
            
            response = self.slack_client.chat_postMessage(
                channel=target_channel,
                blocks=blocks,
                text="Daily Report"
            )
            
            logger.info(f"Report posted to Slack channel")
            return {
                'success': True,
                'channel': target_channel,
                'timestamp': response['ts']
            }
            
        except SlackApiError as e:
            safe_log_error(logger, "Error posting to Slack", e)
            raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for daily report generation and posting"""
    try:
        # Validate configuration
        missing_vars = Config.validate()
        if missing_vars:
            logger.error(f"Missing required configuration: {missing_vars}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Missing required configuration',
                    'missing_vars': missing_vars
                })
            }
        
        # Get user_id from event if provided (for user-specific reports)
        user_id = event.get('user_id')
        channel_id = event.get('channel_id')
        
        # Generate report
        generator = DailyReportGenerator()
        result = generator.generate_report(user_id)
        
        # Post to Slack
        post_result = generator.post_to_slack(result['report'], channel_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Daily report posted successfully',
                'post_result': post_result
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

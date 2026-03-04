from typing import Dict, Any, List
from openai import OpenAI

from .logger import setup_logger, safe_log_error


logger = setup_logger(__name__)


class AISummarizer:
    """AI-powered summarization using OpenAI"""
    
    def __init__(self, api_key: str, model: str = 'gpt-4-turbo-preview'):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def summarize_daily_activity(
        self,
        github_prs: List[Dict[str, Any]],
        calendar_events: List[Dict[str, Any]],
        slack_activity: Dict[str, Any]
    ) -> str:
        """Generate AI summary of daily activity"""
        try:
            # Prepare context for AI
            context = self._prepare_context(github_prs, calendar_events, slack_activity)
            
            prompt = f"""You are an AI assistant that summarizes daily work activities.
Based on the following data, create a concise and insightful summary of today's work.

{context}

Please provide:
1. Key highlights and accomplishments
2. Areas of focus
3. Collaboration patterns
4. Suggestions for tomorrow (if any)

Keep the summary professional and concise (3-5 paragraphs)."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes daily work activities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            logger.info("AI summary generated successfully")
            return summary
            
        except Exception as e:
            safe_log_error(logger, "Error generating AI summary", e)
            return "_Error occurred while generating AI summary._"
    
    def _prepare_context(
        self,
        github_prs: List[Dict[str, Any]],
        calendar_events: List[Dict[str, Any]],
        slack_activity: Dict[str, Any]
    ) -> str:
        """Prepare context string for AI"""
        context_parts = []
        
        # GitHub PRs
        context_parts.append("### GitHub Pull Requests")
        if github_prs:
            for pr in github_prs:
                context_parts.append(f"- {pr['title']} ({pr['state']}) in {pr['repository']}")
        else:
            context_parts.append("- No PRs created or updated today")
        
        # Calendar Events
        context_parts.append("\n### Calendar Events")
        if calendar_events:
            for event in calendar_events:
                context_parts.append(f"- {event['summary']} at {event['start']}")
        else:
            context_parts.append("- No events scheduled")
        
        # Slack Activity
        context_parts.append("\n### Slack Activity")
        context_parts.append(f"- Messages sent: {slack_activity.get('messages_sent', 0)}")
        context_parts.append(f"- Threads participated: {slack_activity.get('threads_participated', 0)}")
        if slack_activity.get('channels_active'):
            context_parts.append("- Active channels:")
            for channel in slack_activity['channels_active']:
                context_parts.append(f"  - #{channel['name']}: {channel['message_count']} messages")
        
        return "\n".join(context_parts)

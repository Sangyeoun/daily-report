from datetime import datetime, timedelta
from typing import List, Dict, Any
from github import Github, GithubException
import pytz

from ..utils import Config, setup_logger, safe_log_error, LogMasker


logger = setup_logger(__name__)


class GitHubCollector:
    """Collect GitHub Pull Requests authored by the user"""
    
    def __init__(self, token: str, username: str):
        self.client = Github(token)
        self.username = username
    
    def get_todays_prs(self, timezone: str = 'Asia/Seoul') -> List[Dict[str, Any]]:
        """Get PRs created or updated today by the authenticated user"""
        try:
            tz = pytz.timezone(timezone)
            today = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
            
            user = self.client.get_user()
            prs = []
            
            # Search for PRs authored by the user
            query = f"author:{self.username} is:pr created:>={today.strftime('%Y-%m-%d')}"
            search_results = self.client.search_issues(query)
            
            for issue in search_results:
                pr_data = {
                    'title': issue.title,
                    'url': issue.html_url,
                    'state': issue.state,
                    'repository': issue.repository.full_name,
                    'created_at': issue.created_at.isoformat(),
                    'updated_at': issue.updated_at.isoformat() if issue.updated_at else None,
                    'labels': [label.name for label in issue.labels],
                    'draft': getattr(issue, 'draft', False)
                }
                prs.append(pr_data)
            
            # Also check for PRs updated today
            query_updated = f"author:{self.username} is:pr updated:>={today.strftime('%Y-%m-%d')}"
            search_updated = self.client.search_issues(query_updated)
            
            existing_urls = {pr['url'] for pr in prs}
            for issue in search_updated:
                if issue.html_url not in existing_urls:
                    pr_data = {
                        'title': issue.title,
                        'url': issue.html_url,
                        'state': issue.state,
                        'repository': issue.repository.full_name,
                        'created_at': issue.created_at.isoformat(),
                        'updated_at': issue.updated_at.isoformat() if issue.updated_at else None,
                        'labels': [label.name for label in issue.labels],
                        'draft': getattr(issue, 'draft', False)
                    }
                    prs.append(pr_data)
            
            logger.info(f"Found {len(prs)} PRs for today")
            return prs
            
        except GithubException as e:
            safe_log_error(logger, "GitHub API error", e)
            raise
        except Exception as e:
            safe_log_error(logger, "Error collecting GitHub PRs", e)
            raise
    
    def format_pr_summary(self, prs: List[Dict[str, Any]]) -> str:
        """Format PR list as markdown for Slack"""
        if not prs:
            return "_No PRs created or updated today_"
        
        summary = []
        for pr in prs:
            status_emoji = "✅" if pr['state'] == 'closed' else "🔄" if pr['state'] == 'open' else "❌"
            draft_label = " [Draft]" if pr.get('draft') else ""
            summary.append(f"{status_emoji} <{pr['url']}|{pr['title']}>{draft_label}")
            summary.append(f"  _Repository:_ {pr['repository']}")
        
        return "\n".join(summary)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for GitHub PR collection"""
    try:
        collector = GitHubCollector(Config.GITHUB_TOKEN(), Config.GITHUB_USERNAME())
        prs = collector.get_todays_prs(Config.TIMEZONE())
        
        return {
            'statusCode': 200,
            'body': {
                'prs': prs,
                'summary': collector.format_pr_summary(prs)
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

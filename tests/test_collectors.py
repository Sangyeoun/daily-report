import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.collectors import GitHubCollector, CalendarCollector, SlackCollector


class TestGitHubCollector:
    """Test GitHub PR collector"""
    
    @patch('src.collectors.github_collector.Github')
    def test_get_todays_prs(self, mock_github):
        """Test fetching today's PRs"""
        # Setup mock
        mock_client = Mock()
        mock_github.return_value = mock_client
        
        mock_issue = Mock()
        mock_issue.title = "Test PR"
        mock_issue.html_url = "https://github.com/user/repo/pull/1"
        mock_issue.state = "open"
        mock_issue.repository.full_name = "user/repo"
        mock_issue.created_at = datetime.now()
        mock_issue.updated_at = datetime.now()
        mock_issue.labels = []
        mock_issue.draft = False
        
        mock_search = Mock()
        mock_search.__iter__ = Mock(return_value=iter([mock_issue]))
        mock_client.search_issues.return_value = mock_search
        
        # Test
        collector = GitHubCollector("token", "username")
        prs = collector.get_todays_prs()
        
        assert len(prs) > 0
        assert prs[0]['title'] == "Test PR"
    
    def test_format_pr_summary_empty(self):
        """Test formatting empty PR list"""
        collector = GitHubCollector("token", "username")
        summary = collector.format_pr_summary([])
        assert "_No PRs created or updated today_" in summary
    
    def test_format_pr_summary_with_prs(self):
        """Test formatting PR list"""
        collector = GitHubCollector("token", "username")
        prs = [{
            'title': 'Test PR',
            'url': 'https://github.com/user/repo/pull/1',
            'state': 'open',
            'repository': 'user/repo',
            'draft': False
        }]
        summary = collector.format_pr_summary(prs)
        assert 'Test PR' in summary
        assert 'user/repo' in summary


class TestCalendarCollector:
    """Test Calendar collector"""
    
    @patch('src.collectors.calendar_collector.build')
    @patch('src.collectors.calendar_collector.service_account')
    def test_get_todays_events(self, mock_service_account, mock_build):
        """Test fetching today's events"""
        # Setup mock
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        mock_events = {
            'items': [{
                'summary': 'Test Meeting',
                'start': {'dateTime': '2026-03-04T10:00:00+09:00'},
                'end': {'dateTime': '2026-03-04T11:00:00+09:00'},
                'description': 'Test description',
                'location': 'Test location',
                'attendees': []
            }]
        }
        
        mock_service.events().list().execute.return_value = mock_events
        
        # Test
        collector = CalendarCollector('{}', 'primary')
        events = collector.get_todays_events()
        
        assert len(events) > 0
        assert events[0]['summary'] == 'Test Meeting'


class TestSlackCollector:
    """Test Slack collector"""
    
    @patch('src.collectors.slack_collector.WebClient')
    def test_get_todays_activity(self, mock_web_client):
        """Test collecting Slack activity"""
        # Setup mock
        mock_client = Mock()
        mock_web_client.return_value = mock_client
        
        mock_client.auth_test.return_value = {'user_id': 'U123'}
        mock_client.conversations_list.return_value = {
            'channels': [{'id': 'C123', 'name': 'general', 'is_member': True}],
            'response_metadata': {}
        }
        mock_client.conversations_history.return_value = {
            'messages': [{
                'user': 'U123',
                'text': 'Test message',
                'ts': '1234567890.123456'
            }]
        }
        
        # Test
        collector = SlackCollector('token', 'U123')
        activity = collector.get_todays_activity()
        
        assert activity['messages_sent'] > 0
        assert len(activity['channels_active']) > 0

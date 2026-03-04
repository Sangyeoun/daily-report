import pytest
import json
from unittest.mock import Mock, patch

from src.handlers import slash_command, scheduled_report


class TestSlashCommandHandler:
    """Test slash command handler"""
    
    @patch('src.handlers.slash_command.lambda_client')
    @patch('src.handlers.slash_command.Config')
    def test_valid_slash_command(self, mock_config, mock_lambda_client):
        """Test valid slash command processing"""
        mock_config.SLACK_SIGNING_SECRET = 'secret'
        mock_config.SLACK_CHANNEL_ID = 'C123'
        mock_config.DAILY_REPORT_GENERATOR_ARN = 'arn:aws:lambda:region:account:function:name'
        
        # Mock event (simplified)
        event = {
            'headers': {
                'X-Slack-Request-Timestamp': '1234567890',
                'X-Slack-Signature': 'v0=test_signature'
            },
            'body': 'command=/daily-report&user_id=U123&user_name=testuser&channel_id=C456&response_url=https://hooks.slack.com/test'
        }
        
        # Note: This test will fail signature verification in real scenario
        # For actual testing, you'd need to calculate correct signature
        
        with patch.object(slash_command.SlashCommandHandler, 'verify_slack_request', return_value=True):
            response = slash_command.lambda_handler(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'Daily report' in body['text']


class TestScheduledReportHandler:
    """Test scheduled report handler"""
    
    @patch('src.handlers.scheduled_report.DailyReportGenerator')
    @patch('src.handlers.scheduled_report.Config')
    def test_scheduled_report(self, mock_config, mock_generator_class):
        """Test scheduled report execution"""
        mock_config.validate.return_value = []
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_report.return_value = {
            'report': [],
            'data': {}
        }
        mock_generator.post_to_slack.return_value = {
            'success': True
        }
        
        # Test
        event = {}
        response = scheduled_report.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        mock_generator.generate_report.assert_called_once()
        mock_generator.post_to_slack.assert_called_once()

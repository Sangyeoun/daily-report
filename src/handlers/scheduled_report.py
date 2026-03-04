import json
from typing import Dict, Any

from .report_generator import DailyReportGenerator
from ..utils import Config, setup_logger, safe_log_error


logger = setup_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for scheduled daily report (EventBridge trigger)"""
    try:
        logger.info("Scheduled daily report triggered")
        
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
        
        # Generate and post report
        # For scheduled reports, use the configured GitHub username's activity
        generator = DailyReportGenerator()
        result = generator.generate_report()
        
        # Post to the configured Slack channel
        post_result = generator.post_to_slack(result['report'])
        
        logger.info("Scheduled daily report completed successfully")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Daily report posted successfully',
                'post_result': post_result
            })
        }
        
    except Exception as e:
        safe_log_error(logger, "Scheduled report handler error", e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }

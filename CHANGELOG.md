# Changelog

## [1.0.0] - 2026-03-04

### Added
- Initial release with daily report automation
- GitHub PR collection
- Google Calendar integration
- Slack activity analysis
- AI-powered summary (OpenAI)
- AWS Secrets Manager integration
- Automatic log masking
- Slack signature verification with timestamp
- Rate limiting (API Gateway)
- CloudWatch Alarms

### Security
- All secrets in AWS Secrets Manager
- Auto-masking of tokens/emails in logs
- Replay attack prevention (±5min timestamp)
- IAM least privilege policies
- Git hooks to prevent token commits
- KMS-encrypted CloudWatch Logs

### Changed
- Runtime: Python 3.13
- Region: ap-northeast-2 (Seoul) → ap-northeast-1 (Tokyo)
- Timezone: Asia/Seoul (KST) → Asia/Tokyo (JST)
- Structure: Simplified (docs/, deployment/ separation)
- Documentation: English only, reduced from 12 to 3 core docs
- Root directory: Clean (only 7 essential files)

### Removed
- Verbose documentation (consolidated)
- Korean language docs (switched to English)

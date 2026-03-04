# Setup Guide

## Prerequisites

- AWS CLI & SAM CLI  
- Python 3.13+
- Region: ap-northeast-1 (Tokyo)
- Timezone: Asia/Tokyo (JST)
- Slack workspace admin access
- GitHub account
- Google Cloud project
- OpenAI API key

## Quick Setup

### 1. Get API Credentials

**Slack**:
- Bot Token (`xoxb-...`)
- Signing Secret
- Channel ID

**GitHub**:
- Personal Access Token (Fine-grained recommended)
- Scopes: Pull requests (read)

**Google Calendar**:
- Service Account JSON
- Share calendar with service account email

**OpenAI**:
- API Key (`sk-...`)

### 2. Create Secrets File

```bash
cd deployment
cp secrets.json.example secrets.json
# Edit with actual credentials
```

### 3. Configure Deployment

```bash
cp samconfig.toml.example samconfig.toml
# Update s3_bucket name
```

### 4. Deploy

```bash
# Create S3 bucket
aws s3 mb s3://daily-report-$(date +%s) --region ap-northeast-1

# Deploy
cd ..
make deploy

# Update secrets
make update-secrets
rm deployment/secrets.json
```

### 5. Configure Slack App

Set Request URL to the deployed API Gateway endpoint:
```
https://{api-id}.execute-api.{region}.amazonaws.com/prod/slack/command
```

## Configuration

### Schedule
- Default: 17:30 JST (08:30 UTC)
- Modify: `deployment/samconfig.toml` → `ScheduleExpression`

### Access Control (Optional)
```toml
AllowedUsers=U01234567,U89ABCDEF
AllowedChannels=C0123456789
```

## Testing

```bash
# Slack
/daily-report

# Manual invoke
aws lambda invoke --function-name daily-report-generator --payload '{}' out.json

# View logs
make logs
```

## Troubleshooting

**"Missing configuration"**:
```bash
aws secretsmanager get-secret-value --secret-id daily-report/credentials
```

**Invalid signature**: Check Slack signing secret

**API errors**: Verify token permissions

## Updates

```bash
# Code update
git pull
make deploy

# Secrets rotation
cd deployment
# Edit secrets.json with new tokens
./scripts/update-secrets.sh
rm secrets.json
```

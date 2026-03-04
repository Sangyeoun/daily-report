#!/bin/bash

# Update Secrets Manager with actual credentials

set -e

# Get to deployment directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🔐 Updating AWS Secrets Manager..."

# Check if secrets.json exists
if [ ! -f "secrets.json" ]; then
    echo "❌ Error: secrets.json not found"
    echo ""
    echo "Please create secrets.json with the following format:"
    echo ""
    cat << 'EOF'
{
  "slack_bot_token": "xoxb-YOUR-TOKEN",
  "slack_signing_secret": "YOUR-SIGNING-SECRET",
  "slack_channel_id": "C0123456789",
  "github_token": "ghp_YOUR-TOKEN",
  "github_username": "your-username",
  "google_calendar_credentials": "{...your json...}",
  "google_calendar_id": "primary",
  "openai_api_key": "sk-YOUR-KEY",
  "openai_model": "gpt-4-turbo-preview",
  "timezone": "Asia/Seoul"
}
EOF
    echo ""
    exit 1
fi

# Validate JSON format
echo "Validating JSON format..."
if ! jq empty secrets.json 2>/dev/null; then
    echo "❌ Error: secrets.json is not valid JSON"
    exit 1
fi

# Get secret ARN from CloudFormation outputs
SECRET_ARN=$(aws cloudformation describe-stacks \
    --stack-name daily-report-stack \
    --query 'Stacks[0].Outputs[?OutputKey==`SecretsManagerArn`].OutputValue' \
    --output text)

if [ -z "$SECRET_ARN" ]; then
    echo "❌ Error: Could not find Secrets Manager ARN"
    echo "Make sure the stack is deployed first (sam deploy)"
    exit 1
fi

echo "Secret ARN: $SECRET_ARN"

# Update secret value
echo "Updating secret value..."
aws secretsmanager put-secret-value \
    --secret-id "$SECRET_ARN" \
    --secret-string file://secrets.json

echo ""
echo "✅ Secrets updated successfully!"
echo ""
echo "⚠️  IMPORTANT: Delete secrets.json now for security:"
echo "  rm secrets.json"
echo ""
echo "🔄 Lambda functions will automatically use the new secrets on next invocation"
echo ""

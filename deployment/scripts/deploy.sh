#!/bin/bash

# Daily Report Deployment Script

set -e

# Get to deployment directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🚀 Starting deployment..."

# Check if samconfig.toml exists
if [ ! -f "samconfig.toml" ]; then
    echo "❌ Error: samconfig.toml not found"
    echo "Please copy samconfig.toml.example and configure it first:"
    echo "  cd deployment"
    echo "  cp samconfig.toml.example samconfig.toml"
    exit 1
fi

# Build the application
echo "📦 Building SAM application..."
sam build --template-file template.yaml

# Deploy
echo "🌐 Deploying to AWS..."
sam deploy --config-file samconfig.toml

# Get outputs
echo ""
echo "✅ Deployment complete! (Region: ap-northeast-1 Tokyo)"
echo ""
echo "📋 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name daily-report-stack \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "🔗 Next Steps:"
echo "1. Update secrets: ./scripts/update-secrets.sh"
echo "2. Configure Slack app with SlashCommandApiUrl"
echo "3. Test: /daily-report in Slack"
echo ""

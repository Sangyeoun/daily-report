#!/bin/bash

# Local Testing Script

set -e

# Get to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
cd "$SCRIPT_DIR/.."

echo "🧪 Testing Daily Report locally..."

# Check if .env exists in project root
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Create .env from .env.example for local testing"
    echo "  cp .env.example .env"
    exit 1
fi

# Export environment variables
export $(cat "$PROJECT_ROOT/.env" | xargs)

# Build
echo "📦 Building..."
sam build --template-file template.yaml

# Test report generator
echo ""
echo "📊 Testing Report Generator..."
sam local invoke ReportGeneratorFunction \
    --event events/test-event.json \
    --env-vars "$PROJECT_ROOT/.env"

echo ""
echo "✅ Local test complete!"

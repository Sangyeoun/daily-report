#!/bin/bash

# Setup Git hooks for security

set -e

# Get to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "🔧 Setting up Git security hooks..."

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Prevent committing sensitive files
SENSITIVE_FILES=".env .env.local deployment/secrets.json deployment/samconfig.toml credentials.json google-credentials.json"

for file in $SENSITIVE_FILES; do
    if git diff --cached --name-only | grep -q "^${file}$"; then
        echo "❌ ERROR: Attempting to commit sensitive file: $file"
        echo "This file should never be committed to Git!"
        exit 1
    fi
done

# Check for token patterns in staged changes
if git diff --cached | grep -E '(xoxb-[a-zA-Z0-9\-]{50,}|ghp_[a-zA-Z0-9]{36,}|sk-proj-[a-zA-Z0-9]{100,}|-----BEGIN PRIVATE KEY-----)'; then
    echo "❌ ERROR: Potential token/secret found in staged changes!"
    echo ""
    echo "Please review your changes and remove any secrets."
    echo "Use environment variables or AWS Secrets Manager instead."
    exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
EOF

chmod +x .git/hooks/pre-commit

echo "✅ Git hooks installed successfully!"
echo ""
echo "Hooks installed:"
echo "  - pre-commit: Prevents committing sensitive files and tokens"
echo ""
echo "Test with:"
echo "  git add secrets.json  # Should be blocked"
echo ""

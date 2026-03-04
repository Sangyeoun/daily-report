#!/bin/bash

# Security check script

set -e

# Get to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "🔍 Running security checks..."
echo ""

# 1. Check for secrets in git history
echo "1. Checking Git history for secrets..."
if git log --all --full-history -- '*secret*' '*token*' '*.env' 'deployment/samconfig.toml' 2>/dev/null | grep -q .; then
    echo "⚠️  WARNING: Found potential secrets in git history!"
    echo "   Review with: git log --all --full-history -- '*secret*' '*token*' '*.env' 'samconfig.toml'"
else
    echo "✅ No secrets found in git history"
fi
echo ""

# 2. Check .gitignore
echo "2. Checking .gitignore..."
REQUIRED_IGNORES=(".env" ".env.local" "samconfig.toml" "secrets.json")
MISSING=()

for item in "${REQUIRED_IGNORES[@]}"; do
    if ! grep -q "^${item}$" .gitignore 2>/dev/null; then
        MISSING+=("$item")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "⚠️  WARNING: Missing entries in .gitignore:"
    printf '   - %s\n' "${MISSING[@]}"
else
    echo "✅ .gitignore properly configured"
fi
echo ""

# 3. Check for untracked sensitive files
echo "3. Checking for sensitive files..."
SENSITIVE_FILES=(".env" "deployment/samconfig.toml" "deployment/secrets.json" "credentials.json")
FOUND=()

for file in "${SENSITIVE_FILES[@]}"; do
    if [ -f "$file" ]; then
        FOUND+=("$file")
    fi
done

if [ ${#FOUND[@]} -gt 0 ]; then
    echo "⚠️  WARNING: Found sensitive files (ensure they're gitignored):"
    printf '   - %s\n' "${FOUND[@]}"
    echo ""
    echo "   Verify they're ignored:"
    echo "   git check-ignore ${FOUND[@]}"
else
    echo "✅ No sensitive files found in working directory"
fi
echo ""

# 4. Check Python dependencies for vulnerabilities
echo "4. Checking Python dependencies..."
if command -v pip-audit &> /dev/null; then
    pip-audit --desc || echo "⚠️  Found vulnerabilities (see above)"
else
    echo "ℹ️  pip-audit not installed (install with: pip install pip-audit)"
fi
echo ""

# 5. Check AWS Secrets Manager configuration
echo "5. Checking AWS Secrets Manager..."
if aws secretsmanager describe-secret --secret-id daily-report/credentials &> /dev/null; then
    echo "✅ Secrets Manager secret exists"
    
    # Check if it's still placeholder
    SECRET_VALUE=$(aws secretsmanager get-secret-value --secret-id daily-report/credentials --query SecretString --output text)
    if echo "$SECRET_VALUE" | grep -q "PLACEHOLDER"; then
        echo "⚠️  WARNING: Secrets still contain PLACEHOLDER values"
        echo "   Update with: ./scripts/update-secrets.sh"
    else
        echo "✅ Secrets appear to be configured"
    fi
else
    echo "ℹ️  Secrets Manager secret not found (deploy first)"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Security check complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Security Guide

## Overview

This project implements enterprise-grade security:

- ✅ AWS Secrets Manager (encrypted storage)
- ✅ Auto log masking (tokens, emails)
- ✅ Slack signature verification + timestamp
- ✅ IAM least privilege
- ✅ Rate limiting
- ✅ Git hooks (prevent token commits)

## Security Features

### 1. Secrets Management

**All secrets stored in AWS Secrets Manager**:
```bash
# Update secrets
cd deployment
./scripts/update-secrets.sh
rm secrets.json  # Delete immediately!
```

Never commit:
- `deployment/secrets.json`
- `deployment/samconfig.toml`
- `.env`

### 2. Log Masking

Auto-masks sensitive patterns:
- `xoxb-*` → `xoxb-***`
- `ghp_*` → `ghp_***`
- `sk-*` → `sk-***`
- `-----BEGIN PRIVATE KEY-----` → `[MASKED]`
- Emails → `***@***.***`

### 3. Slack Verification

- HMAC-SHA256 signature
- Timestamp validation (±5 minutes)
- Prevents replay attacks

### 4. Access Control

Whitelist users/channels (production recommended):
```toml
AllowedUsers=U01234567,U89ABCDEF
AllowedChannels=C0123456789
```

### 5. Rate Limiting

API Gateway throttling:
- Burst: 10 requests
- Rate: 5 requests/second

## Security Checklist

### Before Deployment
```bash
cd deployment
./scripts/check-security.sh
./scripts/setup-git-hooks.sh
```

- [ ] No secrets in git history
- [ ] Git hooks installed
- [ ] `.gitignore` configured

### After Deployment
- [ ] Secrets Manager updated
- [ ] `secrets.json` deleted
- [ ] Log masking verified
- [ ] Signature verification tested

## Token Management

### Recommended Practices

**GitHub**:
- Use Fine-grained tokens (not classic)
- Minimal scopes (Pull requests: read)
- 90-day expiration
- Bot-specific account

**Rotation** (quarterly):
```bash
# 1. Generate new tokens
# 2. Update secrets.json
cd deployment
./scripts/update-secrets.sh
rm secrets.json
# 3. Revoke old tokens
```

## Incident Response

### If Token Leaked

1. **Revoke immediately**
   - GitHub: https://github.com/settings/tokens
   - Slack: Regenerate in app settings
   - OpenAI: Revoke at dashboard

2. **Disable Lambda**
   ```bash
   aws lambda update-function-configuration \
     --function-name daily-report-generator \
     --reserved-concurrent-executions 0
   ```

3. **Generate new tokens**

4. **Update Secrets Manager**
   ```bash
   cd deployment
   ./scripts/update-secrets.sh
   ```

5. **Re-enable Lambda**
   ```bash
   aws lambda delete-function-concurrency \
     --function-name daily-report-generator
   ```

## Monitoring

### CloudWatch Alarms
- Slash command errors > 5/5min
- Generator errors > 3/5min

### Log Review
```bash
make logs
# Verify tokens are masked (***)
```

## Best Practices

1. **Never hardcode secrets** in code
2. **Always mask logs** with sensitive data
3. **Use Git hooks** to prevent accidental commits
4. **Rotate tokens** quarterly
5. **Monitor CloudWatch** for anomalies
6. **Keep dependencies** updated (`pip-audit`)

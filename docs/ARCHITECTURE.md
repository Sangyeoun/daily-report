# Architecture

## System Overview

Daily report automation using AWS serverless architecture.

## Components

### Lambda Functions

#### 1. SlashCommandFunction
- **Trigger**: API Gateway (Slack slash command)
- **Flow**:
  1. Verify Slack signature + timestamp
  2. Check user/channel authorization
  3. Invoke ReportGeneratorFunction (async)
  4. Return immediate response

#### 2. ReportGeneratorFunction
- **Triggers**: 
  - SlashCommandFunction (async)
  - EventBridge Schedule (17:30 JST)
- **Flow**:
  1. Collect GitHub PRs
  2. Collect Google Calendar events
  3. Collect Slack activity
  4. Generate AI summary (OpenAI)
  5. Post to Slack channel

### Infrastructure

- **API Gateway**: REST API for Slack commands
- **EventBridge**: Cron schedule (17:30 KST = 08:30 UTC)
- **Secrets Manager**: Encrypted credential storage
- **KMS**: Log encryption
- **CloudWatch**: Logs + Alarms

## Data Flow

```
User: /daily-report
  ↓
API Gateway → SlashCommandFunction
  ↓ (signature verify + timestamp check)
  ↓ (async invoke)
ReportGeneratorFunction
  ├→ GitHub API (collect PRs)
  ├→ Google Calendar API (collect events)
  ├→ Slack API (analyze activity)
  └→ OpenAI API (generate summary)
  ↓
Format report (Slack blocks)
  ↓
Post to #backend-daily-report channel
```

## Security Architecture

### Secrets Flow
```
Secrets Manager (encrypted)
  ↓ (runtime load)
Lambda (memory only, never logged)
  ↓ (API calls)
External APIs (Slack, GitHub, etc.)
```

### Log Safety
```
Raw log → LogMasker → CloudWatch (masked)
  xoxb-123 → xoxb-***
  ghp_abc  → ghp_***
  sk-xyz   → sk-***
```

### Request Validation
```
Slack Request
  ↓
1. Signature (HMAC-SHA256) ✓
2. Timestamp (±5 min) ✓
3. User whitelist ✓
4. Channel whitelist ✓
  ↓
Process or Reject (401/403)
```

## IAM Permissions

### SlashCommandFunction
```yaml
Permissions:
  - lambda:InvokeFunction → ReportGeneratorFunction only
  - secretsmanager:GetSecretValue → daily-report/credentials only
```

### ReportGeneratorFunction
```yaml
Permissions:
  - secretsmanager:GetSecretValue → daily-report/credentials only
  - logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
```

## API Integrations

| API | Purpose | Auth | Rate Limit |
|-----|---------|------|------------|
| Slack | Post messages, analyze activity | Bot Token | 1/sec |
| GitHub | Collect PRs | PAT/Fine-grained | 5000/hour |
| Google Calendar | Collect events | Service Account | Quota-based |
| OpenAI | Generate summary | API Key | Tier-based |

## Performance

- **Cold start**: ~2-3 seconds
- **Warm execution**: ~30-60 seconds
  - GitHub: ~10s
  - Calendar: ~5s
  - Slack: ~15s
  - OpenAI: ~10s
- **Memory**: 1024 MB (Report Generator), 512 MB (Slash Command)
- **Timeout**: 600s (Report Generator), 300s (Slash Command)

## Cost Estimation

**Monthly** (1 execution/day):
- Lambda: ~$1
- Secrets Manager: $0.40
- KMS: $1
- API Gateway: $0.10
- CloudWatch: $0.50
- **Total**: ~$3-4/month

## Scalability

**Current**: Single user, synchronous data collection

**Future improvements**:
- Multi-user support (DynamoDB config)
- Parallel API calls (async/await)
- Redis caching
- Step Functions orchestration

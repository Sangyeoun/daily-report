# Daily Report Bot

Automated daily report system that posts to Slack at 17:30 JST.

## Features

- 📝 **GitHub PRs**: Authored PRs (created/updated today)
- 📅 **Google Calendar**: Today's events
- 💬 **Slack Activity**: Message analysis (excluding DMs)
- 🤖 **AI Summary**: GPT-powered insights

## Architecture

```
Slack Command → API Gateway → Lambda → Async → Report Generator → Slack
EventBridge (17:30 JST) → Report Generator → Slack
```

**Stack**: AWS Lambda (Python 3.13) + API Gateway + EventBridge + Secrets Manager

## Security

- ✅ AWS Secrets Manager (encrypted credentials)
- ✅ Auto log masking (tokens/emails)
- ✅ Slack signature + timestamp verification
- ✅ IAM least privilege
- ✅ Rate limiting (10 burst / 5 req/sec)
- ✅ Git hooks (prevent token commits)

Details: [docs/SECURITY.md](docs/SECURITY.md)

## Quick Start

```bash
# 1. Setup
cd deployment
cp secrets.json.example secrets.json  # Add your tokens
cp samconfig.toml.example samconfig.toml  # Configure S3 bucket

# 2. Deploy
cd ..
make deploy

# 3. Update secrets
make update-secrets
rm deployment/secrets.json  # Delete immediately!

# 4. Test
/daily-report  # In Slack
```

Full guide: [docs/SETUP.md](docs/SETUP.md)

## Structure

```
daily-report/
├── src/           # Source code (handlers, collectors, utils)
├── tests/         # Unit tests
├── deployment/    # AWS SAM (template.yaml, scripts/)
└── docs/          # Documentation (3 files)
```

## Commands

```bash
make install        # Install dependencies
make test           # Run tests
make build          # Build SAM
make deploy         # Deploy to AWS
make logs           # View Lambda logs
make security       # Security check
```

## Usage

**Manual**: `/daily-report` in Slack

**Automatic**: Daily at 17:30 JST → `#backend-daily-report`

## Documentation

- [docs/SETUP.md](docs/SETUP.md) - Setup & deployment
- [docs/SECURITY.md](docs/SECURITY.md) - Security guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design

## Cost

~$4/month (1 execution/day)

## License

MIT

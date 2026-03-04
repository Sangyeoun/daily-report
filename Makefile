.PHONY: help install test build deploy clean logs security setup-hooks update-secrets

help:
	@echo "Available commands:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make test           - Run tests"
	@echo "  make build          - Build SAM application"
	@echo "  make deploy         - Deploy to AWS"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make logs           - Tail Lambda logs"
	@echo "  make security       - Run security checks"
	@echo "  make setup-hooks    - Setup Git security hooks"
	@echo "  make update-secrets - Update AWS Secrets Manager"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

build:
	cd deployment && sam build

deploy:
	cd deployment && ./scripts/deploy.sh

clean:
	rm -rf deployment/.aws-sam/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

logs:
	@echo "Select function to tail logs:"
	@echo "1) SlashCommandFunction"
	@echo "2) ReportGeneratorFunction"
	@read -p "Enter choice: " choice; \
	case $$choice in \
		1) cd deployment && sam logs -n SlashCommandFunction --tail ;; \
		2) cd deployment && sam logs -n ReportGeneratorFunction --tail ;; \
		*) echo "Invalid choice" ;; \
	esac

security:
	@echo "🔍 Running security checks..."
	@cd deployment && ./scripts/check-security.sh

setup-hooks:
	@echo "🔧 Setting up Git security hooks..."
	@cd deployment && ./scripts/setup-git-hooks.sh

update-secrets:
	@echo "🔐 Updating AWS Secrets Manager..."
	@cd deployment && ./scripts/update-secrets.sh
	@echo ""
	@echo "⚠️  IMPORTANT: Delete secrets.json now!"
	@echo "  rm deployment/secrets.json"

# Darpan Labs - Unified Makefile for AWS Training Workflow
# Complete automation: Launch → Setup → Train → Download → Chat

.PHONY: help setup test lint fmt clean

# Default target
.DEFAULT_GOAL := help

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1m\033[36mDarpan Labs - AWS Training Workflow\033[0m\n\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Dependencies

setup: ## Install dependencies and setup environment
	pip install -e .
	@echo "✅ Setup complete!"

setup-dev: ## Install development dependencies
	pip install -e ".[dev]"
	pip install ruff black mypy pytest

##@ Complete Workflow (All-in-One)

workflow: ## Run complete workflow (Launch → Setup → Train → Download → Chat)
	./darpan.py workflow

workflow-status: ## Check workflow status
	./darpan.py status

##@ Individual Workflow Steps

launch: ## Launch AWS GPU instance
	./darpan.py launch

setup-instance: ## Setup instance (run on EC2 instance)
	./darpan.py setup

train: ## Train all persona models (run on EC2 instance)
	./darpan.py train --auto-shutdown

train-subset: ## Train specific personas (example: k0 k1 k2)
	./darpan.py train --twins bargain_hunter premium_buyer deal_hunter

train-parallel: ## Train with parallel processing (multi-GPU)
	./darpan.py train --parallel --auto-shutdown

download: ## Download trained models from S3
	./darpan.py download

chat: ## Interactive chat with trained personas
	./darpan.py chat

sync-code: ## Sync local code changes to EC2 instance (for rapid iteration)
	@echo "📤 Syncing local code to EC2..."
	@read -p "Enter EC2 instance IP: " EC2_IP; \
	KEY_FILE="$${DARPAN_SSH_KEY:-$$HOME/darpan-training.pem}"; \
	rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
	  --exclude '.git' --exclude 'artifacts' --exclude 'DATA' --exclude '*.egg-info' \
	  --exclude '.pytest_cache' --exclude '.mypy_cache' --exclude '.ruff_cache' \
	  -e "ssh -i $$KEY_FILE -o StrictHostKeyChecking=no" \
	  ./ ubuntu@$$EC2_IP:~/mvp_v1.0/
	@echo "✅ Code synced to EC2"

setup-remote: ## Setup EC2 instance (run setup script via SSH)
	@echo "⚙️  Setting up EC2 instance..."
	@read -p "Enter EC2 instance IP: " EC2_IP; \
	KEY_FILE="$${DARPAN_SSH_KEY:-$$HOME/darpan-training.pem}"; \
	echo "Creating directories..."; \
	ssh -i $$KEY_FILE ubuntu@$$EC2_IP "mkdir -p ~/mvp_v1.0/artifacts/llm_adapters ~/mvp_v1.0/DATA"; \
	echo "Running setup script (this takes ~10-15 minutes)..."; \
	ssh -i $$KEY_FILE ubuntu@$$EC2_IP "cd ~/mvp_v1.0 && bash scripts/aws/setup_training_instance.sh"

train-remote: ## Start training on EC2 instance (via SSH in tmux)
	@echo "🚀 Starting training on EC2..."
	@read -p "Enter EC2 instance IP: " EC2_IP; \
	KEY_FILE="$${DARPAN_SSH_KEY:-$$HOME/darpan-training.pem}"; \
	ssh -i $$KEY_FILE ubuntu@$$EC2_IP "cd ~/mvp_v1.0 && source venv/bin/activate && tmux new-session -d -s training './darpan.py train --auto-shutdown' && echo '✅ Training started in tmux session. To attach: ssh to EC2 and run: tmux attach -t training'"

train-remote-status: ## Check training status on EC2
	@echo "📊 Checking training status..."
	@read -p "Enter EC2 instance IP: " EC2_IP; \
	KEY_FILE="$${DARPAN_SSH_KEY:-$$HOME/darpan-training.pem}"; \
	ssh -i $$KEY_FILE ubuntu@$$EC2_IP "cd ~/mvp_v1.0 && tail -20 training_output.log 2>/dev/null || echo 'No training log found'"

##@ Local Development

serve: ## Start local API server
	uvicorn src.api.service:app --reload --host 0.0.0.0 --port 8000

serve-prod: ## Start production API server
	uvicorn src.api.service:app --host 0.0.0.0 --port 8000 --workers 4

interact: ## Interactive CLI with personas
	python interact_cli.py

##@ Testing & Quality

test: ## Run all tests
	pytest -q

test-verbose: ## Run tests with verbose output
	pytest -v

test-specific: ## Run specific test file (e.g., make test-specific FILE=test_health.py)
	pytest TESTS/$(FILE) -v

gate: ## Run separation quality gates
	python scripts/eval_separation.py

guard: ## Run reason guard tests
	pytest TESTS/test_reason_guard.py -v

metrics: ## Evaluate separation metrics
	python scripts/eval_separation.py

all-checks: test gate guard ## Run all tests and quality checks
	@echo "✅ All checks passed!"

##@ Code Quality

lint: ## Run linters
	ruff .
	mypy src/

fmt: ## Format code
	ruff --fix . || true
	black .
	isort .

clean: ## Clean build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f server.log
	@echo "✅ Cleaned build artifacts"

clean-models: ## Remove downloaded models (use with caution!)
	rm -rf artifacts/llm_adapters/
	@echo "⚠️  Removed all downloaded models"

##@ Dataset Management

dataset-opera: ## Download Opera dataset
	python scripts/download_opera_dataset.py

dataset-info: ## Show dataset information
	@python -c "from src.datasets import DatasetFactory; ds = DatasetFactory.create('opera'); print(ds.get_stats())"

personas-discover: ## Discover personas from Opera dataset
	python scripts/opera/discover_personas_from_opera.py --augment --min_rows 200 --max_personas 24

personas-list: ## List all available personas
	@python -c "import json; from pathlib import Path; data = json.loads(Path('DATA/personas.json').read_text()); print(f'Total Personas: {len(data[\"personas\"])}'); [print(f'  {i+1}. {p[\"label\"]} ({p[\"id\"]})') for i, p in enumerate(data['personas'])]"

##@ Training Data Preparation

prep-sft-data: ## Prepare SFT training data
	python scripts/prepare_llm_sft_data.py

prep-opera-sft: ## Prepare SFT data from Opera dataset
	python scripts/opera/prepare_sft_from_opera.py --cfg CONFIGS/opera/fields.yaml

##@ Model Training (Local)

train-local-all: ## Train all adapters locally (requires GPU)
	python scripts/train_all_adapters.py

train-local-one: ## Train single adapter (example: make train-local-one TWIN=k3)
	python scripts/train_llm_persona_sft.py --twin_id $(TWIN)

eval-adapter: ## Evaluate trained adapter (example: make eval-adapter TWIN=k3)
	python scripts/eval_llm_persona_sft.py --twin_id $(TWIN)

##@ AWS Cost Management

cost-status: ## Check current AWS costs
	@echo "📊 Checking AWS costs..."
	@aws ce get-cost-and-usage \
		--time-period Start=2025-10-01,End=2025-10-12 \
		--granularity MONTHLY \
		--metrics BlendedCost \
		--query 'ResultsByTime[0].Total.BlendedCost.Amount' \
		--output text 2>/dev/null || echo "❌ AWS CLI not configured"

cost-alert: ## Set budget alert (default: $5)
	aws cloudwatch put-metric-alarm \
		--alarm-name darpan-training-cost-alert \
		--alarm-description "Alert if training costs exceed threshold" \
		--metric-name EstimatedCharges \
		--namespace AWS/Billing \
		--statistic Maximum \
		--period 21600 \
		--threshold 5 \
		--comparison-operator GreaterThanThreshold

##@ S3 Management

s3-list: ## List files in S3 bucket
	@BUCKET=$${TRAINING_S3_BUCKET:-darpan-training}; \
	echo "📦 Listing s3://$$BUCKET/"; \
	aws s3 ls s3://$$BUCKET/trained_adapters/ --recursive --human-readable

s3-upload: ## Upload local models to S3
	@BUCKET=$${TRAINING_S3_BUCKET:-darpan-training}; \
	aws s3 sync artifacts/llm_adapters/ s3://$$BUCKET/trained_adapters/

s3-download: ## Download models from S3
	@BUCKET=$${TRAINING_S3_BUCKET:-darpan-training}; \
	aws s3 sync s3://$$BUCKET/trained_adapters/ artifacts/llm_adapters/

##@ API Documentation

openapi: ## Export OpenAPI spec
	python scripts/export_openapi.py

docs-api: ## View API documentation
	@echo "🌐 API docs will be at http://localhost:8000/docs"
	@echo "Run 'make serve' first if not already running"

##@ Docker

docker-build: ## Build Docker image
	docker build -t darpan/what-if-simulator:latest .

docker-run: ## Run Docker container
	docker compose up --build

docker-stop: ## Stop Docker containers
	docker compose down

##@ Reports & Analytics

report-confusion: ## Generate persona confusion matrix
	python scripts/reports/persona_confusion.py

report-deltas: ## Generate scenario delta heatmap
	python scripts/reports/scenario_delta_heatmap.py

##@ Testing & Evaluation

test-personas: ## Test persona response quality with new core logic
	python examples/test_persona_responses.py

test-decide: ## Run decide_then_verbalize example
	python examples/run_decide_then_verbalize.py

verify-models: ## Verify all 18 persona models are present
	@echo "📦 Verifying persona models..."
	@COUNT=$$(find artifacts/llm_adapters -name "adapter_model.safetensors" 2>/dev/null | wc -l | tr -d ' '); \
	if [ $$COUNT -eq 18 ]; then \
		echo "✅ All 18 persona models present"; \
	else \
		echo "⚠️  Found $$COUNT models (expected 18)"; \
	fi

##@ Admin & Utilities

pins: ## List all pinned twin configurations
	python scripts/cli.py pins --token changeme

reload-all: ## Reload all twins (requires API running)
	@python -c 'import json,http.client; from pathlib import Path; p=json.loads(Path("DATA/personas.json").read_text()); [print(t["id"], http.client.HTTPConnection("127.0.0.1",8000).request("POST",f"/admin/twin/{t[\"id\"]}/reload",headers={"X-Admin-Token":"changeme"}) or http.client.HTTPConnection("127.0.0.1",8000).getresponse().status) for t in p["personas"]]'

train-status: ## Check training status via API
	curl -H "X-Admin-Token: changeme" http://127.0.0.1:8000/admin/train/status

##@ Quick Start Guide

quickstart: ## Show quick start guide
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                    DARPAN LABS - QUICK START GUIDE                         ║"
	@echo "╚════════════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📋 COMPLETE WORKFLOW (Automated):"
	@echo "   make workflow              # Run everything: Launch → Setup → Train → Download → Chat"
	@echo ""
	@echo "🔧 STEP-BY-STEP WORKFLOW:"
	@echo "   1. make launch             # Launch AWS GPU instance"
	@echo "   2. make setup-instance     # Setup environment (run on EC2)"
	@echo "   3. make train              # Train models (run on EC2)"
	@echo "   4. make download           # Download trained models"
	@echo "   5. make chat               # Chat with personas"
	@echo ""
	@echo "💻 LOCAL DEVELOPMENT:"
	@echo "   make setup                 # Install dependencies"
	@echo "   make serve                 # Start API server"
	@echo "   make test                  # Run tests"
	@echo "   make interact              # Interactive CLI"
	@echo ""
	@echo "📊 STATUS & MONITORING:"
	@echo "   make workflow-status       # Check workflow progress"
	@echo "   make cost-status           # Check AWS costs"
	@echo "   make s3-list               # List S3 contents"
	@echo ""
	@echo "📚 More commands: make help"
	@echo ""

.PHONY: workflow workflow-status launch setup-instance train train-subset train-parallel download chat sync-code
.PHONY: setup-remote train-remote train-remote-status
.PHONY: serve serve-prod interact test test-verbose test-specific gate guard metrics all-checks
.PHONY: lint fmt clean clean-models dataset-opera dataset-info personas-discover personas-list
.PHONY: prep-sft-data prep-opera-sft train-local-all train-local-one eval-adapter
.PHONY: cost-status cost-alert s3-list s3-upload s3-download openapi docs-api
.PHONY: docker-build docker-run docker-stop report-confusion report-deltas
.PHONY: test-personas test-decide verify-models pins reload-all train-status quickstart

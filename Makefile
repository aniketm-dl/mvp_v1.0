.DEFAULT_GOAL := help

PYTHON := python
PIP := pip
STREAMLIT := streamlit

TRAINING_PAIRS ?= DATA/OPeRA/processed/ssr_training_pairs.jsonl
OUTPUT_DIR ?= models/ssr_reference
BATCH_SIZE ?= 32
EMBEDDING_EPOCHS ?= 10
REGRESSION_EPOCHS ?= 20
USE_REFERENCES ?= 0
HUMAN_DATA ?= DATA/OPeRA/processed/ssr_training_pairs.jsonl
SYNTHETIC_RESPONSES ?=
ANCHOR_SCENARIOS ?=
FLR_SCENARIOS ?=
INCLUDE_REGRESSION ?= 1
LLM_PROVIDER ?= openai
LLM_MODEL ?= gpt-4o-mini
LLM_TEMPERATURE ?= 0.5
LLM_SAMPLES_PER_PROMPT ?= 2
LLM_MAX_SESSIONS ?= 0
LLM_SEED ?= 42

define PRINT_HELP
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1m\033[36mDarpan Labs – OPeRA-SSR Toolkit\033[0m\n"} \
	/^[a-zA-Z0-9_\-]+:.*##/ { printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2 } \
	/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0,5) }' $(MAKEFILE_LIST)
endef

##@ General
help: ## Show this help message
	$(PRINT_HELP)

setup: ## Install project dependencies
	$(PIP) install -e .

setup-dev: ## Install project + development dependencies
	$(PIP) install -e ".[dev]"
	$(PIP) install black isort ruff mypy pytest

##@ Data Pipeline
download-opera: ## Download OPeRA dataset from HuggingFace
	$(PYTHON) scripts/01_download_opera.py

preprocess-opera: ## Align OPeRA data and generate SSR training pairs
	$(PYTHON) scripts/02_preprocess_opera.py

preprocess-opera-llm: ## Run preprocessing with LLM elicitation (set OPENAI_API_KEY first)
	$(PYTHON) scripts/02b_preprocess_opera_with_llm.py \
		--llm-provider $(LLM_PROVIDER) \
		--llm-model $(LLM_MODEL) \
		--llm-temperature $(LLM_TEMPERATURE) \
		--samples-per-prompt $(LLM_SAMPLES_PER_PROMPT) \
		--seed $(LLM_SEED) \
		$(if $(filter-out 0,$(LLM_MAX_SESSIONS)),--max-llm-sessions $(LLM_MAX_SESSIONS),)

discover-personas: ## Discover personas (UMAP + HDBSCAN + GPT-4o summaries)
	$(PYTHON) scripts/03_discover_personas.py --use-llm-summary

##@ Model Training & Evaluation
train-ssr: ## Train SSR model (set USE_REFERENCES=1 for LLM-elicited data)
	$(PYTHON) scripts/04_train_ssr.py \
		--training-pairs $(TRAINING_PAIRS) \
		--out $(OUTPUT_DIR) \
		--batch-size $(BATCH_SIZE) \
		--embedding-epochs $(EMBEDDING_EPOCHS) \
		--regression-epochs $(REGRESSION_EPOCHS) \
		$(if $(filter 1,$(USE_REFERENCES)),--use-references,)

evaluate-ssr: ## Evaluate trained SSR model
	$(PYTHON) scripts/07_evaluate.py \
		--ssr-model $(OUTPUT_DIR) \
		--human-data $(HUMAN_DATA) \
		--out-dir reports \
		$(if $(SYNTHETIC_RESPONSES),--synthetic-responses $(SYNTHETIC_RESPONSES),) \
		$(foreach sc,$(ANCHOR_SCENARIOS),--anchor-scenario $(sc)) \
		$(foreach sc,$(FLR_SCENARIOS),--flr-scenario $(sc)) \
		$(if $(filter 1,$(INCLUDE_REGRESSION)),--include-regression,)

demo: ## Launch Streamlit demo application
	$(STREAMLIT) run src/app/main.py

pipeline-local: ## Run entire pipeline locally (download → preprocess → personas → train → evaluate)
	$(MAKE) download-opera
	$(MAKE) preprocess-opera
	$(MAKE) discover-personas
	$(MAKE) train-ssr
	$(MAKE) evaluate-ssr

##@ AWS
aws-train: ## Run complete AWS training pipeline (set TRAINING_S3_BUCKET first)
	bash scripts/aws/train_complete_pipeline.sh --auto-shutdown

##@ Quality
lint: ## Run code linters
	ruff .
	mypy src/

fmt: ## Format codebase
	black src scripts TESTS
	isort src scripts TESTS
	ruff --fix src scripts TESTS

test: ## Run full test suite
	pytest TESTS -q

test-unit: ## Run verbose unit tests
	pytest TESTS -v

clean: ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

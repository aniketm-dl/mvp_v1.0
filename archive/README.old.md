# Darpan Labs — What-If Simulator (Twins MVP)

You will build a deterministic what-if simulator that answers: what happens if we change price, show a promo badge, switch ad copy, or promise faster delivery? Twins choose among the options visible on the page, explain in one short line, and we report deltas vs the base.

## Quick Start

### Local Development (with stub personas)
1) Read SPECS/WHAT_IF_SIMULATOR_SPEC.md and API/SCHEMAS.md.
2) Install: `make setup`
3) Run tests: `make test`
4) Serve API: `make serve`
5) Follow TESTS/acceptance.md.

### Training Real LLM Personas

**🎯 Recommended: Mistral-7B-Instruct-v0.2** (no gated access!)

**Option A: Google Colab (Recommended - needs GPU)**
- See: **[DOCS/MISTRAL_QUICKSTART.md](DOCS/MISTRAL_QUICKSTART.md)** for 5-step guide
- Model: **Mistral-7B-Instruct-v0.2** (instant access, better performance)
- GitHub: https://github.com/aniketm-dl/mvp_v1.0
- Use Colab Pro for GPU training (2-4 hours for 18 personas)
- Use Claude Code for local development and testing
- Notebook: `notebooks/train_mistral_on_colab.ipynb`

**Option B: Local Training (requires 16GB+ GPU)**
- `python scripts/train_all_adapters.py`
- Time: 10-20 hours on CPU, 3-4 hours on T4 GPU
- Default model: Mistral-7B-Instruct-v0.2

### Interactive Chat with Personas
```bash
python interact_cli.py
```

## API Endpoints

1) POST /match → twin weights for a user or session.
2) POST /recommend → top-N and optional short reason.
3) POST /simulate → run scenarios; returns per-twin and blended results, plus deltas vs base.

We predict only among page-visible items or actions.

## Project Structure

- **src/** - Core application code (API, models, reasoning)
- **scripts/** - Training, evaluation, and utility scripts
- **DATA/** - Personas, training data, copy variants
- **CONFIGS/** - Configuration files for serving and training
- **DOCS/** - Documentation (including Colab workflow)
- **notebooks/** - Jupyter/Colab notebooks for training
- **artifacts/** - Trained model adapters (generated)

## Hybrid Development Workflow

**Use Claude Code locally for:**
- Code editing and development
- Creating training data
- Testing and debugging
- Running evaluations

**Use Google Colab for:**
- GPU-intensive training
- Batch processing
- Model experiments

See [DOCS/COLAB_WORKFLOW.md](DOCS/COLAB_WORKFLOW.md) for complete workflow details.

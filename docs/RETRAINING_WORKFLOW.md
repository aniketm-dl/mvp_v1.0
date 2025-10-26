# SSR Retraining Workflow

Use this checklist whenever you change data processing, persona discovery, or SSR model code.  
It assumes the active branch is `mvp_opera` and you are targeting the OPeRA dataset.

---

## 1. Local Rebuild (Recommended Before AWS)

```bash
# 1. Reinstall dependencies if requirements changed
pip install -e .

# 2. Download / refresh raw data (idempotent)
python scripts/01_download_opera.py

# 3. Regenerate features and SSR pairs
python scripts/02_preprocess_opera.py
# For LLM-based SSR pairs:
python scripts/02b_preprocess_opera_with_llm.py \
  --llm-provider openai \
  --samples-per-prompt 2 \
  --max-llm-sessions 250

# 4. Re-run persona discovery (UMAP + HDBSCAN + GPT summaries)
python scripts/03_discover_personas.py --use-llm-summary

# 5. Train SSR model (pass --use-references if you created *_llm pairs)
python scripts/04_train_ssr.py \
  --training-pairs DATA/OPeRA/processed/ssr_training_pairs_llm.jsonl \
  --use-references

# 6. Evaluate changes (anchors + baselines)
python scripts/07_evaluate.py \
  --ssr-model models/ssr_reference \
  --human-data DATA/OPeRA/processed/ssr_training_pairs.jsonl \
  --anchor-scenario persona=DATA/OPeRA/processed/ssr_training_pairs_llm.jsonl \
  --include-regression
```

Key artifacts refreshed:

| Artifact | Path |
|----------|------|
| Aligned sessions | `DATA/OPeRA/processed/aligned_sequences.jsonl` |
| Persona features | `DATA/OPeRA/processed/persona_features.parquet` |
| SSR pairs (standard) | `DATA/OPeRA/processed/ssr_training_pairs.jsonl` |
| SSR pairs (LLM) | `DATA/OPeRA/processed/ssr_training_pairs_llm.jsonl` |
| Personas | `models/persona_profiles.json` |
| SSR model | `models/ssr_reference/` |
| Evaluation | `reports/evaluation_results.json`, `scenario_summary.csv`, `concept_evaluation_*.csv`, `subgroup_metrics_*.csv` |

---

## 2. AWS Rebuild (Optional for Large Runs)

1. **Commit & push** your changes  
   ```bash
   git status
   git add <files>
   git commit -m "feat: adjust SSR trainer"
   git push origin mvp_opera
   ```

2. **Export required env vars** on your local machine  
   ```bash
   export OPENAI_API_KEY=sk-...
   export TRAINING_S3_BUCKET=darpan-training-$(whoami)
   ```

3. **Run the managed pipeline**  
   ```bash
   bash scripts/aws/train_complete_pipeline.sh --auto-shutdown \
     --use-llm-elicitations \
     --llm-max-samples 500
   ```

   *The script now performs download → preprocessing → persona discovery → SSR training → evaluation → S3 sync.  LLM elicitation is optional and controlled via flags.*

4. **Retrieve outputs** (if S3 syncing is enabled)  
   ```bash
   aws s3 sync s3://$TRAINING_S3_BUCKET/models/ models/
   aws s3 sync s3://$TRAINING_S3_BUCKET/reports/ reports/
   ```

---

## 3. Regression Checklist

- ✅ `pytest` passes (especially `TESTS/test_opera_parse_and_dataset.py`, `TESTS/test_llm_elicitation.py`, `TESTS/test_anchor_mapper.py`, `TESTS/test_human_metrics.py`, `TESTS/test_evaluation_utils.py`)
- ✅ `scripts/07_evaluate.py` hits target metrics (Spearman ≥ 0.70, KS ≥ 0.80)
- ✅ Streamlit demo runs (`make demo`)
- ✅ Updated artifacts committed or documented (e.g., new model version)

If any step fails, fix the issue locally, rerun the corresponding command, and repeat the evaluation pipeline.

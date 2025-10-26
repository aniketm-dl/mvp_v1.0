# Darpan Labs MVP Scope - OPeRA-SSR-Twin System

## Executive Summary

This MVP transforms Darpan Labs from an e-commerce simulator with manually-defined personas into a **data-driven behavioral prediction platform** grounded in real user data from the OPeRA (Open Persona Research Archive) dataset.

## Domain Focus

**Primary Domain**: E-commerce behavioral prediction
**Decision Task**: Predict user choice distributions and ratings for product options under varying contexts (price, promotions, delivery, ad copy)

## Core Components

### 1. Data Foundation: OPeRA Dataset
- **Survey Data**: Demographics (age, gender, income, education) + Psychographics (OCEAN personality scores)
- **Session Logs**: User interactions (clicks, searches, cart adds, purchases)
- **Rationales**: Free-text explanations for user decisions ("Why did you choose X?")
- **Outcomes**: Final choices and satisfaction ratings (1-5 Likert scale)

### 2. Persona Discovery (Data-Driven)
- **Method**: UMAP dimensionality reduction + HDBSCAN density-based clustering
- **Input**: 12-D feature vectors (3-D demographics + 4-D psychographics + 5-D OCEAN)
- **Output**: 8-12 discovered persona archetypes with interpretable labels
- **Validation**: Silhouette score ≥ 0.35, manual review for business interpretability

### 3. SSR Engine (Semantic Similarity Rating)
- **Architecture**: Fine-tuned sentence-transformers (all-MiniLM-L6-v2) + regression head
- **Training**: Contrastive loss on (persona_vec, stimulus_text, likert_score) triplets
- **Inference**: Given (persona_id, new_stimulus) → P(Likert=1..5) distribution
- **Performance**: <50ms per prediction, generalizes to unseen ad copy/prices

### 4. Hybrid Twin System
- **Fast Path (SSR)**: Embedding-based, deterministic, scales to 100+ personas
- **Slow Path (LLM)**: Mistral-7B LoRA adapters, persona-specific explanations
- **Fusion**: Weighted blend α*P_ssr + (1-α)*P_llm (default α=0.6)
- **Output**: Predicted choice + probability + grounded rationale

### 5. Evaluation Framework
- **Primary Metric**: Kolmogorov-Smirnov similarity (predicted vs. actual distributions) ≥ 0.80
- **Secondary Metrics**:
  - Spearman correlation (predicted vs. actual ratings) ≥ 0.70
  - Separation metrics (silhouette, JSD, ARI) for persona differentiation
- **Dashboard**: Interactive Plotly visualization (reports/eval_dashboard.html)

### 6. Interactive Demo
- **Platform**: Streamlit web app
- **User Flow**: Select persona → Define scenario (price/promo/delivery/copy) → View prediction + explanation
- **Backend**: FastAPI service (existing /simulate + new /ssr/predict)

## Success Criteria

### Must-Have (P1)
1. ✅ **KS Similarity ≥ 0.80**: Predictions match human behavior distributions
2. ✅ **Correlation ≥ 0.70**: Rating predictions align with actual ratings
3. ✅ **SSR Inference <50ms**: Fast enough for real-time A/B testing
4. ✅ **8-12 Discoverable Personas**: Clustering produces interpretable archetypes
5. ✅ **Streamlit Demo Works**: Non-technical users can explore scenarios

### Should-Have (P2)
1. 📊 Evaluation dashboard auto-generates on each training run
2. 📓 Jupyter notebooks for EDA and model prototyping
3. 🧪 Unit tests for SSR inference and persona discovery
4. 📚 Documentation for SSR methodology and OPeRA integration

### Nice-to-Have (P3)
1. 🎯 Counterfactual fairness testing (demographics flip → measure Δprediction)
2. 📄 PDF persona profile reports
3. 🔔 SNS notifications on training completion
4. 🌐 Multi-dataset support (Amazon reviews, Shopify checkouts)

## Out of Scope for MVP

- ❌ Multi-turn conversational interactions (focus on single-decision prediction)
- ❌ Real-time streaming data ingestion (batch processing only)
- ❌ Production-grade authentication/authorization (demo-only security)
- ❌ Mobile app (web app sufficient for MVP)
- ❌ Recommendation ranking systems (choice prediction only)

## Technical Constraints

### Determinism
- SSR: Fixed seed, no sampling, byte-identical outputs
- LLM: Temperature=0, top_p=1, canonical sorting
- Quantization: At feature boundaries only, maintain reproducibility

### Separation Quality
- **Silhouette ≥ 0.35**: Personas must be distinguishable in embedding space
- **JSD ≥ 0.10**: Probability distributions must differ meaningfully across personas
- **ARI ≥ 0.80**: Clustering must be stable across random seeds

### Reason Quality
- **Length**: ≤20 tokens per explanation
- **Grounding**: Must reference visible context (price, promo, delivery)
- **Validation**: ReasonGuard checks for hallucinated numbers and banned terms

### AWS Infrastructure
- **Training Instance**: g5.xlarge (A10G, 24GB VRAM) or g4dn.xlarge (T4, 16GB VRAM)
- **Training Time**: ~2 hours for 8-12 persona adapters + SSR model
- **Storage**: S3 bucket for model artifacts, training data, evaluation reports
- **Cost**: <$1 per full training run (spot instances)

## Data Flow

```
OPeRA Raw Data (survey + sessions + rationales + outcomes)
  ↓ 02_preprocess_opera.py
Aligned Sequences (triplets: session → action → outcome)
  ↓ 03_discover_personas.py
Persona Profiles (8-12 clusters with labels)
  ↓ 04_train_ssr.py
SSR Reference Model (embeddings → Likert distributions)
  ↓ 05_prepare_sft_data.py
Twin Training Data (persona-specific conversations)
  ↓ 06_train_twins.py
LLM Adapters (Mistral-7B LoRA for each persona)
  ↓ hybrid.py
Hybrid Predictions (SSR + LLM fusion)
  ↓ 07_evaluate.py
Evaluation Dashboard (KS test + correlation metrics)
  ↓ 08_deploy.py
Streamlit App (interactive demo)
```

## Acceptance Criteria

### For Data Pipeline
- [ ] `data/processed/aligned_sequences.jsonl` exists with ≥1000 valid triplets
- [ ] `data/processed/persona_features.parquet` contains 12-D feature vectors
- [ ] `data/processed/ssr_training_pairs.jsonl` has (persona, stimulus, likert) tuples

### For Persona Discovery
- [ ] `models/persona_profiles.json` contains 8-12 personas
- [ ] Each persona has: id, label, description, psychographic_tags, ocean_scores
- [ ] Silhouette score ≥ 0.35 in validation report

### For SSR Engine
- [ ] `models/ssr_reference.pkl` loads successfully
- [ ] Inference: predict("p01", "Free shipping") returns distribution in <50ms
- [ ] Training converges: validation loss <0.5, correlation ≥ 0.70

### For Hybrid System
- [ ] API endpoint /ssr/predict returns Likert distribution
- [ ] API endpoint /simulate uses hybrid fusion (SSR + LLM)
- [ ] Explanations pass ReasonGuard validation

### For Evaluation
- [ ] `reports/eval_dashboard.html` opens in browser
- [ ] Dashboard shows KS similarity ≥ 0.80 for ≥70% of personas
- [ ] Correlation chart shows Spearman ≥ 0.70

### For Streamlit App
- [ ] `streamlit run src/app/main.py` starts without errors
- [ ] UI allows: persona selection, scenario configuration, prediction viewing
- [ ] Results display: choice, probability, explanation, comparison chart

## Timeline

**Week 1: Data + Personas**
- Day 1-2: OPeRA preprocessing (alignment.py + 02_preprocess_opera.py)
- Day 3-4: Persona discovery (discovery.py + profiler.py + 03_discover_personas.py)
- Day 5: Validation and documentation

**Week 2: SSR + Hybrid**
- Day 1-2: SSR embedder + trainer (embedder.py + trainer.py + 04_train_ssr.py)
- Day 3: SSR inference + API endpoint (inference.py + ssr.py)
- Day 4-5: Hybrid system (hybrid.py) + existing LLM integration

**Week 3: Evaluation + Demo**
- Day 1-2: Evaluation framework (ks_test.py + dashboard.py + 07_evaluate.py)
- Day 3-4: Streamlit app (main.py + components/ + 08_deploy.py)
- Day 5: End-to-end testing on AWS

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| OPeRA data quality issues | High | Add data validation checks, handle missing values gracefully |
| SSR model underfits | Medium | Hyperparameter tuning, try larger embedding models (e5-large) |
| Personas not separable | High | Adjust clustering parameters, add more features (behavioral signals) |
| LLM adapters too slow | Medium | Use SSR-only mode (α=1), optimize policy heads |
| AWS cost overruns | Low | Use spot instances, set budget alerts, auto-shutdown |

## Future Enhancements (Post-MVP)

1. **Multi-dataset support**: Extend to Amazon reviews, Shopify checkouts
2. **Real-time inference**: WebSocket API for streaming predictions
3. **A/B testing framework**: Automated experiment design and analysis
4. **Persona evolution**: Track how personas change over time
5. **Explainability**: SHAP values for feature attribution

## References

- OPeRA Dataset: [Link to dataset documentation]
- Sentence-Transformers: https://www.sbert.net/
- UMAP: https://umap-learn.readthedocs.io/
- HDBSCAN: https://hdbscan.readthedocs.io/
- Streamlit: https://streamlit.io/

---

**Document Version**: 1.0
**Last Updated**: 2025-01-25
**Owner**: Darpan Labs Engineering Team

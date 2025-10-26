# OPeRA-SSR Flow Overview

```mermaid
flowchart TD
    A[01_download_opera.py<br/>OPeRA raw parquet/jsonl] --> B[02_preprocess_opera.py<br/>Alignment + features]
    B --> C[02b_preprocess_opera_with_llm.py<br/>Persona-conditioned LLM responses<br/>(optional)]
    B --> D[persona_features.parquet]
    B --> E[ssr_training_pairs.jsonl<br/>(human ratings)]
    C --> F[ssr_training_pairs_llm.jsonl<br/>(LLM statements × anchors)]

    E --> G[03_discover_personas.py<br/>UMAP + HDBSCAN + GPT summaries]
    G --> H[models/persona_profiles.json]

    E --> I[04_train_ssr.py<br/>Contrastive fine-tuning]
    F --> I
    I --> J[models/ssr_reference/<br/>embedding_model + regression_head]

    F --> K[SSRAnchorMapper<br/>text-embedding-3-small<br/>6 anchor sets]
    J --> L[SSRInference<br/>regression fallback]

    subgraph Evaluation
        K --> M[07_evaluate.py<br/>KS similarity · MAE/RMSE<br/>Pearson/Spearman · correlation attainment]
        L --> M
        E --> M
    end

    M --> N[reports/<br/>evaluation_results.json<br/>scenario_summary.csv<br/>concept/subgroup/pmf tables<br/>Plotly dashboards]
    J --> O[src/app/main.py<br/>Streamlit demo]
```

**Legend**

- **Blue blocks** (scripts) orchestrate pipeline steps.
- **Orange blocks** represent persisted artefacts reused downstream.
- **Green blocks** are runtime services/components (LLM elicitation, anchor mapper, inference).
- **Evaluation** consumes both synthetic responses and trained models to produce KS, correlation attainment, subgroup tables, and aggregate PMFs.

The AWS helper `scripts/aws/train_complete_pipeline.sh` stitches these steps together on a GPU instance, tagging the EC2 resource as `mvp_opera_do_not_delete` and syncing processed data, models, and reports back to S3.

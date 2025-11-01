# Clustering & Persona Identification System

## Overview

This document describes the comprehensive persona identification and clustering system for the Digital Twin Simulator. The system provides:

1. **Flexible Twin Creation**: Unsupervised clustering with configurable parameters
2. **Full Transparency**: Explainable assignments with feature importance
3. **Hierarchical Analysis**: Understanding persona relationships and splits
4. **Live Progress Tracking**: Real-time visibility into clustering pipeline
5. **API Endpoints**: Access assignment details and visualizations

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                 Clustering Pipeline                      │
│  (scripts/cluster_personas.py)                          │
│  - Loads user behavioral data                           │
│  - Performs unsupervised clustering                     │
│  - Generates twin bank and personas                     │
│  - Computes quality metrics                             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Twin Bank                              │
│  (DATA/twin_bank.json)                                  │
│  - Twin centers (15-D embeddings)                       │
│  - Persona labels and descriptions                      │
│  - Metadata (version, method, metrics)                  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Assignment & Explainability                 │
│  (src/metrics/explainability.py)                        │
│  - Feature importance calculation                       │
│  - Natural language explanations                        │
│  - Distance computations                                │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   API Endpoints                          │
│  GET /user/{user_id}/assignment                         │
│  GET /metrics/cluster_map                               │
│  GET /metrics/hierarchy                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Running the Clustering Pipeline

### Method 1: Interactive Mode

```bash
python scripts/cluster_personas.py --interactive
```

This will prompt you for:
- Number of personas to create
- Clustering method (K-Means, GMM, HDBSCAN, Hierarchical)
- LLM model for persona descriptions
- Feature weights (behavior/psychographic/demographic)
- Random seed for reproducibility

### Method 2: Configuration File

```bash
python scripts/cluster_personas.py --config CONFIGS/clustering/cluster_config.yaml
```

### Example Configuration

```yaml
# CONFIGS/clustering/cluster_config.yaml

n_clusters: 10
clustering_method: "kmeans"
llm_model: "gpt-4"
random_seed: 42

feature_weights:
  behavior: 0.5
  psychographic: 0.3
  demographic: 0.2

separation_thresholds:
  silhouette_min: 0.35
  mean_jsd_min: 0.10
  ari_min: 0.80

verbosity: "verbose"
show_progress: true
```

### Customizable Parameters

#### Core Settings
- **n_clusters**: Number of personas to create (default: 10)
- **clustering_method**: `"kmeans"`, `"gmm"`, `"hdbscan"`, `"hierarchical"`
- **llm_model**: LLM for generating persona descriptions
- **random_seed**: For reproducibility

#### Feature Engineering
- **feature_weights**: Balance behavior, psychographic, demographic signals
- **normalize_features**: Standardize before clustering (recommended: true)
- **apply_pca**: Dimensionality reduction before clustering

#### Quality Gates
- **silhouette_min**: Minimum cluster cohesion (0.35)
- **mean_jsd_min**: Minimum twin differentiation (0.10)
- **ari_min**: Minimum stability (0.80)
- **fail_on_low_quality**: Stop if gates don't pass

#### Algorithm-Specific

**K-Means:**
```yaml
kmeans:
  n_init: 50
  max_iter: 300
  algorithm: "lloyd"
```

**GMM:**
```yaml
gmm:
  covariance_type: "full"
  n_init: 10
  max_iter: 100
```

**HDBSCAN:**
```yaml
hdbscan:
  min_cluster_size: 20
  min_samples: 5
  metric: "euclidean"
```

**Hierarchical:**
```yaml
hierarchical_linkage: "ward"
hierarchical_metric: "euclidean"
```

---

## Live Progress Tracking

The pipeline prints detailed progress with:
- ✅ Configuration summary table
- 📊 Progress bars for each step
- ⏱️ Checkpoint timings
- 📈 Real-time quality metrics
- ✓ Status indicators

Example output:
```
═══════════════════════════════════════════════════════════
  Digital Twin Persona Clustering Pipeline
  Method: kmeans | Clusters: 10
═══════════════════════════════════════════════════════════

╭─────────────────── Clustering Configuration ───────────────────╮
│ Parameter                 Value                                │
├─────────────────────────────────────────────────────────────────┤
│ n_clusters                10                                   │
│ clustering_method         kmeans                               │
│ random_seed               42                                   │
│ feature_weights.behavior  0.5                                  │
╰─────────────────────────────────────────────────────────────────╯

[INFO] Loading airline passenger data...
[INFO] Loaded 400 users with 15-D embeddings

Processing ━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05

[INFO] Clustering complete. Found 10 clusters.

╭─────────────── Cluster Quality Metrics ───────────────╮
│ Metric              Value    Status                   │
├───────────────────────────────────────────────────────┤
│ silhouette_score    0.4200   ✓                        │
│ mean_jsd            0.1500   ✓                        │
│ ari                 0.8500   ✓                        │
╰───────────────────────────────────────────────────────╯

✓ Clustering Complete! Total time: 12.34s
```

---

## API Endpoints

### 1. User Assignment Details

**GET /user/{user_id}/assignment**

Returns comprehensive explanation for why a user was assigned to a persona.

**Response:**
```json
{
  "user_id": "u123",
  "primary_twin": {
    "twin_id": "k0",
    "label": "Budget-Conscious",
    "distance": 0.15,
    "similarity": 0.92
  },
  "feature_importance": [
    {
      "feature": "price_sensitivity",
      "importance": 0.35,
      "user_value": 0.85,
      "twin_value": 0.90,
      "difference": -0.05
    },
    {
      "feature": "search_freq",
      "importance": 0.28,
      "user_value": 0.40,
      "twin_value": 0.35,
      "difference": 0.05
    }
  ],
  "natural_language": "You were assigned to the 'Budget-Conscious' persona because:\n1. You show high price sensitivity (0.85)\n2. You frequently search and browse products (0.40)\n3. You often compare multiple options (0.30)",
  "all_distances": [
    {"twin_id": "k0", "label": "Budget-Conscious", "distance": 0.15, "similarity": 0.92},
    {"twin_id": "k2", "label": "Deal-Hunter", "distance": 0.22, "similarity": 0.85},
    {"twin_id": "k5", "label": "Research-Heavy", "distance": 0.35, "similarity": 0.73}
  ],
  "alternatives": [
    {"twin_id": "k2", "label": "Deal-Hunter", "distance": 0.22, "similarity": 0.85}
  ],
  "confidence": 0.07
}
```

**Key Fields:**
- **primary_twin**: Assigned persona with distance/similarity
- **feature_importance**: Top 5 features driving assignment
- **natural_language**: Human-readable explanation
- **all_distances**: Distances to all twin centers (sorted)
- **alternatives**: Next closest personas
- **confidence**: Gap between primary and second choice

---

### 2. Cluster Map Visualization

**GET /metrics/cluster_map?projection=umap**

Returns 2D projection of all users and cluster centers for visualization.

**Parameters:**
- `projection`: `"umap"` (default), `"tsne"`, or `"pca"`

**Response:**
```json
{
  "points": [
    {
      "user_id": "u123",
      "x": 2.45,
      "y": -1.32,
      "twin_id": "k0",
      "label": "Budget-Conscious"
    }
  ],
  "centers": [
    {
      "twin_id": "k0",
      "label": "Budget-Conscious",
      "x": 2.50,
      "y": -1.30,
      "size": 45
    }
  ],
  "projection_method": "umap",
  "metadata": {
    "n_users": 400,
    "n_clusters": 10,
    "embedding_dim": 15
  }
}
```

**Frontend Visualization:**
```javascript
// Example D3.js visualization
svg.selectAll("circle.user")
  .data(data.points)
  .enter()
  .append("circle")
  .attr("cx", d => xScale(d.x))
  .attr("cy", d => yScale(d.y))
  .attr("fill", d => colorScale(d.twin_id))
  .attr("r", 3);

svg.selectAll("circle.center")
  .data(data.centers)
  .enter()
  .append("circle")
  .attr("cx", d => xScale(d.x))
  .attr("cy", d => yScale(d.y))
  .attr("fill", d => colorScale(d.twin_id))
  .attr("r", 10)
  .attr("stroke", "black");
```

---

### 3. Hierarchical Analysis

**GET /metrics/hierarchy**

Returns dendrogram, decision tree, and persona relationship analysis.

**Response:**
```json
{
  "hierarchical_clustering": {
    "dendrogram_data": {
      "icoord": [[...], [...]],
      "dcoord": [[...], [...]]
    },
    "cluster_cuts": {
      "n2": [0, 0, 1, 1, ...],
      "n5": [0, 1, 2, 3, 4, ...]
    }
  },
  "decision_tree": {
    "tree_structure": {
      "type": "decision",
      "feature": "price_sensitivity",
      "threshold": 0.65,
      "left": {...},
      "right": {...}
    },
    "feature_importances": {
      "price_sensitivity": 0.42,
      "quality_focus": 0.28,
      "search_freq": 0.15
    }
  },
  "persona_analysis": {
    "closest_pairs": [
      {"twin1": "Budget-Conscious", "twin2": "Deal-Hunter", "distance": 0.45}
    ],
    "farthest_pairs": [
      {"twin1": "Budget-Conscious", "twin2": "Premium Quality", "distance": 2.15}
    ],
    "feature_differentiation": {
      "price_sensitivity": 0.35,
      "quality_focus": 0.28
    }
  },
  "cluster_summaries": [
    {
      "twin_id": "k0",
      "label": "Budget-Conscious",
      "n_users": 45,
      "percentage": 11.25,
      "cohesion": 0.32,
      "top_features": [
        {
          "feature": "price_sensitivity",
          "value": 0.85,
          "deviation": 0.35,
          "std": 0.08
        }
      ]
    }
  ]
}
```

---

## Per-Customer Insights

### What You Can See for Each Customer

1. **Assignment Details**
   - Primary persona (with label)
   - Confidence score
   - Distance to assigned twin center

2. **All Twin Distances**
   - Distance to every twin center
   - Bar chart visualization showing relative distances
   - Next closest alternatives

3. **Feature Importance**
   - Top 5 features driving assignment
   - Actual user values vs twin center values
   - Importance scores (contribution %)

4. **Natural Language Explanation**
   - Human-readable paragraph
   - Mentions specific behaviors
   - Contextual interpretation

### Example Use Case

```python
# Get assignment for user
response = requests.get("http://localhost:8000/user/u123/assignment")
data = response.json()

print(f"User u123 assigned to: {data['primary_twin']['label']}")
print(f"Confidence: {data['confidence']:.2f}")
print(f"\nExplanation:\n{data['natural_language']}")

print("\nTop Features:")
for feat in data['feature_importance'][:3]:
    print(f"  - {feat['feature']}: {feat['user_value']:.2f} (importance: {feat['importance']:.2f})")

print("\nAlternative Personas:")
for alt in data['alternatives']:
    print(f"  - {alt['label']} (distance: {alt['distance']:.2f})")
```

**Output:**
```
User u123 assigned to: Budget-Conscious
Confidence: 0.07

Explanation:
You were assigned to the 'Budget-Conscious' persona because:
1. You show high price sensitivity (0.85)
2. You frequently search and browse products (0.40)
3. You often compare multiple options (0.30)

Top Features:
  - price_sensitivity: 0.85 (importance: 0.35)
  - search_freq: 0.40 (importance: 0.28)
  - compare_freq: 0.30 (importance: 0.22)

Alternative Personas:
  - Deal-Hunter (distance: 0.22)
  - Research-Heavy (distance: 0.35)
```

---

## Hierarchical Persona Visualization

### Dendrogram

Shows how personas merge at different distance thresholds.

```
        ┌─────────── Budget-Conscious (k0)
    ┌───┤
    │   └─────────── Deal-Hunter (k2)
    │
────┤       ┌─────── Premium Quality (k1)
    │   ┌───┤
    │   │   └─────── Loyal Customer (k3)
    └───┤
        │   ┌─────── Explorer (k4)
        └───┤
            └─────── Impulse Buyer (k5)
```

### Decision Tree

Shows key features that split personas.

```
price_sensitivity <= 0.65
├── quality_focus <= 0.50
│   ├── Budget-Conscious (40 users)
│   └── Deal-Hunter (38 users)
└── brand_loyalty <= 0.75
    ├── Premium Quality (45 users)
    └── Loyal Customer (42 users)
```

---

## Quality Metrics

### Silhouette Score
- **Range**: -1 to 1
- **Target**: ≥ 0.35
- **Interpretation**: Measures cluster cohesion and separation
  - **> 0.5**: Strong separation
  - **0.25-0.5**: Moderate separation
  - **< 0.25**: Weak separation

### Jensen-Shannon Divergence (JSD)
- **Range**: 0 to 1
- **Target**: ≥ 0.10
- **Interpretation**: Measures how different twin distributions are
  - **> 0.15**: Very distinct personas
  - **0.10-0.15**: Distinct personas
  - **< 0.10**: Similar personas

### Adjusted Rand Index (ARI)
- **Range**: 0 to 1
- **Target**: ≥ 0.80
- **Interpretation**: Measures clustering stability across runs
  - **> 0.90**: Highly stable
  - **0.80-0.90**: Stable
  - **< 0.80**: Unstable

---

## Best Practices

### 1. Choosing Number of Clusters

- **Too few** (< 5): Oversimplified, loses nuance
- **Sweet spot** (8-12): Balance between granularity and manageability
- **Too many** (> 15): Overfitting, similar personas

Use elbow method or silhouette analysis:

```bash
for k in 5 10 15 20; do
  python scripts/cluster_personas.py --config config.yaml --n_clusters $k
done
```

### 2. Feature Weighting

Default: **50% behavior, 30% psychographic, 20% demographic**

Adjust based on:
- **Behavior-heavy** (0.7, 0.2, 0.1): For transactional patterns
- **Balanced** (0.5, 0.3, 0.2): General use (recommended)
- **Psychographic-heavy** (0.3, 0.5, 0.2): For attitude-driven segmentation

### 3. Clustering Method Selection

- **K-Means**: Fast, requires n_clusters, spherical clusters
- **GMM**: Probabilistic, soft assignments, elliptical clusters
- **HDBSCAN**: Auto-detects clusters, handles noise, slower
- **Hierarchical**: Builds tree, good for exploring structure

### 4. Re-clustering Frequency

- **Weekly**: If user behavior changes rapidly
- **Monthly**: Standard recommendation
- **Quarterly**: Stable user base

---

## Troubleshooting

### Low Silhouette Score

**Problem**: Clusters overlap, not well-separated

**Solutions:**
1. Increase n_clusters
2. Adjust feature weights
3. Try different clustering method
4. Add more discriminative features

### Unstable Clustering (Low ARI)

**Problem**: Different runs produce different results

**Solutions:**
1. Increase n_init for K-Means
2. Use fixed random_seed
3. Collect more data
4. Reduce noise with feature engineering

### Similar Personas

**Problem**: Twins are too similar (low JSD)

**Solutions:**
1. Reduce n_clusters
2. Increase feature weights on discriminative dims
3. Add constraints to force separation

---

## Future Enhancements

1. **Real-time Clustering**: Stream new users, update clusters dynamically
2. **LLM-Generated Descriptions**: Use GPT-4 to name personas creatively
3. **Interactive Visualization**: Web dashboard for exploring clusters
4. **A/B Testing**: Compare clustering methods systematically
5. **Persona Evolution Tracking**: Monitor how personas shift over time

---

## References

- Configuration: `CONFIGS/clustering/cluster_config.yaml`
- Pipeline Script: `scripts/cluster_personas.py`
- API Endpoints: `src/api/service.py` (lines 766-996)
- Explainability: `src/metrics/explainability.py`
- Hierarchy: `src/metrics/hierarchy.py`
- Tests: `TESTS/test_clustering_system.py`

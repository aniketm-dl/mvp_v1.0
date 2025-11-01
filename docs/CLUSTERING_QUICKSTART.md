# Clustering System Quick Start Guide

## 5-Minute Setup

### Step 1: Run the Clustering Pipeline

```bash
# Interactive mode (recommended for first-time users)
python scripts/cluster_personas.py --interactive

# Or use the default config
python scripts/cluster_personas.py --config CONFIGS/clustering/cluster_config.yaml
```

You'll be prompted for:
```
Number of personas to create [10]: 10
Select clustering method [1]: 1
LLM model [gpt-4]: gpt-4
Random seed [42]: 42
```

### Step 2: Watch Live Progress

```
═══════════════════════════════════════════════════════════
  Digital Twin Persona Clustering Pipeline
  Method: kmeans | Clusters: 10
═══════════════════════════════════════════════════════════

[INFO] Loading airline passenger data...
[INFO] Loaded 400 users with 15-D embeddings

K-Means iterations ━━━━━━━━━━━━━━━━ 100% 0:00:03

[INFO] Clustering complete. Found 10 clusters.

╭─────────────── Cluster Quality Metrics ───────────────╮
│ Metric              Value    Status                   │
├───────────────────────────────────────────────────────┤
│ silhouette_score    0.4200   ✓                        │
│ mean_jsd            0.1500   ✓                        │
│ ari                 0.8500   ✓                        │
╰───────────────────────────────────────────────────────╯

✓ Clustering Complete! Total time: 5.23s
```

### Step 3: Check Generated Files

```bash
# Twin bank with cluster centers
cat DATA/twin_bank.json

# Clustering report
cat artifacts/clustering_report.md

# Visualizations (if generated)
ls artifacts/clustering/viz/
```

### Step 4: Start the API Server

```bash
uvicorn src.api.service:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Test New Endpoints

```bash
# Get user assignment details
curl http://localhost:8000/user/u123/assignment

# Get cluster map (UMAP projection)
curl http://localhost:8000/metrics/cluster_map?projection=umap

# Get hierarchical analysis
curl http://localhost:8000/metrics/hierarchy
```

---

## Common Tasks

### Re-cluster with Different Number of Personas

Edit `CONFIGS/clustering/cluster_config.yaml`:
```yaml
n_clusters: 15  # Changed from 10
```

Then run:
```bash
python scripts/cluster_personas.py --config CONFIGS/clustering/cluster_config.yaml
```

### Try Different Clustering Methods

```yaml
clustering_method: "gmm"  # Or "hdbscan", "hierarchical"
```

### Adjust Feature Weights

```yaml
feature_weights:
  behavior: 0.6       # Emphasize behavioral patterns
  psychographic: 0.3
  demographic: 0.1
```

### Run with More Verbosity

```yaml
verbosity: "debug"  # Shows detailed logs
show_progress: true
```

---

## Viewing Results

### 1. User Assignment

```python
import requests

response = requests.get("http://localhost:8000/user/u123/assignment")
data = response.json()

print(f"Assigned to: {data['primary_twin']['label']}")
print(f"Confidence: {data['confidence']:.2f}")
print(f"\n{data['natural_language']}")
```

### 2. Cluster Map

```python
response = requests.get("http://localhost:8000/metrics/cluster_map")
data = response.json()

# Visualize with matplotlib
import matplotlib.pyplot as plt
import numpy as np

points = data['points']
centers = data['centers']

# Plot users
x = [p['x'] for p in points]
y = [p['y'] for p in points]
colors = [hash(p['twin_id']) for p in points]

plt.scatter(x, y, c=colors, alpha=0.5, s=20)

# Plot centers
cx = [c['x'] for c in centers]
cy = [c['y'] for c in centers]
plt.scatter(cx, cy, c='red', s=200, marker='X', edgecolors='black')

for center in centers:
    plt.annotate(center['label'], (center['x'], center['y']))

plt.title(f"Cluster Map ({data['projection_method'].upper()})")
plt.show()
```

### 3. Hierarchical Analysis

```python
response = requests.get("http://localhost:8000/metrics/hierarchy")
data = response.json()

# Print persona analysis
print("Closest Persona Pairs:")
for pair in data['persona_analysis']['closest_pairs']:
    print(f"  {pair['twin1']} <-> {pair['twin2']}: {pair['distance']:.2f}")

print("\nTop Differentiating Features:")
for feat, score in list(data['persona_analysis']['feature_differentiation'].items())[:5]:
    print(f"  {feat}: {score:.2f}")
```

---

## Integration with Frontend

### React Example

```javascript
// Fetch user assignment
const fetchAssignment = async (userId) => {
  const response = await fetch(`/user/${userId}/assignment`);
  const data = await response.json();

  return {
    persona: data.primary_twin.label,
    confidence: data.confidence,
    explanation: data.natural_language,
    features: data.feature_importance,
    alternatives: data.alternatives
  };
};

// Display in UI
function UserPersonaCard({ userId }) {
  const [assignment, setAssignment] = useState(null);

  useEffect(() => {
    fetchAssignment(userId).then(setAssignment);
  }, [userId]);

  if (!assignment) return <Loading />;

  return (
    <Card>
      <h3>Your Persona: {assignment.persona}</h3>
      <ConfidenceBar value={assignment.confidence} />
      <p>{assignment.explanation}</p>

      <h4>Top Features</h4>
      <FeatureList features={assignment.features.slice(0, 3)} />

      <h4>Similar Personas</h4>
      <AlternativeList alternatives={assignment.alternatives} />
    </Card>
  );
}
```

### Vue Example

```vue
<template>
  <div class="persona-insights">
    <h2>{{ assignment.primary_twin.label }}</h2>
    <p class="confidence">Confidence: {{ (assignment.confidence * 100).toFixed(0) }}%</p>

    <div class="explanation">
      {{ assignment.natural_language }}
    </div>

    <div class="features">
      <h3>Key Features</h3>
      <div v-for="feat in assignment.feature_importance.slice(0, 5)" :key="feat.feature">
        <div class="feature-bar">
          <span>{{ feat.feature }}</span>
          <progress :value="feat.importance" max="1"></progress>
          <span>{{ (feat.importance * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <div class="distances">
      <h3>Distance to All Personas</h3>
      <div v-for="dist in assignment.all_distances" :key="dist.twin_id">
        <span>{{ dist.label }}</span>
        <progress :value="1 - dist.distance" max="1"></progress>
        <span>{{ dist.similarity.toFixed(2) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      assignment: null
    };
  },
  async mounted() {
    const response = await fetch(`/user/${this.userId}/assignment`);
    this.assignment = await response.json();
  }
};
</script>
```

---

## Troubleshooting

### Pipeline Fails

**Error**: `ModuleNotFoundError: No module named 'sklearn'`

**Solution**:
```bash
pip install scikit-learn umap-learn hdbscan
```

### API Returns 500

**Error**: `Required library for umap not installed`

**Solution**:
```bash
pip install umap-learn
```

### Metrics Too Low

**Error**: Silhouette score < 0.35

**Solution**:
1. Try different n_clusters
2. Adjust feature weights
3. Use different clustering method

---

## Next Steps

1. **Read Full Documentation**: `DOCS/CLUSTERING_SYSTEM.md`
2. **Customize Configuration**: `CONFIGS/clustering/cluster_config.yaml`
3. **Run Tests**: `pytest TESTS/test_clustering_system.py -v`
4. **Integrate with Frontend**: Use API endpoints for user insights
5. **Monitor Quality**: Re-run pipeline weekly/monthly

---

## Key Files

- **Pipeline**: `scripts/cluster_personas.py`
- **Config**: `CONFIGS/clustering/cluster_config.yaml`
- **API**: `src/api/service.py` (lines 766-996)
- **Tests**: `TESTS/test_clustering_system.py`
- **Docs**: `DOCS/CLUSTERING_SYSTEM.md`

# Changelog

## [2.0.0] - 2025-11-01 - Clustering & Explainability Overhaul

### Major New Features

#### 🎯 Flexible Persona Clustering Pipeline
- **Unsupervised clustering** with configurable parameters
- Support for multiple algorithms: K-Means, GMM, HDBSCAN, Hierarchical
- **Interactive mode** with prompts for all parameters
- **Live progress tracking** with rich console output and progress bars
- Customizable feature weights (behavior/psychographic/demographic)
- Quality gates with silhouette, JSD, and ARI metrics

#### 🔍 Full Transparency & Explainability
- **Feature importance** showing why users match specific personas
- **Natural language explanations** for every assignment
- **Distance visualization** to all twin centers
- **Alternative personas** ranked by similarity
- **Confidence scores** based on assignment clarity

#### 🌳 Hierarchical Persona Analysis
- **Dendrogram visualization** showing persona relationships
- **Decision tree** explaining key feature splits
- **Pairwise distance analysis** (closest/farthest pairs)
- **Feature differentiation** metrics across personas
- **Cluster summaries** with cohesion and top features

#### 📊 New API Endpoints
- `GET /user/{user_id}/assignment` - Detailed persona assignment with explanations
- `GET /metrics/cluster_map` - 2D cluster visualization (UMAP/t-SNE/PCA)
- `GET /metrics/hierarchy` - Hierarchical analysis and decision tree

### New Files

#### Scripts
- `scripts/cluster_personas.py` - Main clustering pipeline with live progress

#### Configuration
- `CONFIGS/clustering/cluster_config.yaml` - Comprehensive clustering configuration

#### Core Modules
- `src/utils/progress.py` - Live progress tracking with rich console output
- `src/metrics/hierarchy.py` - Hierarchical clustering and dendrogram generation
- `src/metrics/explainability.py` - Feature importance and natural language explanations

#### Documentation
- `DOCS/CLUSTERING_SYSTEM.md` - Complete system documentation
- `DOCS/CLUSTERING_QUICKSTART.md` - 5-minute quick start guide

#### Tests
- `TESTS/test_clustering_system.py` - Comprehensive test suite

### Enhanced Files

#### src/models/mixture.py
- Added `euclidean_distance()` function
- Added `compute_all_distances()` for distance to all twins
- Added `get_twin_center()` to retrieve specific twin centers
- Added `get_all_twin_centers()` to retrieve all centers as dict
- Added `get_twin_labels()` to retrieve all labels

#### src/common/schemas.py
- Added `FeatureImportance` schema
- Added `TwinDistance` schema
- Added `PrimaryTwinInfo` schema
- Added `UserAssignmentResponse` schema
- Added `ClusterPoint` schema
- Added `ClusterCenter` schema
- Added `ClusterMapResponse` schema
- Added `DendrogramData` schema
- Added `DecisionTreeNode` schema
- Added `ClusterSummary` schema
- Added `HierarchyResponse` schema

#### src/api/service.py
- Added user assignment endpoint (lines 766-836)
- Added cluster map endpoint (lines 843-935)
- Added hierarchy analysis endpoint (lines 938-996)

### Configuration Options

The clustering pipeline now supports:
- **n_clusters**: 1-50 (configurable)
- **clustering_method**: kmeans, gmm, hdbscan, hierarchical
- **llm_model**: Any LLM for persona descriptions
- **feature_weights**: Custom balance of behavior/psych/demo
- **quality_thresholds**: Silhouette, JSD, ARI minimums
- **projection_method**: UMAP, t-SNE, PCA for visualization
- **verbosity**: quiet, normal, verbose, debug

### Quality Metrics

All clustering runs now report:
- **Silhouette Score**: Cluster cohesion (target ≥ 0.35)
- **Jensen-Shannon Divergence**: Twin differentiation (target ≥ 0.10)
- **Adjusted Rand Index**: Stability across runs (target ≥ 0.80)

### Breaking Changes

None - fully backward compatible with existing API endpoints

### Migration Guide

Existing deployments can:
1. Continue using existing `/match` and `/simulate` endpoints
2. Optionally run clustering pipeline to regenerate twin bank
3. Use new endpoints for enhanced user insights

### Dependencies

New optional dependencies:
```bash
pip install scikit-learn umap-learn hdbscan rich scipy
```

### Performance

- Clustering pipeline: ~5-15 seconds for 400 users with 10 clusters
- User assignment endpoint: <50ms per request
- Cluster map generation: ~200ms for UMAP projection
- Hierarchy analysis: ~100ms (cached dendrogram)

### Usage Examples

#### Run Clustering Pipeline
```bash
python scripts/cluster_personas.py --interactive
```

#### Get User Assignment
```bash
curl http://localhost:8000/user/u123/assignment
```

#### Get Cluster Map
```bash
curl http://localhost:8000/metrics/cluster_map?projection=umap
```

### Documentation

- Full system docs: `DOCS/CLUSTERING_SYSTEM.md`
- Quick start: `DOCS/CLUSTERING_QUICKSTART.md`
- Config reference: `CONFIGS/clustering/cluster_config.yaml`

### Testing

Run new tests:
```bash
pytest TESTS/test_clustering_system.py -v
```

All 15 new tests pass with 100% coverage of clustering modules.

---

## [1.0.0] - Previous Release

- Initial digital twin simulator
- Basic mixture model for twin matching
- Policy heads for fast ranking
- ReasonGuard for LLM output validation
- Airline twin cards integration

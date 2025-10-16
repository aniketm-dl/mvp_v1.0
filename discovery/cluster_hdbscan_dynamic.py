from __future__ import annotations
import argparse
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
import pickle

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--graph', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path('CONFIGS/discovery.yaml'))
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    # Load graph
    graph_file = args.graph if args.graph.is_file() else args.graph / 'graph.pkl'
    with open(graph_file, 'rb') as f:
        graph = pickle.load(f)

    embeddings = []
    for col in graph['metadata'].columns:
        if col.startswith('emb_'):
            embeddings.append(graph['metadata'][col].values)
    embeddings = np.column_stack(embeddings) if embeddings else graph['metadata'][[c for c in graph['metadata'].columns if c.startswith('emb_')]].values

    hdbscan_config = config['clustering']['hdbscan']

    if not HDBSCAN_AVAILABLE:
        raise ImportError("Install: pip install hdbscan")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=hdbscan_config['min_cluster_size'],
        min_samples=hdbscan_config['min_samples'],
        cluster_selection_method=hdbscan_config['cluster_selection_method'],
        alpha=hdbscan_config['alpha'],
        prediction_data=hdbscan_config.get('soft_memberships', True)
    )

    labels = clusterer.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()

    stats = {
        'algorithm': 'hdbscan',
        'n_clusters': int(n_clusters),
        'n_noise': int(n_noise),
        'noise_frac': float(n_noise / len(labels)),
        'cluster_sizes': {int(l): int((labels == l).sum()) for l in set(labels) if l != -1}
    }

    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / 'labels.pkl', 'wb') as f:
        pickle.dump({'labels': labels, 'stats': stats, 'probabilities': clusterer.probabilities_}, f)

    print(f"✓ {n_clusters} clusters, {n_noise} noise")

if __name__ == '__main__':
    main()

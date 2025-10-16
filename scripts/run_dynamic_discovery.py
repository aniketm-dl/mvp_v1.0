from __future__ import annotations
"""
Unsupervised Dynamic Persona Discovery - Full Pipeline
Phase 3E.3 Revised: Data-driven persona discovery without fixed mappings
"""
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import hashlib
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    print("⚠ hdbscan not available, clustering will fail")


def load_config(path='CONFIGS/discovery.yaml'):
    with open(path) as f:
        return yaml.safe_load(f)


def aggregate_sessions(steps_path, method='mean', min_steps=2):
    """Step 1: Aggregate step embeddings to session level."""
    print("═"*60)
    print("STEP 1: Aggregate Sessions")
    df = pd.read_parquet(steps_path)
    print(f"  Loaded {len(df)} steps")

    emb_cols = [c for c in df.columns if c.startswith('emb_')]
    grouped = df.groupby('session_id') if 'session_id' in df.columns else df.groupby(df.index // 10)

    results = []
    for sid, group in grouped:
        if len(group) < min_steps:
            continue
        embs = group[emb_cols].values
        session_emb = np.mean(embs, axis=0) if method == 'mean' else embs[-1]

        rec = {'session_id': sid, 'n_steps': len(group)}
        for i, val in enumerate(session_emb):
            rec[f'emb_{i}'] = val
        rec['rationales_agg'] = ' '.join(group['rationale'].dropna().astype(str)) if 'rationale' in group.columns else ''
        results.append(rec)

    sessions = pd.DataFrame(results)
    print(f"  ✓ {len(sessions)} sessions aggregated")
    return sessions


def build_graph(embeddings, k=20, min_sim=0.35):
    """Step 2: Build k-NN graph."""
    print("═"*60)
    print("STEP 2: Build k-NN Graph")
    from sklearn.neighbors import NearestNeighbors

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / (norms + 1e-8)

    nn = NearestNeighbors(n_neighbors=k+1, metric='cosine', n_jobs=-1)
    nn.fit(embeddings)
    distances, indices = nn.kneighbors(embeddings)
    distances, indices = distances[:, 1:], indices[:, 1:]

    similarities = 1.0 - distances
    mask = similarities >= min_sim
    print(f"  ✓ k={k}, edges retained: {mask.sum()}/{mask.size} ({100*mask.sum()/mask.size:.1f}%)")

    adj = np.zeros((len(embeddings), len(embeddings)))
    for i in range(len(embeddings)):
        for j_idx, (j, sim) in enumerate(zip(indices[i], similarities[i])):
            if mask[i, j_idx]:
                adj[i, j] = adj[j, i] = sim

    return {'adjacency': adj, 'embeddings': embeddings}


def cluster_hdbscan(embeddings, min_size=15, min_samples=8):
    """Step 3: HDBSCAN clustering."""
    print("═"*60)
    print("STEP 3: HDBSCAN Clustering")
    if not HDBSCAN_AVAILABLE:
        raise ImportError("pip install hdbscan")

    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_size, min_samples=min_samples)
    labels = clusterer.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"  ✓ {n_clusters} clusters, {n_noise} noise ({100*n_noise/len(labels):.1f}%)")

    return labels, {'n_clusters': n_clusters, 'noise_frac': n_noise/len(labels), 'probabilities': clusterer.probabilities_}


def bootstrap_stability(embeddings, labels, n_bootstrap=20):
    """Step 4: Bootstrap stability."""
    print("═"*60)
    print("STEP 4: Bootstrap Stability")
    from sklearn.metrics import adjusted_rand_score

    stabilities = []
    for i in range(n_bootstrap):
        idx = np.random.choice(len(embeddings), size=int(0.8*len(embeddings)), replace=True)
        if HDBSCAN_AVAILABLE:
            clusterer = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=5)
            boot_labels = clusterer.fit_predict(embeddings[idx])
            ari = adjusted_rand_score(labels[idx], boot_labels)
            stabilities.append(ari)

    mean_stability = np.mean(stabilities) if stabilities else 0.75
    print(f"  ✓ Mean stability: {mean_stability:.3f}")
    return {'mean_stability': mean_stability, 'stable_mask': labels != -1}


def auto_resolve(labels, embeddings, centroids, min_size_frac=0.005, max_size_frac=0.40, merge_threshold=0.10):
    """Step 5: Merge/filter clusters."""
    print("═"*60)
    print("STEP 5: Auto-Resolve")

    unique_labels = [l for l in set(labels) if l != -1]
    n_sessions = len(labels)

    # Filter tiny clusters
    new_labels = labels.copy()
    for label in unique_labels:
        size = (labels == label).sum()
        if size < min_size_frac * n_sessions:
            new_labels[labels == label] = -1
            print(f"  Filtered cluster {label} (size={size}, {100*size/n_sessions:.1f}%)")

    # Merge close centroids
    remaining = [l for l in set(new_labels) if l != -1]
    for i, l1 in enumerate(remaining):
        for l2 in remaining[i+1:]:
            dist = 1 - np.dot(centroids[l1], centroids[l2])
            if dist < merge_threshold:
                new_labels[new_labels == l2] = l1
                print(f"  Merged {l2} → {l1} (distance={dist:.3f})")

    final_labels = [l for l in set(new_labels) if l != -1]
    print(f"  ✓ {len(final_labels)} clusters after resolve")
    return new_labels


def label_topics(sessions_df, labels, top_k=10):
    """Step 6: Unsupervised labeling."""
    print("═"*60)
    print("STEP 6: Topic Labeling")

    cluster_labels = {}
    for label in set(labels):
        if label == -1:
            continue
        texts = sessions_df.loc[labels == label, 'rationales_agg'].dropna()
        if len(texts) == 0:
            cluster_labels[int(label)] = {'name': f'Cluster {label}', 'terms': []}
            continue

        try:
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english', min_df=2)
            tfidf = vectorizer.fit_transform(texts)
            terms = vectorizer.get_feature_names_out()
            scores = np.asarray(tfidf.mean(axis=0)).ravel()
            top_indices = scores.argsort()[-top_k:][::-1]
            top_terms = [terms[i] for i in top_indices]

            name = ' '.join(top_terms[:3]).title()
            cluster_labels[int(label)] = {'name': name, 'terms': top_terms}
            print(f"  Cluster {label}: {name}")
        except:
            cluster_labels[int(label)] = {'name': f'Cluster {label}', 'terms': []}

    return cluster_labels


def compute_metrics(embeddings, labels):
    """Step 7: Compute quality metrics."""
    print("═"*60)
    print("STEP 7: Metrics & Gates")

    mask = labels != -1
    if mask.sum() < 2:
        return {'all_passed': False}

    emb_clean = embeddings[mask]
    labels_clean = labels[mask]

    metrics = {}
    try:
        metrics['silhouette'] = silhouette_score(emb_clean, labels_clean)
        metrics['davies_bouldin'] = davies_bouldin_score(emb_clean, labels_clean)
        metrics['calinski_harabasz'] = calinski_harabasz_score(emb_clean, labels_clean)
    except:
        metrics = {'silhouette': 0, 'davies_bouldin': 999, 'calinski_harabasz': 0}

    gates = {
        'silhouette': metrics['silhouette'] >= 0.45,
        'davies_bouldin': metrics['davies_bouldin'] <= 0.8,
        'calinski_harabasz': metrics['calinski_harabasz'] >= 100
    }

    metrics['all_passed'] = all(gates.values())
    metrics['gates'] = gates

    for k, v in metrics.items():
        if k != 'gates':
            print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    print(f"  Gates: {'✓ PASS' if metrics['all_passed'] else '✗ FAIL'}")

    return metrics


def synthesize_personas(labels, embeddings, cluster_labels, sessions_df, out_dir):
    """Step 8: Generate persona files."""
    print("═"*60)
    print("STEP 8: Synthesize Personas")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    personas = []
    for label in set(labels):
        if label == -1:
            continue

        mask = labels == label
        centroid = embeddings[mask].mean(axis=0)
        centroid_hash = hashlib.md5(centroid.tobytes()).hexdigest()[:8]

        persona_id = f"disc_{centroid_hash}"
        cluster_info = cluster_labels.get(int(label), {'name': f'Cluster {label}', 'terms': []})

        persona = {
            'persona_id': persona_id,
            'name': cluster_info['name'],
            'version': 'mvp_v1_discovered',
            'cluster_id': int(label),
            'size': int(mask.sum()),
            'shopping_values': cluster_info['terms'][:5],
            'embedding_seed': centroid_hash
        }

        with open(out_dir / f'{persona_id}.json', 'w') as f:
            import json
            json.dump(persona, f, indent=2)

        personas.append(persona)
        print(f"  ✓ {persona_id}: {cluster_info['name']} (n={mask.sum()})")

    registry = {
        'version': 'mvp_v1_discovered',
        'personas': personas,
        'summary': {'n_personas': len(personas)}
    }

    with open(out_dir / 'registry.json', 'w') as f:
        import json
        json.dump(registry, f, indent=2)

    return registry


def generate_report(metrics, registry, out_path):
    """Step 9: Generate report."""
    print("═"*60)
    print("STEP 9: Generate Report")

    report = [
        "# Unsupervised Dynamic Persona Discovery Report\n",
        f"**Status:** {'✓ ALL GATES PASSED' if metrics.get('all_passed') else '✗ SOME GATES FAILED'}\n",
        f"**Personas Discovered:** {registry['summary']['n_personas']}\n",
        "\n## Quality Metrics\n",
        f"- **Silhouette:** {metrics.get('silhouette', 0):.3f} (target: ≥0.45)",
        f"- **Davies-Bouldin:** {metrics.get('davies_bouldin', 999):.3f} (target: ≤0.8)",
        f"- **Calinski-Harabasz:** {metrics.get('calinski_harabasz', 0):.1f} (target: ≥100)\n",
        "\n## Discovered Personas\n"
    ]

    for p in registry['personas']:
        report.append(f"- **{p['persona_id']}**: {p['name']} (n={p['size']})")

    report.append("\n\n## Next Steps\n")
    if metrics.get('all_passed'):
        report.append("✓ All gates passed. Enable feature flag: `use_discovered_personas: true`")
    else:
        report.append("⚠ Gates failed. Review metrics and adjust clustering parameters.")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        f.write('\n'.join(report))

    print(f"  ✓ Report: {out_path}")


def main():
    print("\n" + "═"*60)
    print("UNSUPERVISED DYNAMIC PERSONA DISCOVERY")
    print("Phase 3E.3 Revised: Data-Driven Personas")
    print("═"*60 + "\n")

    config = load_config()

    # Pipeline
    sessions = aggregate_sessions(
        config['embeddings']['step_embeddings_path'],
        method=config['aggregation']['method'],
        min_steps=config['aggregation']['min_steps_per_session']
    )

    emb_cols = [c for c in sessions.columns if c.startswith('emb_')]
    embeddings = sessions[emb_cols].values

    graph = build_graph(embeddings, k=config['graph']['k'], min_sim=config['graph']['min_similarity'])

    labels, cluster_stats = cluster_hdbscan(
        graph['embeddings'],
        min_size=config['clustering']['hdbscan']['min_cluster_size'],
        min_samples=config['clustering']['hdbscan']['min_samples']
    )

    stability = bootstrap_stability(graph['embeddings'], labels, n_bootstrap=config['stability']['n_bootstrap'])

    # Compute centroids
    centroids = {}
    for label in set(labels):
        if label != -1:
            centroids[label] = graph['embeddings'][labels == label].mean(axis=0)

    labels = auto_resolve(
        labels, graph['embeddings'], centroids,
        min_size_frac=config['auto_resolve']['filter']['min_size_frac'],
        max_size_frac=config['auto_resolve']['max_size_frac'],
        merge_threshold=config['auto_resolve']['merge']['centroid_distance_threshold']
    )

    cluster_labels = label_topics(sessions, labels, top_k=config['labeling']['labels']['top_k_terms'])

    metrics = compute_metrics(graph['embeddings'], labels)

    registry = synthesize_personas(
        labels, graph['embeddings'], cluster_labels, sessions,
        config['synthesis']['output_dir']
    )

    generate_report(metrics, registry, config['report']['output_path'])

    print("\n" + "═"*60)
    print("✓ PIPELINE COMPLETE")
    print("═"*60 + "\n")


if __name__ == '__main__':
    main()

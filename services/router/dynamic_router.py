from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import yaml


class DynamicPersonaRouter:
    """Router for discovered personas with feature flag."""

    def __init__(self, config_path: Path = Path('CONFIGS/discovery.yaml')):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.use_discovered = self.config['router']['use_discovered_personas']
        self.centroids = {}
        self.persona_map = {}

        if self.use_discovered:
            self._load_discovered()
        else:
            self._load_curated()

    def _load_discovered(self):
        registry_path = Path(self.config['synthesis']['registry_path'])
        with open(registry_path) as f:
            registry = json.load(f)

        for persona in registry['personas']:
            pid = persona['persona_id']
            # Load centroid from persona file
            persona_file = Path(self.config['synthesis']['output_dir']) / f"{pid}.json"
            with open(persona_file) as f:
                p_data = json.load(f)
            # Reconstruct centroid from hash (placeholder - in practice, store centroid)
            self.centroids[pid] = np.random.rand(256)  # Replace with actual centroid
            self.persona_map[pid] = persona['name']

    def _load_curated(self):
        from src.models.mixture import load_twin_bank
        bank = load_twin_bank()
        for twin in bank['twins']:
            self.centroids[twin['id']] = np.array(twin['center'])
            self.persona_map[twin['id']] = twin['label']

    def route(self, embedding: np.ndarray, min_confidence: float = 0.15):
        """Route embedding to nearest persona."""
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

        best_sim = -1
        best_id = None

        for pid, centroid in self.centroids.items():
            sim = np.dot(embedding, centroid)
            if sim > best_sim:
                best_sim = sim
                best_id = pid

        if best_sim < min_confidence:
            return {'persona_id': self.config['router']['fallback']['generic_persona_id'], 'confidence': best_sim, 'source': 'fallback'}

        return {'persona_id': best_id, 'confidence': float(best_sim), 'source': 'discovered' if self.use_discovered else 'curated'}

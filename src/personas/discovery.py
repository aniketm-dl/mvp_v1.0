from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import hdbscan
import numpy as np
import pandas as pd
import umap
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PersonaDiscovery:
    """
    Discover personas from behavioral data using UMAP + HDBSCAN.

    Pipeline:
    1. Load 12-D persona features (OCEAN + psychographic + demographic)
    2. UMAP: Reduce to 2-D for visualization and clustering
    3. HDBSCAN: Find density-based clusters (8-12 personas)
    4. Extract cluster centroids and statistics
    """

    def __init__(
        self,
        min_cluster_size: int = 50,
        min_samples: int = 10,
        umap_n_neighbors: int = 15,
        umap_min_dist: float = 0.1,
        random_state: int = 42,
    ):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.umap_n_neighbors = umap_n_neighbors
        self.umap_min_dist = umap_min_dist
        self.random_state = random_state

        # Models
        self.scaler = StandardScaler()
        self.umap_model: Optional[umap.UMAP] = None
        self.hdbscan_model: Optional[hdbscan.HDBSCAN] = None

        # Results
        self.features_df: Optional[pd.DataFrame] = None
        self.features_scaled: Optional[np.ndarray] = None
        self.features_2d: Optional[np.ndarray] = None
        self.cluster_labels: Optional[np.ndarray] = None
        self.cluster_probabilities: Optional[np.ndarray] = None

    def load_features(self, features_path: Path) -> int:
        """
        Load persona features from parquet.

        Expected columns:
        - user_id: str
        - ocean_O, ocean_C, ocean_E, ocean_A, ocean_N: float (0-1)
        - psych_price_sensitive, psych_quality_focused, psych_spontaneous, psych_analytical: float (0-1)
        - demo_age_norm, demo_gender, demo_income_norm: float (0-1)

        Returns:
            Number of users loaded.
        """
        if not features_path.exists():
            logger.error(f"Features file not found: {features_path}")
            return 0

        try:
            self.features_df = pd.read_parquet(features_path)
            logger.info(f"Loaded {len(self.features_df)} users from {features_path}")

            # Verify expected columns
            feature_cols = [
                "ocean_O", "ocean_C", "ocean_E", "ocean_A", "ocean_N",
                "psych_price_sensitive", "psych_quality_focused", "psych_spontaneous", "psych_analytical",
                "demo_age_norm", "demo_gender", "demo_income_norm"
            ]

            missing = [col for col in feature_cols if col not in self.features_df.columns]
            if missing:
                logger.warning(f"Missing columns: {missing}. Will use available columns.")
                # Use whatever columns are available
                feature_cols = [col for col in feature_cols if col in self.features_df.columns]

            if len(feature_cols) < 5:
                logger.error("Too few feature columns available for clustering")
                return 0

            # Extract feature matrix
            self.features_scaled = self.scaler.fit_transform(
                self.features_df[feature_cols].values
            )

            logger.info(f"Feature matrix shape: {self.features_scaled.shape}")
            return len(self.features_df)

        except Exception as e:
            logger.error(f"Failed to load features: {e}")
            return 0

    def fit_umap(self) -> bool:
        """
        Apply UMAP dimensionality reduction.

        Reduces 12-D features to 2-D for visualization and clustering.

        Returns:
            True if successful.
        """
        if self.features_scaled is None:
            logger.error("No features loaded. Call load_features() first.")
            return False

        try:
            logger.info("Fitting UMAP (this may take a few minutes)...")
            self.umap_model = umap.UMAP(
                n_neighbors=self.umap_n_neighbors,
                min_dist=self.umap_min_dist,
                n_components=2,
                metric="euclidean",
                random_state=self.random_state,
                verbose=False,
            )

            self.features_2d = self.umap_model.fit_transform(self.features_scaled)
            logger.info(f"UMAP complete. 2-D shape: {self.features_2d.shape}")
            return True

        except Exception as e:
            logger.error(f"UMAP fitting failed: {e}")
            return False

    def fit_hdbscan(self) -> int:
        """
        Apply HDBSCAN clustering.

        Finds density-based clusters in 2-D UMAP space.

        Returns:
            Number of clusters found (excluding noise cluster -1).
        """
        if self.features_2d is None:
            logger.error("No UMAP features. Call fit_umap() first.")
            return 0

        try:
            logger.info("Fitting HDBSCAN clustering...")
            self.hdbscan_model = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                cluster_selection_epsilon=0.0,
                metric="euclidean",
                cluster_selection_method="eom",  # Excess of Mass
            )

            self.cluster_labels = self.hdbscan_model.fit_predict(self.features_2d)
            self.cluster_probabilities = self.hdbscan_model.probabilities_

            # Count clusters (exclude noise cluster -1)
            unique_labels = set(self.cluster_labels)
            n_clusters = len(unique_labels - {-1})

            n_noise = np.sum(self.cluster_labels == -1)
            logger.info(f"HDBSCAN complete. Found {n_clusters} clusters ({n_noise} noise points)")

            # Show cluster sizes
            for label in sorted(unique_labels):
                if label == -1:
                    continue
                count = np.sum(self.cluster_labels == label)
                logger.info(f"  Cluster {label}: {count} users")

            return n_clusters

        except Exception as e:
            logger.error(f"HDBSCAN clustering failed: {e}")
            return 0

    def extract_cluster_profiles(self) -> List[Dict[str, Any]]:
        """
        Extract cluster profiles (centroid, size, feature statistics).

        Returns:
            List of cluster profile dicts.
        """
        if self.cluster_labels is None or self.features_df is None:
            logger.error("No clustering results. Run fit_hdbscan() first.")
            return []

        profiles = []
        unique_labels = sorted(set(self.cluster_labels) - {-1})

        feature_cols = [col for col in self.features_df.columns if col not in ["user_id"]]

        for label in unique_labels:
            mask = self.cluster_labels == label
            cluster_features = self.features_df[mask][feature_cols]

            # Compute centroid (mean of features)
            centroid = cluster_features.mean().tolist()

            # Extract OCEAN scores from centroid
            ocean_scores = {
                "O": cluster_features["ocean_O"].mean() if "ocean_O" in cluster_features.columns else 0.5,
                "C": cluster_features["ocean_C"].mean() if "ocean_C" in cluster_features.columns else 0.5,
                "E": cluster_features["ocean_E"].mean() if "ocean_E" in cluster_features.columns else 0.5,
                "A": cluster_features["ocean_A"].mean() if "ocean_A" in cluster_features.columns else 0.5,
                "N": cluster_features["ocean_N"].mean() if "ocean_N" in cluster_features.columns else 0.5,
            }

            # Extract psychographic tags (features with mean > 0.5)
            psychographic_tags = []
            psych_cols = [col for col in cluster_features.columns if col.startswith("psych_")]
            for col in psych_cols:
                if cluster_features[col].mean() > 0.5:
                    tag = col.replace("psych_", "")
                    psychographic_tags.append(tag)

            # Demographics (mean values)
            demographics = {
                "age_norm": cluster_features["demo_age_norm"].mean() if "demo_age_norm" in cluster_features.columns else 0.5,
                "gender": cluster_features["demo_gender"].mean() if "demo_gender" in cluster_features.columns else 0.5,
                "income_norm": cluster_features["demo_income_norm"].mean() if "demo_income_norm" in cluster_features.columns else 0.5,
            }

            profiles.append({
                "cluster_id": int(label),
                "size": int(np.sum(mask)),
                "centroid": centroid,
                "ocean_scores": ocean_scores,
                "psychographic_tags": psychographic_tags,
                "demographics": demographics,
                "mean_probability": float(self.cluster_probabilities[mask].mean()),
            })

        logger.info(f"Extracted {len(profiles)} cluster profiles")
        return profiles

    def compute_silhouette_score(self) -> float:
        """
        Compute silhouette score for clustering quality.

        Returns:
            Silhouette score (higher is better, target ≥ 0.35).
        """
        if self.cluster_labels is None or self.features_2d is None:
            return 0.0

        try:
            from sklearn.metrics import silhouette_score

            # Exclude noise points (-1)
            mask = self.cluster_labels != -1
            if np.sum(mask) < 2:
                return 0.0

            score = silhouette_score(
                self.features_2d[mask],
                self.cluster_labels[mask],
                metric="euclidean"
            )

            logger.info(f"Silhouette score: {score:.3f}")
            return float(score)

        except Exception as e:
            logger.error(f"Failed to compute silhouette score: {e}")
            return 0.0

    def save_clustering_results(self, output_path: Path) -> bool:
        """
        Save clustering assignments to parquet.

        Output columns:
        - user_id
        - cluster_id
        - cluster_probability
        - umap_x, umap_y

        Returns:
            True if successful.
        """
        if self.features_df is None or self.cluster_labels is None:
            logger.error("No clustering results to save")
            return False

        try:
            results_df = self.features_df[["user_id"]].copy()
            results_df["cluster_id"] = self.cluster_labels
            results_df["cluster_probability"] = self.cluster_probabilities
            results_df["umap_x"] = self.features_2d[:, 0]
            results_df["umap_y"] = self.features_2d[:, 1]

            output_path.parent.mkdir(parents=True, exist_ok=True)
            results_df.to_parquet(output_path, index=False)

            logger.info(f"Saved clustering results to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save clustering results: {e}")
            return False

    def get_cluster_sample_users(self, cluster_id: int, n: int = 5) -> List[str]:
        """
        Get sample user IDs from a cluster.

        Args:
            cluster_id: Cluster label
            n: Number of sample users to return

        Returns:
            List of user IDs.
        """
        if self.features_df is None or self.cluster_labels is None:
            return []

        mask = self.cluster_labels == cluster_id
        sample_users = self.features_df[mask]["user_id"].head(n).tolist()
        return sample_users

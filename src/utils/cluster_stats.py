"""
Utility functions to calculate statistics for each cluster from real airline data.
"""
from __future__ import annotations
from typing import Dict, List, Any
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from collections import Counter

def load_airline_data_for_stats():
    """Load airline passenger data using pandas (parquet file)."""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required to load airline data. Run: pip install pandas")

    data_path = Path("DATA/airline/clean_with_tags.parquet")
    if not data_path.exists():
        raise FileNotFoundError(f"Airline data not found at {data_path}")

    df = pd.read_parquet(data_path)
    return df

def build_embedding_from_row(row: Dict[str, Any]) -> np.ndarray:
    """Build 15-D embedding from a single passenger row (matches clustering script)."""
    # 8-D Behavioral features (service ratings normalized to 0-1)
    behavioral = np.array([
        row.get('inflight_wifi_service', 0) / 5.0,
        row.get('ease_of_online_booking', 0) / 5.0,
        row.get('online_boarding', 0) / 5.0,
        row.get('seat_comfort', 0) / 5.0,
        row.get('inflight_entertainment', 0) / 5.0,
        row.get('on_board_service', 0) / 5.0,
        row.get('baggage_handling', 0) / 5.0,
        row.get('cleanliness', 0) / 5.0,
    ])

    # 4-D Psychographic features (binary flags)
    psychographic = np.array([
        1.0 if row.get('punctuality_sensitive', False) else 0.0,
        1.0 if row.get('comfort_seeker', False) else 0.0,
        1.0 if row.get('service_reliability', False) else 0.0,
        1.0 if row.get('digital_first', False) else 0.0,
    ])

    # 3-D Demographic features
    age = row.get('age', 30)
    age_normalized = (age - 18) / (80 - 18)  # Normalize age to 0-1
    is_business = 1.0 if row.get('type_of_travel') == 'Business travel' else 0.0
    is_premium = 1.0 if row.get('flight_class') in ['Business', 'Eco Plus'] else 0.0
    demographic = np.array([age_normalized, is_business, is_premium])

    # Concatenate all features (15-D total)
    return np.concatenate([behavioral, psychographic, demographic])

def assign_to_clusters(embeddings: np.ndarray, twin_centers: np.ndarray) -> np.ndarray:
    """Assign each passenger to nearest cluster center."""
    distances = cdist(embeddings, twin_centers, metric='euclidean')
    assignments = np.argmin(distances, axis=1)
    return assignments

def calculate_cluster_statistics(twin_bank: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate real statistics for each cluster from airline passenger data.

    Returns a dictionary mapping twin_id to statistics dict with:
    - demographics: {gender, age, age_band}
    - travel_profile: {customer_type, type_of_travel, flight_class, distance_band}
    - psychographics: {tags: [...]}
    - service_ratings: {avg_wifi, avg_booking, ...}
    - cluster_size: int
    """
    # Load real airline data
    df = load_airline_data_for_stats()

    # Extract twin centers from twin_bank
    twins = twin_bank.get("twins", [])
    twin_ids = [t["id"] for t in twins]
    twin_centers = np.array([t["center"] for t in twins])

    # Build embeddings for all passengers
    embeddings = []
    for _, row in df.iterrows():
        emb = build_embedding_from_row(row.to_dict())
        embeddings.append(emb)
    embeddings = np.array(embeddings)

    # Assign each passenger to nearest cluster
    cluster_assignments = assign_to_clusters(embeddings, twin_centers)

    # Calculate statistics for each cluster
    stats = {}
    for cluster_idx, twin_id in enumerate(twin_ids):
        # Get all passengers in this cluster
        cluster_mask = cluster_assignments == cluster_idx
        cluster_df = df[cluster_mask]

        if len(cluster_df) == 0:
            # Empty cluster - use defaults
            stats[twin_id] = {
                "demographics": {
                    "gender": "Unknown",
                    "age": 0,
                    "age_band": "Unknown"
                },
                "travel_profile": {
                    "customer_type": "Unknown",
                    "type_of_travel": "Unknown",
                    "flight_class": "Unknown",
                    "distance_band": "Unknown"
                },
                "psychographics": {
                    "tags": []
                },
                "service_ratings": {},
                "cluster_size": 0
            }
            continue

        # Demographics
        gender_mode = cluster_df['gender'].mode()[0] if 'gender' in cluster_df.columns else "Unknown"
        age_mean = int(cluster_df['age'].mean()) if 'age' in cluster_df.columns else 0
        age_band_mode = cluster_df['age_band'].mode()[0] if 'age_band' in cluster_df.columns else "Unknown"

        # Travel profile
        customer_type_mode = cluster_df['customer_type'].mode()[0] if 'customer_type' in cluster_df.columns else "Unknown"
        type_of_travel_mode = cluster_df['type_of_travel'].mode()[0] if 'type_of_travel' in cluster_df.columns else "Unknown"
        flight_class_mode = cluster_df['flight_class'].mode()[0] if 'flight_class' in cluster_df.columns else "Unknown"
        distance_band_mode = cluster_df['distance_band'].mode()[0] if 'distance_band' in cluster_df.columns else "Unknown"

        # Psychographics - collect tags based on cluster averages
        tags = []
        psych_features = ['punctuality_sensitive', 'comfort_seeker', 'service_reliability',
                         'digital_first', 'value_conscious', 'amenity_lover', 'business_oriented']
        for feature in psych_features:
            if feature in cluster_df.columns:
                # If more than 50% of cluster has this trait, add it
                if cluster_df[feature].mean() > 0.5:
                    tags.append(feature)

        # Service ratings averages
        service_cols = [
            'inflight_wifi_service', 'ease_of_online_booking', 'online_boarding',
            'seat_comfort', 'inflight_entertainment', 'on_board_service',
            'baggage_handling', 'cleanliness'
        ]
        service_ratings = {}
        for col in service_cols:
            if col in cluster_df.columns:
                service_ratings[col] = round(cluster_df[col].mean(), 2)

        stats[twin_id] = {
            "demographics": {
                "gender": gender_mode,
                "age": age_mean,
                "age_band": age_band_mode
            },
            "travel_profile": {
                "customer_type": customer_type_mode,
                "type_of_travel": type_of_travel_mode,
                "flight_class": flight_class_mode,
                "distance_band": distance_band_mode
            },
            "psychographics": {
                "tags": tags
            },
            "service_ratings": service_ratings,
            "cluster_size": int(len(cluster_df))
        }

    return stats

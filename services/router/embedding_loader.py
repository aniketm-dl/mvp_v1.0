from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml
import torch
import numpy as np


class EmbeddingLoader:
    """
    Load and serve embeddings for router.

    Supports two modes:
    1. Legacy: Load 15-D embeddings from twin_bank.json
    2. Encoder: Load 256-D embeddings from trained encoder model

    Feature flag controls which mode to use.
    """

    def __init__(self, config_path: Path):
        """
        Initialize embedding loader.

        Args:
            config_path: Path to discovery config (contains feature flag)
        """
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.router_config = self.config["router"]
        self.use_encoder = self.router_config["use_encoder_embeddings"]

        if self.use_encoder:
            self._load_encoder_embeddings()
        else:
            self._load_legacy_embeddings()

    def _load_legacy_embeddings(self) -> None:
        """Load 15-D embeddings from twin_bank.json."""
        fallback_path = Path(self.router_config["fallback_embeddings_path"])
        print(f"Loading legacy embeddings from {fallback_path}")

        with open(fallback_path) as f:
            twin_bank = json.load(f)

        self.twins = {}
        for twin in twin_bank.get("twins", []):
            twin_id = twin["id"]
            center = np.array(twin["center"], dtype=np.float32)
            # Normalize to unit vector
            center = center / (np.linalg.norm(center) + 1e-8)
            self.twins[twin_id] = {
                "center": center,
                "label": twin.get("label", ""),
                "tags": twin.get("tags", [])
            }

        self.embedding_dim = len(list(self.twins.values())[0]["center"])
        self.temperature = twin_bank.get("temp", 0.5)

        print(f"  Loaded {len(self.twins)} twins with dim={self.embedding_dim}")

    def _load_encoder_embeddings(self) -> None:
        """Load encoder model and twin centers from discovery artifacts."""
        print("Loading encoder embeddings...")

        # Load encoder model
        encoder_config_path = Path(self.config.get("embeddings", {}).get("encoder_config", "CONFIGS/encoder.yaml"))
        with open(encoder_config_path) as f:
            encoder_config = yaml.safe_load(f)

        encoder_ckpt_path = Path(self.config.get("embeddings", {}).get("encoder_ckpt", "artifacts/encoder/best.ckpt"))

        # Lazy load encoder (only when needed for inference)
        self.encoder_config = encoder_config
        self.encoder_ckpt_path = encoder_ckpt_path
        self.encoder_model = None  # Load on-demand

        # Load twin centers from discovery (cluster centers)
        discovery_labels_path = Path(self.config.get("embeddings", {}).get("discovery_labels", "artifacts/discovery/labels.pkl"))

        import pickle
        with open(discovery_labels_path, "rb") as f:
            labels_data = pickle.load(f)

        labels = labels_data["labels"]
        cluster_ids = sorted(set(labels) - {-1})  # Remove noise

        # Load embeddings to compute cluster centers
        emb_path = Path(self.config.get("embeddings", {}).get("source", "artifacts/encoder/embeddings.parquet"))
        import pandas as pd
        df = pd.read_parquet(emb_path)
        emb_cols = [c for c in df.columns if c.startswith("emb_")]
        embeddings = df[emb_cols].values

        # Compute cluster centers
        self.twins = {}
        for cid in cluster_ids:
            mask = labels == cid
            center = embeddings[mask].mean(axis=0).astype(np.float32)
            # Normalize
            center = center / (np.linalg.norm(center) + 1e-8)

            # Map cluster ID to persona ID (use personas.json as reference)
            persona_id = self._map_cluster_to_persona(cid)

            self.twins[persona_id] = {
                "cluster_id": int(cid),
                "center": center,
                "label": persona_id.replace("_", " ").title(),
                "tags": []
            }

        self.embedding_dim = embeddings.shape[1]
        self.temperature = self.router_config.get("temperature", 0.5)

        print(f"  Loaded {len(self.twins)} twins with dim={self.embedding_dim}")

    def _map_cluster_to_persona(self, cluster_id: int) -> str:
        """
        Map discovered cluster ID to persona ID.

        In production, this would use the persona classifier confusion matrix.
        For now, use a simple mapping based on cluster order.
        """
        # Load personas
        personas_path = Path(self.config.get("persona", {}).get("personas_path", "DATA/personas.json"))
        with open(personas_path) as f:
            personas = json.load(f)

        persona_list = personas.get("personas", [])
        if cluster_id < len(persona_list):
            return persona_list[cluster_id]["id"]
        else:
            return f"cluster_{cluster_id}"

    def get_twin_centers(self) -> Dict[str, np.ndarray]:
        """
        Get twin centers for mixture computation.

        Returns:
            Dict mapping twin_id -> center embedding
        """
        return {tid: twin["center"] for tid, twin in self.twins.items()}

    def get_temperature(self) -> float:
        """Get softmax temperature for mixture weights."""
        return self.temperature

    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.embedding_dim

    def encode_session(self, session_data: Dict[str, Any]) -> np.ndarray:
        """
        Encode session data to embedding.

        For legacy mode: Directly use provided embedding.
        For encoder mode: Run inference through trained encoder.

        Args:
            session_data: Dict with session information
                - For legacy: {"embedding": [15-D vector]}
                - For encoder: {"seq_tokens": [...], "rationale_tokens": [...], ...}

        Returns:
            Embedding vector (normalized)
        """
        if not self.use_encoder:
            # Legacy mode: extract embedding directly
            emb = np.array(session_data.get("embedding", []), dtype=np.float32)
            if len(emb) != self.embedding_dim:
                raise ValueError(f"Expected {self.embedding_dim}-D embedding, got {len(emb)}-D")
            # Normalize
            emb = emb / (np.linalg.norm(emb) + 1e-8)
            return emb
        else:
            # Encoder mode: run inference
            return self._encode_with_model(session_data)

    def _encode_with_model(self, session_data: Dict[str, Any]) -> np.ndarray:
        """Run encoder inference to get embedding."""
        # Load model if not already loaded
        if self.encoder_model is None:
            self._lazy_load_encoder()

        # Prepare inputs
        # This is a simplified version - in production, use proper tokenization
        # For now, assume session_data contains pre-tokenized inputs
        seq_tokens = torch.tensor(session_data.get("seq_tokens", []), dtype=torch.long).unsqueeze(0)
        rat_tokens = torch.tensor(session_data.get("rationale_tokens", []), dtype=torch.long).unsqueeze(0)
        persona_vec = torch.tensor(session_data.get("persona_vec", [0.5] * 12), dtype=torch.float32).unsqueeze(0)
        catalog_vec = torch.tensor(session_data.get("catalog_vec", [0.5] * 10), dtype=torch.float32).unsqueeze(0)

        # Move to device
        device = next(self.encoder_model.parameters()).device
        seq_tokens = seq_tokens.to(device)
        rat_tokens = rat_tokens.to(device)
        persona_vec = persona_vec.to(device)
        catalog_vec = catalog_vec.to(device)

        # Forward pass
        with torch.no_grad():
            outputs = self.encoder_model(
                seq_tokens=seq_tokens,
                rationale_tokens=rat_tokens,
                persona_vec=persona_vec,
                catalog_vec=catalog_vec
            )

        emb = outputs["fused_embedding"].cpu().numpy()[0]

        # Normalize
        emb = emb / (np.linalg.norm(emb) + 1e-8)

        return emb.astype(np.float32)

    def _lazy_load_encoder(self) -> None:
        """Lazy load encoder model on first use."""
        print(f"Loading encoder model from {self.encoder_ckpt_path}")

        from src.models.encoder.fuser import MultiViewEncoder

        # Load checkpoint
        checkpoint = torch.load(self.encoder_ckpt_path, map_location="cpu")

        # Initialize model
        model_config = self.encoder_config["model"]

        # Vocab sizes - these should be saved in checkpoint metadata
        # For now, use placeholder values
        vocab_size = checkpoint.get("vocab_size", 10000)
        num_actions = checkpoint.get("num_actions", 10)

        model = MultiViewEncoder(
            vocab_size_seq=vocab_size,
            vocab_size_rat=vocab_size,
            num_actions=num_actions,
            fused_dim=model_config["fused_dim"],
            seq_config=model_config["sequence"],
            rat_config=model_config["rationale"],
            persona_config=model_config["persona"],
            catalog_config=model_config["catalog"],
            fusion_config=model_config["fusion"]
        )

        # Load weights
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()

        self.encoder_model = model

        print(f"  Encoder loaded: {self.embedding_dim}-D embeddings")

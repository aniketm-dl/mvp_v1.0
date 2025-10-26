from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSREmbedder:
    """
    Wrapper for sentence-transformers model for SSR (Semantic Similarity Rating).

    Provides consistent interface for encoding text and persona vectors.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        cache_folder: Optional[Path] = None,
    ):
        """
        Initialize SSR embedder.

        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2, 384-D)
            device: Device to use (cuda/cpu, auto-detect if None)
            cache_folder: Model cache directory
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_folder = cache_folder

        logger.info(f"Loading embedding model: {model_name}")
        logger.info(f"Device: {self.device}")

        try:
            self.model = SentenceTransformer(
                model_name,
                device=self.device,
                cache_folder=str(cache_folder) if cache_folder else None,
            )
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def encode_texts(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """
        Encode text(s) into embeddings.

        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            normalize: Whether to L2-normalize embeddings
            show_progress_bar: Show progress for long lists

        Returns:
            Embeddings array of shape (n_texts, embedding_dim)
        """
        if isinstance(texts, str):
            texts = [texts]

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True,
            )

            return embeddings

        except Exception as e:
            logger.error(f"Text encoding failed: {e}")
            raise

    def encode_persona_vector(
        self,
        persona_vec: List[float],
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Encode persona vector (12-D) into embedding space.

        Since persona vectors are numeric, we project them into the embedding space
        using a learned linear projection (trained during SSR fine-tuning).

        For now, returns the persona vector as-is. Will be replaced with learned
        projection after SSR training.

        Args:
            persona_vec: 12-D persona feature vector
            normalize: Whether to L2-normalize

        Returns:
            Persona embedding (12-D for now, will be embedding_dim after training)
        """
        persona_array = np.array(persona_vec, dtype=np.float32).reshape(1, -1)

        if normalize:
            norm = np.linalg.norm(persona_array, axis=1, keepdims=True)
            persona_array = persona_array / (norm + 1e-8)

        return persona_array

    def compute_similarity(
        self,
        embeddings1: np.ndarray,
        embeddings2: np.ndarray,
        metric: str = "cosine",
    ) -> np.ndarray:
        """
        Compute pairwise similarity between two sets of embeddings.

        Args:
            embeddings1: Array of shape (n1, dim)
            embeddings2: Array of shape (n2, dim)
            metric: Similarity metric ("cosine" or "dot")

        Returns:
            Similarity matrix of shape (n1, n2)
        """
        if metric == "cosine":
            # Assuming embeddings are already normalized
            similarities = np.dot(embeddings1, embeddings2.T)
        elif metric == "dot":
            similarities = np.dot(embeddings1, embeddings2.T)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return similarities

    def save(self, save_path: Path):
        """Save model to disk."""
        save_path.mkdir(parents=True, exist_ok=True)
        self.model.save(str(save_path))
        logger.info(f"Saved embedding model to {save_path}")

    @classmethod
    def load(cls, model_path: Path, device: Optional[str] = None) -> SSREmbedder:
        """Load model from disk."""
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        logger.info(f"Loading embedding model from {model_path}")
        embedder = cls.__new__(cls)
        embedder.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        embedder.model = SentenceTransformer(str(model_path), device=embedder.device)
        embedder.embedding_dim = embedder.model.get_sentence_embedding_dimension()
        embedder.model_name = str(model_path)
        logger.info(f"Model loaded from {model_path}")
        return embedder

    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "device": self.device,
            "max_seq_length": self.model.max_seq_length,
        }

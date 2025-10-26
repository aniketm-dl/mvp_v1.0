from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional, TYPE_CHECKING

import numpy as np

from src.ssr.reference_statements import ReferenceStatementSets

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - typing convenience
    from src.ssr.embedder import SSREmbedder


class SSRAnchorMapper:
    """Compute Likert pmfs via semantic similarity to reference anchor sets."""

    def __init__(
        self,
        embedder: Optional["SSREmbedder"] = None,
        anchor_sets: Optional[Dict[str, List[str]]] = None,
        temperature: float = 1.0,
        epsilon: float = 1e-6,
        embedding_provider: str = "openai",
        embedding_model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
    ) -> None:
        if temperature <= 0:
            raise ValueError("temperature must be > 0")
        if epsilon <= 0:
            raise ValueError("epsilon must be > 0")

        if embedder is None:
            self.embedder = self._create_default_embedder(
                provider=embedding_provider, model=embedding_model, api_key=api_key
            )
        else:
            self.embedder = embedder

        self.temperature = temperature
        self.epsilon = epsilon

        self.anchor_sets = anchor_sets or ReferenceStatementSets.get_all_sets()
        self.set_names = list(self.anchor_sets.keys())
        self._anchor_embeddings = self._encode_anchor_sets()
        self._metadata = {
            "anchor_version": ReferenceStatementSets.get_version(),
            "anchor_hash": ReferenceStatementSets.compute_hash(),
            "embedding_provider": embedding_provider,
            "embedding_model": getattr(
                self.embedder,
                "model_name",
                getattr(self.embedder, "model_name_or_path", embedding_model),
            ),
            "temperature": temperature,
            "epsilon": epsilon,
        }

    def _encode_anchor_sets(self) -> Dict[str, np.ndarray]:
        embeddings: Dict[str, np.ndarray] = {}
        for set_name, statements in self.anchor_sets.items():
            embeddings[set_name] = self.embedder.encode_texts(statements, normalize=True)
        return embeddings

    def compute_pmf(
        self,
        response_text: str,
        *,
        temperature: Optional[float] = None,
        epsilon: Optional[float] = None,
    ) -> Dict[str, np.ndarray]:
        """Compute averaged Likert pmf for a single response text."""
        temp = temperature if temperature is not None else self.temperature
        eps = epsilon if epsilon is not None else self.epsilon

        if temp <= 0:
            raise ValueError("temperature must be > 0")
        if eps <= 0:
            raise ValueError("epsilon must be > 0")

        response_embedding = self.embedder.encode_texts(response_text, normalize=True)[0]

        per_set_pmfs: Dict[str, np.ndarray] = {}
        for set_name, anchor_embs in self._anchor_embeddings.items():
            sims = np.dot(anchor_embs, response_embedding)
            shifted = sims - sims.min()
            shifted = np.clip(shifted, 0.0, None) + eps

            if temp != 1.0:
                adjusted = np.power(shifted, 1.0 / temp)
            else:
                adjusted = shifted

            pmf = adjusted / adjusted.sum()
            per_set_pmfs[set_name] = pmf

        averaged_pmf = np.vstack(list(per_set_pmfs.values())).mean(axis=0)
        likert_values = np.arange(1, 6, dtype=np.float32)
        expected_rating = float(np.dot(averaged_pmf, likert_values))

        return {
            "pmf": averaged_pmf,
            "expected_rating": expected_rating,
            "per_set_pmfs": per_set_pmfs,
        }

    def compute_pmfs_batch(
        self,
        response_texts: List[str],
        *,
        temperature: Optional[float] = None,
        epsilon: Optional[float] = None,
    ) -> List[Dict[str, np.ndarray]]:
        """Vectorised convenience wrapper around :meth:`compute_pmf`."""
        results: List[Dict[str, np.ndarray]] = []
        for text in response_texts:
            results.append(
                self.compute_pmf(
                    text,
                    temperature=temperature,
                    epsilon=epsilon,
                )
            )
        return results

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _create_default_embedder(
        provider: str,
        model: str,
        api_key: Optional[str],
    ):
        provider = provider.lower()
        if provider == "openai":
            return _OpenAIEmbeddingClient(model=model, api_key=api_key)
        raise ValueError(
            f"Unsupported embedding provider '{provider}'. "
            "Pass a custom embedder if you do not wish to use OpenAI."
        )

    def get_metadata(self) -> Dict[str, object]:
        """Return static metadata describing the configured anchor mapping."""
        return self._metadata.copy()


class _OpenAIEmbeddingClient:
    """Thin wrapper around OpenAI embeddings API for anchor mapping."""

    def __init__(self, model: str, api_key: Optional[str] = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError(
                "openai package is required for OpenAI embedding provider. "
                "Install via `pip install openai`."
            ) from exc

        self.model_name = model
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OPENAI_API_KEY not set. Provide an API key to use OpenAI embeddings."
            )
        self.client = OpenAI(api_key=key)

    def encode_texts(
        self,
        texts: List[str] | str,
        normalize: bool = True,
        **_: Dict,
    ) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        response = self.client.embeddings.create(model=self.model_name, input=texts)

        vectors = []
        for item in response.data:
            vec = np.array(item.embedding, dtype=np.float32)
            if normalize:
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
            vectors.append(vec)

        return np.vstack(vectors)

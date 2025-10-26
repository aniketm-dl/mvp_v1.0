from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from scipy.stats import spearmanr
from sentence_transformers import InputExample, SentenceTransformer, losses
from torch.utils.data import DataLoader

from src.ssr.embedder import SSREmbedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSRRegressionHead(nn.Module):
    """
    Regression head for predicting Likert distributions from embeddings.

    Maps embedding space to 5-class probability distribution (Likert 1-5).
    """

    def __init__(self, embedding_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 5),  # 5 Likert classes
            nn.Softmax(dim=-1),
        )

    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        """
        Args:
            embeddings: (batch_size, embedding_dim)

        Returns:
            Likert probabilities: (batch_size, 5)
        """
        return self.net(embeddings)


class SSRTrainer:
    """
    Trainer for SSR (Semantic Similarity Rating) model.

    Training pipeline:
    1. Fine-tune sentence-transformers on (persona, stimulus) similarity
    2. Train regression head to predict Likert distributions
    3. Joint fine-tuning for end-to-end optimization
    """

    def __init__(
        self,
        base_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ):
        self.base_model = base_model
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.output_dir = output_dir or Path("models/ssr")

        # Initialize embedder
        self.embedder = SSREmbedder(base_model, device=self.device)
        self.embedding_dim = self.embedder.embedding_dim

        # Initialize regression head
        self.regression_head = SSRRegressionHead(self.embedding_dim).to(self.device)

        # Training history
        self.history: Dict[str, List[float]] = {
            "train_loss": [],
            "val_loss": [],
            "val_correlation": [],
        }

    def load_training_data(
        self, training_pairs_path: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Load SSR training pairs from JSONL.

        Expected format:
        {
          "user_id": "u123",
          "session_id": "s456",
          "persona_vec": [0.6, 0.8, ...],  // 12-D
          "stimulus_text": "Free shipping on all orders",
          "likert_score": 4,  // 1-5
          "rationale": "Explanation..."
        }

        Returns:
            (train_data, val_data) split 80/20
        """
        if not training_pairs_path.exists():
            raise FileNotFoundError(f"Training data not found: {training_pairs_path}")

        pairs = []
        with open(training_pairs_path, "r") as f:
            for line in f:
                pair = json.loads(line.strip())
                pairs.append(pair)

        logger.info(f"Loaded {len(pairs)} training pairs from {training_pairs_path}")

        # Split train/val
        np.random.seed(42)
        indices = np.random.permutation(len(pairs))
        split_idx = int(0.8 * len(pairs))

        train_pairs = [pairs[i] for i in indices[:split_idx]]
        val_pairs = [pairs[i] for i in indices[split_idx:]]

        logger.info(f"Train: {len(train_pairs)}, Val: {len(val_pairs)}")
        return train_pairs, val_pairs

    def prepare_contrastive_data(
        self, pairs: List[Dict[str, Any]]
    ) -> List[InputExample]:
        """
        Prepare data for contrastive learning.

        Creates (text1, text2, score) triplets for sentence-transformers.
        """
        examples = []

        for pair in pairs:
            # Normalize Likert score to [0, 1] for contrastive loss
            likert_score = pair["likert_score"]
            normalized_score = (likert_score - 1) / 4.0  # 1-5 -> 0-1

            # Create input example (stimulus text as both anchor and positive)
            # In real training, we'd need persona text representation
            # For now, use stimulus text with score as similarity
            example = InputExample(
                texts=[pair["stimulus_text"], pair["stimulus_text"]],
                label=normalized_score,
            )
            examples.append(example)

        return examples

    def train_embedding_model(
        self,
        train_pairs: List[Dict[str, Any]],
        val_pairs: List[Dict[str, Any]],
        epochs: int = 10,
        batch_size: int = 32,
        learning_rate: float = 2e-5,
        warmup_steps: int = 100,
    ) -> Dict[str, float]:
        """
        Fine-tune sentence-transformers model on contrastive task.

        Args:
            train_pairs: Training data
            val_pairs: Validation data
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            warmup_steps: Warmup steps for scheduler

        Returns:
            Training metrics
        """
        logger.info("=" * 80)
        logger.info("PHASE 1: Fine-tuning embedding model (contrastive learning)")
        logger.info("=" * 80)

        # Prepare contrastive data
        train_examples = self.prepare_contrastive_data(train_pairs)
        train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)

        # Define loss (CosineSimilarityLoss for regression-style similarity)
        train_loss = losses.CosineSimilarityLoss(self.embedder.model)

        # Calculate total steps
        total_steps = len(train_dataloader) * epochs

        # Train
        logger.info(f"Training for {epochs} epochs ({total_steps} steps)")
        self.embedder.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=warmup_steps,
            optimizer_params={"lr": learning_rate},
            show_progress_bar=True,
            save_best_model=True,
            output_path=str(self.output_dir / "embedding_model"),
        )

        logger.info("✅ Embedding model fine-tuning complete")
        return {"status": "complete"}

    def train_regression_head(
        self,
        train_pairs: List[Dict[str, Any]],
        val_pairs: List[Dict[str, Any]],
        epochs: int = 20,
        batch_size: int = 64,
        learning_rate: float = 1e-3,
    ) -> Dict[str, float]:
        """
        Train regression head to predict Likert distributions.

        Args:
            train_pairs: Training data
            val_pairs: Validation data
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate

        Returns:
            Best validation metrics
        """
        logger.info("=" * 80)
        logger.info("PHASE 2: Training regression head (Likert prediction)")
        logger.info("=" * 80)

        # Prepare data
        train_embeddings, train_labels = self._prepare_regression_data(train_pairs)
        val_embeddings, val_labels = self._prepare_regression_data(val_pairs)

        # Create dataloaders
        train_dataset = torch.utils.data.TensorDataset(
            torch.FloatTensor(train_embeddings),
            torch.LongTensor(train_labels),
        )
        val_dataset = torch.utils.data.TensorDataset(
            torch.FloatTensor(val_embeddings),
            torch.LongTensor(val_labels),
        )

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Setup optimizer and loss
        optimizer = torch.optim.Adam(self.regression_head.parameters(), lr=learning_rate)
        criterion = nn.CrossEntropyLoss()

        best_val_corr = -1.0
        best_epoch = 0

        # Training loop
        for epoch in range(epochs):
            # Train
            self.regression_head.train()
            train_loss = 0.0

            for embeddings, labels in train_loader:
                embeddings = embeddings.to(self.device)
                labels = labels.to(self.device)

                optimizer.zero_grad()
                outputs = self.regression_head(embeddings)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validate
            val_loss, val_corr = self._validate_regression(val_loader, criterion)

            # Log
            logger.info(
                f"Epoch {epoch+1}/{epochs}: "
                f"train_loss={train_loss:.4f}, "
                f"val_loss={val_loss:.4f}, "
                f"val_corr={val_corr:.3f}"
            )

            # Save history
            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            self.history["val_correlation"].append(val_corr)

            # Track best model
            if val_corr > best_val_corr:
                best_val_corr = val_corr
                best_epoch = epoch + 1
                self._save_regression_head()

        logger.info(f"✅ Regression head training complete. Best val correlation: {best_val_corr:.3f} at epoch {best_epoch}")

        return {
            "best_val_correlation": best_val_corr,
            "best_epoch": best_epoch,
            "final_train_loss": train_loss,
            "final_val_loss": val_loss,
        }

    def _prepare_regression_data(
        self, pairs: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare embeddings and labels for regression head training.

        Returns:
            (embeddings, labels) where labels are 0-indexed (0-4 for Likert 1-5)
        """
        # Extract stimulus texts
        texts = [pair["stimulus_text"] for pair in pairs]

        # Encode texts
        embeddings = self.embedder.encode_texts(texts, show_progress_bar=True)

        # Extract Likert scores (convert 1-5 to 0-4)
        labels = np.array([pair["likert_score"] - 1 for pair in pairs], dtype=np.int64)

        return embeddings, labels

    def _validate_regression(
        self, val_loader: DataLoader, criterion: nn.Module
    ) -> Tuple[float, float]:
        """
        Validate regression head.

        Returns:
            (val_loss, val_correlation)
        """
        self.regression_head.eval()
        val_loss = 0.0
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for embeddings, labels in val_loader:
                embeddings = embeddings.to(self.device)
                labels = labels.to(self.device)

                outputs = self.regression_head(embeddings)
                loss = criterion(outputs, labels)
                val_loss += loss.item()

                # Get predicted class (argmax)
                preds = torch.argmax(outputs, dim=-1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        val_loss /= len(val_loader)

        # Compute correlation
        correlation, _ = spearmanr(all_preds, all_labels)

        return val_loss, correlation

    def _save_regression_head(self):
        """Save regression head checkpoint."""
        save_path = self.output_dir / "regression_head.pt"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        torch.save(
            {
                "state_dict": self.regression_head.state_dict(),
                "embedding_dim": self.embedding_dim,
            },
            save_path,
        )

    def save_complete_model(self, save_path: Path):
        """
        Save complete SSR model (embedder + regression head).

        Args:
            save_path: Directory to save model
        """
        save_path.mkdir(parents=True, exist_ok=True)

        # Save embedder
        self.embedder.save(save_path / "embedding_model")

        # Save regression head
        torch.save(
            {
                "state_dict": self.regression_head.state_dict(),
                "embedding_dim": self.embedding_dim,
            },
            save_path / "regression_head.pt",
        )

        # Save config
        config = {
            "base_model": self.base_model,
            "embedding_dim": self.embedding_dim,
            "device": self.device,
        }

        with open(save_path / "ssr_config.json", "w") as f:
            json.dump(config, f, indent=2)

        # Save training history
        with open(save_path / "training_history.json", "w") as f:
            json.dump(self.history, f, indent=2)

        logger.info(f"✅ Saved complete SSR model to {save_path}")

    @classmethod
    def load_complete_model(cls, model_path: Path, device: Optional[str] = None) -> SSRTrainer:
        """
        Load complete SSR model from disk.

        Args:
            model_path: Directory containing saved model
            device: Device to load model on

        Returns:
            Loaded SSRTrainer instance
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        # Load config
        with open(model_path / "ssr_config.json", "r") as f:
            config = json.load(f)

        # Create trainer instance
        trainer = cls(
            base_model=str(model_path / "embedding_model"),
            device=device or config.get("device"),
            output_dir=model_path,
        )

        # Load regression head
        checkpoint = torch.load(
            model_path / "regression_head.pt",
            map_location=trainer.device,
        )
        trainer.regression_head.load_state_dict(checkpoint["state_dict"])

        # Load history if available
        history_path = model_path / "training_history.json"
        if history_path.exists():
            with open(history_path, "r") as f:
                trainer.history = json.load(f)

        logger.info(f"✅ Loaded SSR model from {model_path}")
        return trainer

    def predict_likert_distribution(
        self, stimulus_text: str
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Predict Likert distribution for a stimulus.

        Args:
            stimulus_text: Input text (e.g., "Free shipping on all orders")

        Returns:
            (distribution, metrics) where:
            - distribution: P(Likert=1..5) as [p1, p2, p3, p4, p5]
            - metrics: {"mean": expected value, "std": standard deviation}
        """
        self.regression_head.eval()

        # Encode stimulus
        embedding = self.embedder.encode_texts(stimulus_text, normalize=True)

        # Predict distribution
        with torch.no_grad():
            embedding_tensor = torch.FloatTensor(embedding).to(self.device)
            distribution = self.regression_head(embedding_tensor)
            distribution = distribution.cpu().numpy()[0]

        # Compute metrics
        likert_values = np.array([1, 2, 3, 4, 5])
        mean_rating = np.sum(distribution * likert_values)
        variance = np.sum(distribution * (likert_values - mean_rating) ** 2)
        std_rating = np.sqrt(variance)

        metrics = {
            "mean": float(mean_rating),
            "std": float(std_rating),
            "mode": int(np.argmax(distribution) + 1),
        }

        return distribution, metrics

from __future__ import annotations

import pytest
import torch
import yaml

from src.models.encoder.fuser import FusionMLP, MultiViewEncoder
from src.models.encoder.losses import (
    InfoNCELoss,
    MultiObjectiveLoss,
    NextActionLoss,
    RationaleAlignmentLoss,
)
from src.models.encoder.modules import (
    CatalogEncoder,
    NextActionHead,
    PersonaEncoder,
    RationaleEncoder,
    SequenceEncoder,
)


class TestEncoderModules:
    """Test individual encoder modules."""

    def test_sequence_encoder_shape(self):
        """Test sequence encoder output shape."""
        vocab_size = 1000
        batch_size = 4
        seq_len = 120
        hidden_dim = 256

        encoder = SequenceEncoder(
            vocab_size=vocab_size, embed_dim=128, hidden_dim=hidden_dim, num_layers=2
        )

        seq_tokens = torch.randint(0, vocab_size, (batch_size, seq_len))
        output = encoder(seq_tokens)

        assert output.shape == (batch_size, hidden_dim)

    def test_rationale_encoder_shape(self):
        """Test rationale encoder output shape."""
        vocab_size = 1000
        batch_size = 4
        seq_len = 60
        hidden_dim = 128

        encoder = RationaleEncoder(
            vocab_size=vocab_size, embed_dim=64, hidden_dim=hidden_dim, num_layers=1
        )

        rationale_tokens = torch.randint(0, vocab_size, (batch_size, seq_len))
        output = encoder(rationale_tokens)

        assert output.shape == (batch_size, hidden_dim)

    def test_persona_encoder_shape(self):
        """Test persona encoder output shape."""
        batch_size = 4
        input_dim = 12
        output_dim = 128

        encoder = PersonaEncoder(
            input_dim=input_dim, hidden_dims=[64, 128], output_dim=output_dim
        )

        persona_vec = torch.randn(batch_size, input_dim)
        output = encoder(persona_vec)

        assert output.shape == (batch_size, output_dim)

    def test_catalog_encoder_shape(self):
        """Test catalog encoder output shape."""
        batch_size = 4
        input_dim = 10
        output_dim = 64

        encoder = CatalogEncoder(
            input_dim=input_dim, hidden_dims=[32, 64], output_dim=output_dim
        )

        catalog_vec = torch.randn(batch_size, input_dim)
        output = encoder(catalog_vec)

        assert output.shape == (batch_size, output_dim)

    def test_next_action_head_shape(self):
        """Test next action head output shape."""
        batch_size = 4
        input_dim = 256
        num_actions = 10

        head = NextActionHead(input_dim=input_dim, num_actions=num_actions)

        fused_embedding = torch.randn(batch_size, input_dim)
        logits = head(fused_embedding)

        assert logits.shape == (batch_size, num_actions)


class TestFusionModule:
    """Test fusion module."""

    def test_fusion_mlp_shape(self):
        """Test fusion MLP output shape."""
        batch_size = 4
        seq_dim = 256
        rat_dim = 128
        per_dim = 128
        cat_dim = 64
        input_dim = seq_dim + rat_dim + per_dim + cat_dim
        output_dim = 256

        fusion = FusionMLP(
            input_dim=input_dim,
            hidden_dims=[384, 256],
            output_dim=output_dim,
            use_layer_norm=True,
        )

        seq_emb = torch.randn(batch_size, seq_dim)
        rat_emb = torch.randn(batch_size, rat_dim)
        per_emb = torch.randn(batch_size, per_dim)
        cat_emb = torch.randn(batch_size, cat_dim)

        output = fusion(seq_emb, rat_emb, per_emb, cat_emb)

        assert output.shape == (batch_size, output_dim)

    def test_fusion_ablation(self):
        """Test fusion with ablation flags."""
        batch_size = 4
        input_dim = 576
        output_dim = 256

        fusion = FusionMLP(input_dim=input_dim, output_dim=output_dim)

        seq_emb = torch.randn(batch_size, 256)
        rat_emb = torch.randn(batch_size, 128)
        per_emb = torch.randn(batch_size, 128)
        cat_emb = torch.randn(batch_size, 64)

        # Normal fusion
        out_full = fusion(seq_emb, rat_emb, per_emb, cat_emb)

        # Ablate persona
        out_no_persona = fusion(
            seq_emb, rat_emb, per_emb, cat_emb, disable_persona=True
        )

        # Ablate rationale
        out_no_rationale = fusion(
            seq_emb, rat_emb, per_emb, cat_emb, disable_rationale=True
        )

        # Outputs should differ
        assert not torch.allclose(out_full, out_no_persona)
        assert not torch.allclose(out_full, out_no_rationale)


class TestMultiViewEncoder:
    """Test complete multi-view encoder."""

    def test_multiview_encoder_shapes(self):
        """Test multi-view encoder output shapes."""
        vocab_size = 1000
        num_actions = 10
        batch_size = 4
        fused_dim = 256

        config = {
            "sequence": {
                "embed_dim": 128,
                "hidden_dim": 256,
                "num_layers": 2,
                "dropout": 0.1,
                "max_seq_len": 120,
            },
            "rationale": {
                "embed_dim": 64,
                "hidden_dim": 128,
                "num_layers": 1,
                "dropout": 0.1,
                "max_seq_len": 60,
            },
            "persona": {"input_dim": 12, "hidden_dims": [64, 128], "output_dim": 128},
            "catalog": {"input_dim": 10, "hidden_dims": [32, 64], "output_dim": 64},
            "fusion": {
                "input_dim": 576,
                "hidden_dims": [384, 256],
                "output_dim": 256,
                "use_layer_norm": True,
            },
        }

        encoder = MultiViewEncoder(
            vocab_size=vocab_size,
            num_actions=num_actions,
            seq_config=config["sequence"],
            rationale_config=config["rationale"],
            persona_config=config["persona"],
            catalog_config=config["catalog"],
            fusion_config=config["fusion"],
            fused_dim=fused_dim,
        )

        # Create dummy inputs
        seq_tokens = torch.randint(0, vocab_size, (batch_size, 120))
        rationale_tokens = torch.randint(0, vocab_size, (batch_size, 60))
        persona_vec = torch.randn(batch_size, 12)
        catalog_vec = torch.randn(batch_size, 10)

        # Forward pass
        outputs = encoder(seq_tokens, rationale_tokens, persona_vec, catalog_vec)

        # Check output shapes
        assert outputs["fused_embedding"].shape == (batch_size, fused_dim)
        assert outputs["action_logits"].shape == (batch_size, num_actions)
        assert outputs["seq_embedding"].shape == (batch_size, 256)
        assert outputs["rationale_embedding"].shape == (batch_size, 128)
        assert outputs["persona_embedding"].shape == (batch_size, 128)
        assert outputs["catalog_embedding"].shape == (batch_size, 64)

    def test_multiview_encoder_ablations(self):
        """Test ablations in multi-view encoder."""
        vocab_size = 100
        num_actions = 5
        batch_size = 2
        fused_dim = 256

        # Minimal config
        config = {
            "sequence": {"embed_dim": 64, "hidden_dim": 128, "num_layers": 1},
            "rationale": {"embed_dim": 32, "hidden_dim": 64, "num_layers": 1},
            "persona": {"input_dim": 12, "hidden_dims": [32], "output_dim": 64},
            "catalog": {"input_dim": 10, "hidden_dims": [32], "output_dim": 32},
            "fusion": {
                "input_dim": 128 + 64 + 64 + 32,
                "hidden_dims": [128],
                "output_dim": 256,
            },
        }

        encoder = MultiViewEncoder(
            vocab_size=vocab_size,
            num_actions=num_actions,
            seq_config=config["sequence"],
            rationale_config=config["rationale"],
            persona_config=config["persona"],
            catalog_config=config["catalog"],
            fusion_config=config["fusion"],
            fused_dim=fused_dim,
        )

        # Create dummy inputs
        seq_tokens = torch.randint(0, vocab_size, (batch_size, 120))
        rationale_tokens = torch.randint(0, vocab_size, (batch_size, 60))
        persona_vec = torch.randn(batch_size, 12)
        catalog_vec = torch.randn(batch_size, 10)

        # Full model
        out_full = encoder(seq_tokens, rationale_tokens, persona_vec, catalog_vec)

        # Ablate persona
        out_no_persona = encoder(
            seq_tokens,
            rationale_tokens,
            persona_vec,
            catalog_vec,
            disable_persona=True,
        )

        # Ablate rationale
        out_no_rationale = encoder(
            seq_tokens,
            rationale_tokens,
            persona_vec,
            catalog_vec,
            disable_rationale=True,
        )

        # Embeddings should differ
        assert not torch.allclose(
            out_full["fused_embedding"], out_no_persona["fused_embedding"]
        )
        assert not torch.allclose(
            out_full["fused_embedding"], out_no_rationale["fused_embedding"]
        )


class TestLosses:
    """Test loss functions."""

    def test_next_action_loss(self):
        """Test next action loss."""
        num_actions = 10
        batch_size = 4

        loss_fn = NextActionLoss(num_actions=num_actions, weight=1.0)

        logits = torch.randn(batch_size, num_actions)
        labels = torch.randint(0, num_actions, (batch_size,))

        loss = loss_fn(logits, labels)

        assert loss.ndim == 0
        assert loss.item() > 0

    def test_infonce_loss(self):
        """Test InfoNCE loss."""
        batch_size = 8
        dim = 128

        loss_fn = InfoNCELoss(temperature=0.07, weight=0.5)

        fused_emb = torch.randn(batch_size, dim)
        persona_emb = torch.randn(batch_size, dim)

        loss = loss_fn(fused_emb, persona_emb)

        assert loss.ndim == 0
        assert loss.item() > 0

    def test_rationale_alignment_loss(self):
        """Test rationale alignment loss."""
        batch_size = 4
        dim = 128

        loss_fn = RationaleAlignmentLoss(weight=0.3)

        fused_emb = torch.randn(batch_size, dim)
        rationale_emb = torch.randn(batch_size, dim)

        # Without mask
        loss = loss_fn(fused_emb, rationale_emb)
        assert loss.ndim == 0

        # With mask
        mask = torch.tensor([1.0, 0.0, 1.0, 1.0])
        loss_masked = loss_fn(fused_emb, rationale_emb, mask)
        assert loss_masked.ndim == 0

    def test_multi_objective_loss(self):
        """Test multi-objective loss."""
        config = {
            "next_action": {"enabled": True, "weight": 1.0, "num_actions": 10},
            "persona_alignment": {
                "enabled": True,
                "weight": 0.5,
                "temperature": 0.07,
                "num_negatives": 7,
            },
            "rationale_alignment": {"enabled": True, "weight": 0.3},
            "psychometric": {"enabled": False, "weight": 0.1, "target_dim": 8},
            "fused_dim": 256,
            "persona_dim": 128,
            "rationale_dim": 128,
        }

        loss_fn = MultiObjectiveLoss(config)

        batch_size = 8
        outputs = {
            "fused_embedding": torch.randn(batch_size, 256),
            "action_logits": torch.randn(batch_size, 10),
            "persona_embedding": torch.randn(batch_size, 128),
            "rationale_embedding": torch.randn(batch_size, 128),
        }

        action_labels = torch.randint(0, 10, (batch_size,))
        rationale_mask = torch.tensor([1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0])

        losses = loss_fn(outputs, action_labels, rationale_mask)

        assert "total" in losses
        assert "next_action" in losses
        assert "persona_alignment" in losses
        assert "rationale_alignment" in losses
        assert losses["total"].item() > 0


class TestConfigIntegration:
    """Test config loading and model building."""

    def test_config_loading(self):
        """Test loading encoder config."""
        with open("CONFIGS/encoder.yaml", "r") as f:
            config = yaml.safe_load(f)

        assert "model" in config
        assert "training" in config
        assert "loss" in config
        assert config["model"]["fused_dim"] >= 192
        assert config["model"]["fused_dim"] <= 384


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

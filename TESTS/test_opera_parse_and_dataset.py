from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.data.opera.dataset import OPeRADataModule, OPeRADataset
from src.data.opera.parse_opera import HTMLNormalizer, OPeRAParser
from src.data.opera.schemas import OPeRASession, OPeRAStep


class TestHTMLNormalizer:
    """Test HTML normalization."""

    def test_strip_scripts(self):
        config = {"strip_scripts": True, "strip_styles": True}
        normalizer = HTMLNormalizer(config)

        html = "<div>Hello<script>alert('evil')</script>World</div>"
        result = normalizer.normalize(html)
        assert "script" not in result.lower()
        assert "alert" not in result.lower()
        assert "Hello" in result
        assert "World" in result

    def test_semantic_tags(self):
        config = {"keep_semantic_tags": True, "semantic_tags": ["strong", "em"]}
        normalizer = HTMLNormalizer(config)

        html = "<strong>Bold</strong> and <em>italic</em> text"
        result = normalizer.normalize(html)
        assert "**Bold**" in result
        assert "*italic*" in result

    def test_whitespace_normalization(self):
        config = {"normalize_whitespace": True}
        normalizer = HTMLNormalizer(config)

        html = "<p>Multiple    spaces\n\nand\nlines</p>"
        result = normalizer.normalize(html)
        assert "  " not in result
        assert "\n" not in result

    def test_max_length(self):
        config = {"max_text_length": 20}
        normalizer = HTMLNormalizer(config)

        html = "<div>" + "a" * 100 + "</div>"
        result = normalizer.normalize(html)
        assert len(result) <= 20


class TestSchemas:
    """Test Pydantic schemas."""

    def test_opera_step_valid(self):
        step = OPeRAStep(
            t=0,
            observation="User views product page with price $29.99",
            action="view",
            action_label=0,
            persona_vec=[0.5] * 12,
            rationale="Looking for affordable options",
            context={"price": 29.99},
        )
        assert step.t == 0
        assert len(step.persona_vec) == 12

    def test_opera_step_token_budget(self):
        # Observation within budget
        obs = " ".join(["token"] * 120)
        step = OPeRAStep(
            t=0,
            observation=obs,
            action="click",
            action_label=0,
            persona_vec=[0.5] * 12,
        )
        assert len(step.observation.split()) <= 120

        # Observation exceeds budget
        obs_too_long = " ".join(["token"] * 121)
        with pytest.raises(ValueError, match="exceeds 120 tokens"):
            OPeRAStep(
                t=0,
                observation=obs_too_long,
                action="click",
                action_label=0,
                persona_vec=[0.5] * 12,
            )

    def test_opera_step_rationale_budget(self):
        # Rationale within budget
        rat = " ".join(["word"] * 60)
        step = OPeRAStep(
            t=0,
            observation="Short observation text here",
            action="click",
            action_label=0,
            persona_vec=[0.5] * 12,
            rationale=rat,
        )
        assert len(step.rationale.split()) <= 60

        # Rationale exceeds budget
        rat_too_long = " ".join(["word"] * 61)
        with pytest.raises(ValueError, match="exceeds 60 tokens"):
            OPeRAStep(
                t=0,
                observation="Short observation text here",
                action="click",
                action_label=0,
                persona_vec=[0.5] * 12,
                rationale=rat_too_long,
            )

    def test_persona_vec_bounds(self):
        # Valid bounds
        step = OPeRAStep(
            t=0,
            observation="Test observation with enough length",
            action="click",
            action_label=0,
            persona_vec=[0.0, 0.5, 1.0] + [0.5] * 9,
        )
        assert all(0 <= v <= 1 for v in step.persona_vec)

        # Out of bounds
        with pytest.raises(ValueError, match="must be in"):
            OPeRAStep(
                t=0,
                observation="Test observation with enough length",
                action="click",
                action_label=0,
                persona_vec=[1.5] + [0.5] * 11,
            )

    def test_session_alignment(self):
        steps = [
            OPeRAStep(
                t=i,
                observation=f"Observation {i} with sufficient text length",
                action="click",
                action_label=0,
                persona_vec=[0.5] * 12,
            )
            for i in range(5)
        ]

        session = OPeRASession(
            user_id="u1",
            session_id="s1",
            timestamp=datetime.now(),
            steps=steps,
        )
        assert len(session.steps) == 5

        # Misaligned indices
        bad_steps = [
            OPeRAStep(
                t=0,
                observation="First observation with enough text",
                action="click",
                action_label=0,
                persona_vec=[0.5] * 12,
            ),
            OPeRAStep(
                t=2,
                observation="Skipped index with enough text",
                action="click",
                action_label=0,
                persona_vec=[0.5] * 12,
            ),
        ]
        with pytest.raises(ValueError, match="sequential"):
            OPeRASession(
                user_id="u1",
                session_id="s1",
                timestamp=datetime.now(),
                steps=bad_steps,
            )


class TestParser:
    """Test OPeRA parser."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        config_content = """
paths:
  raw_dir: "DATA/OPeRA/raw"
  processed_dir: "DATA/OPeRA/processed"
input:
  format: "jsonl"
  encoding: "utf-8"
token_limits:
  observation_max: 120
  rationale_max: 60
  action_max: 20
  context_max: 80
html_processing:
  keep_semantic_tags: true
  semantic_tags: ["strong", "em"]
  strip_scripts: true
  strip_styles: true
  normalize_whitespace: true
  max_text_length: 500
persona:
  ocean_dim: 5
  psychographic_dim: 4
  demographic_dim: 3
  total_dim: 12
splits:
  train: 0.7
  val: 0.15
  test: 0.15
  min_sessions_per_user: 2
  random_seed: 17
quality:
  min_observation_length: 10
  min_action_length: 1
  max_steps_per_session: 100
  allow_null_rationale: true
  require_valid_action: true
actions:
  allowed_types: ["click", "view", "purchase", "add_to_cart"]
output:
  format: "parquet"
  compression: "snappy"
alignment:
  require_observation_per_step: true
  require_action_per_step: true
deterministic: true
seed: 17
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(config_content)
            return f.name

    @pytest.fixture
    def temp_data(self):
        """Create temporary test data."""
        sessions = [
            {
                "user_id": "u1",
                "session_id": "s1",
                "timestamp": "2024-01-01T10:00:00",
                "persona_vec": [0.5] * 12,
                "steps": [
                    {
                        "observation": "User views product page with <strong>great deal</strong>",
                        "action": "view",
                        "rationale": "Looking for good prices",
                        "context": {"price": 29.99},
                    },
                    {
                        "observation": "User clicks add to cart button",
                        "action": "add_to_cart",
                        "rationale": "Decided to purchase",
                        "context": {"price": 29.99},
                    },
                ],
            },
            {
                "user_id": "u1",
                "session_id": "s2",
                "timestamp": "2024-01-02T11:00:00",
                "persona_vec": [0.5] * 12,
                "steps": [
                    {
                        "observation": "User searches for electronics",
                        "action": "click",
                        "context": {},
                    }
                ],
            },
            {
                "user_id": "u2",
                "session_id": "s3",
                "timestamp": "2024-01-01T12:00:00",
                "persona_vec": [0.6] * 12,
                "steps": [
                    {
                        "observation": "Premium user views luxury items",
                        "action": "view",
                        "rationale": "Seeking quality products",
                        "context": {"price": 199.99},
                    },
                    {
                        "observation": "User completes purchase transaction",
                        "action": "purchase",
                        "rationale": "Satisfied with quality",
                        "context": {"price": 199.99},
                    },
                ],
            },
            {
                "user_id": "u2",
                "session_id": "s4",
                "timestamp": "2024-01-03T13:00:00",
                "persona_vec": [0.6] * 12,
                "steps": [
                    {
                        "observation": "User returns to view purchase history page",
                        "action": "view",
                        "context": {},
                    }
                ],
            },
        ]

        temp_dir = tempfile.mkdtemp()
        data_file = Path(temp_dir) / "test_data.jsonl"

        with open(data_file, "w") as f:
            for session in sessions:
                f.write(json.dumps(session) + "\n")

        return temp_dir

    def test_parser_basic(self, temp_config, temp_data):
        """Test basic parsing functionality."""
        parser = OPeRAParser(temp_config)
        sessions = parser.parse_directory(Path(temp_data))

        assert len(sessions) == 4
        assert all(isinstance(s, OPeRASession) for s in sessions)

    def test_parser_html_normalization(self, temp_config, temp_data):
        """Test HTML is normalized correctly."""
        parser = OPeRAParser(temp_config)
        sessions = parser.parse_directory(Path(temp_data))

        # Check first observation was normalized
        first_obs = sessions[0].steps[0].observation
        assert "strong" not in first_obs
        assert "**great deal**" in first_obs

    def test_parser_token_budgets(self, temp_config, temp_data):
        """Test token budgets are enforced."""
        parser = OPeRAParser(temp_config)
        sessions = parser.parse_directory(Path(temp_data))

        for session in sessions:
            for step in session.steps:
                assert len(step.observation.split()) <= 120
                if step.rationale:
                    assert len(step.rationale.split()) <= 60

    def test_parser_splits(self, temp_config, temp_data):
        """Test stratified splits."""
        parser = OPeRAParser(temp_config)
        sessions = parser.parse_directory(Path(temp_data))
        splits = parser.create_splits(sessions)

        # Both users have 2 sessions each
        assert "train" in splits
        assert "val" in splits
        assert "test" in splits

        total = sum(len(s) for s in splits.values())
        assert total == 4

    def test_parser_stats(self, temp_config, temp_data):
        """Test statistics computation."""
        parser = OPeRAParser(temp_config)
        sessions = parser.parse_directory(Path(temp_data))
        splits = parser.create_splits(sessions)
        stats = parser.compute_stats(splits)

        assert stats.total_sessions == 4
        assert stats.total_steps == 6
        assert stats.unique_users == 2
        assert stats.observation_coverage >= 0.9
        assert stats.action_coverage == 1.0


class TestDataset:
    """Test PyTorch dataset."""

    @pytest.fixture
    def sample_parquet(self):
        """Create sample parquet file."""
        import pandas as pd

        data = {
            "user_id": ["u1", "u1", "u2"],
            "session_id": ["s1", "s1", "s2"],
            "timestamp": [datetime.now()] * 3,
            "t": [0, 1, 0],
            "observation": [
                "User views product page",
                "User adds item to cart",
                "User completes purchase",
            ],
            "action": ["view", "add_to_cart", "purchase"],
            "action_label": [0, 1, 2],
            "persona_vec": [[0.5] * 12, [0.5] * 12, [0.6] * 12],
            "rationale": ["Browsing options", "Good price", None],
            "context": ['{"price": 29.99}', '{"price": 29.99}', '{"price": 199.99}'],
        }

        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(suffix=".parquet", delete=False)
        df.to_parquet(temp_file.name, index=False)
        return temp_file.name

    def test_dataset_load(self, sample_parquet):
        """Test dataset loading."""
        dataset = OPeRADataset(sample_parquet, max_seq_len=120, max_rationale_len=60)
        assert len(dataset) == 3

    def test_dataset_getitem(self, sample_parquet):
        """Test dataset item retrieval."""
        dataset = OPeRADataset(sample_parquet, max_seq_len=120, max_rationale_len=60)
        item = dataset[0]

        assert "seq_tokens" in item
        assert "rationale_tokens" in item
        assert "persona_vec" in item
        assert "catalog_vec" in item
        assert "action_label" in item
        assert "user_id" in item
        assert "session_id" in item
        assert "t" in item

        # Check shapes
        assert item["seq_tokens"].shape[0] == 120
        assert item["rationale_tokens"].shape[0] == 60
        assert item["persona_vec"].shape[0] == 12
        assert item["catalog_vec"].shape[0] == 10

    def test_dataset_vocab(self, sample_parquet):
        """Test vocabulary building."""
        dataset = OPeRADataset(sample_parquet)
        vocab = dataset.get_vocab()

        assert "<PAD>" in vocab
        assert "<UNK>" in vocab
        assert vocab["<PAD>"] == 0
        assert vocab["<UNK>"] == 1
        assert len(vocab) > 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

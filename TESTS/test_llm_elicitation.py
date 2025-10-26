from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from src.ssr.llm_elicitation import (
    LLMElicitationEngine,
    persona_vec_to_demographics,
)


class TestDemographicFormatting:
    """Test demographic formatting for LLM prompts."""

    def test_format_demographics_full(self):
        """Test formatting with all demographic attributes."""
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)

        demo_text = engine.format_demographics(
            age_bracket=2,  # 35-44
            gender="M",
            income_bracket=3,  # $62,500
            education="bachelor",
        )

        assert "39-year-old" in demo_text or "40-year-old" in demo_text  # Midpoint of 35-44
        assert "male" in demo_text
        assert "$62,500" in demo_text
        assert "bachelor" in demo_text

    def test_format_demographics_age_only(self):
        """Test with age bracket only."""
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)

        demo_text = engine.format_demographics(age_bracket=1)  # 25-34

        assert "29-year-old" in demo_text or "30-year-old" in demo_text

    def test_format_demographics_gender_mapping(self):
        """Test gender encoding mappings."""
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)

        # String encoding
        male_text = engine.format_demographics(gender="M")
        assert "male" in male_text

        female_text = engine.format_demographics(gender="F")
        assert "female" in female_text

        # Numeric encoding
        male_num_text = engine.format_demographics(gender=0)
        assert "male" in male_num_text

    def test_format_demographics_empty(self):
        """Test with no demographics provided."""
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)

        demo_text = engine.format_demographics()

        assert "person" in demo_text

    def test_format_demographics_income_brackets(self):
        """Test income bracket mappings."""
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)

        low_income = engine.format_demographics(income_bracket=0)
        assert "$25,000" in low_income

        high_income = engine.format_demographics(income_bracket=6)
        assert "$175,000" in high_income


class TestPersonaVectorConversion:
    """Test conversion from 12-D persona vector to demographics."""

    def test_persona_vec_to_demographics_valid(self):
        """Test extracting demographics from 12-D persona vector."""
        # OPeRA structure: [OCEAN(5) + Psychographic(4) + Demographic(3)]
        age_norm = (38 - 18) / 82  # ~35-44 bracket
        income_norm = 62_500 / 200_000
        persona_vec = [
            # OCEAN traits (indices 0-4)
            0.6, 0.7, 0.5, 0.8, 0.4,
            # Psychographic (indices 5-8)
            0.9, 0.2, 0.6, 0.5,
            # Demographic (indices 9-11)
            age_norm,
            1.0,  # gender normalised (male)
            income_norm,
        ]

        demographics = persona_vec_to_demographics(persona_vec)

        assert demographics["age_bracket"] == 2
        assert demographics["gender"] == 0
        assert demographics["income_bracket"] == 3
        assert 37 <= demographics["age_estimate"] <= 39
        assert 60_000 <= demographics["income_estimate"] <= 65_000

    def test_persona_vec_to_demographics_invalid_length(self):
        """Vector must be at least 12-D."""
        short_vec = [0.5, 0.6, 0.7]  # Only 3-D

        with pytest.raises(ValueError, match="must be 12-D"):
            persona_vec_to_demographics(short_vec)

    def test_persona_vec_to_demographics_longer_vec(self):
        """Should work with vectors longer than 12-D (extract first 12)."""
        long_vec = list(range(20))  # 20-D vector

        demographics = persona_vec_to_demographics(long_vec)

        assert demographics["age_bracket"] == 5  # clipped to 65+
        assert demographics["gender"] == 0  # male after clipping
        assert demographics["income_bracket"] == 6


class TestPromptCreation:
    """Test LLM prompt creation."""

    def test_create_elicitation_prompt_purchase_intent(self):
        """Test purchase intent prompt template."""
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)

        prompt = engine.create_elicitation_prompt(
            stimulus_text="Free shipping on orders over $50",
            demographics={"age_bracket": 2, "gender": "M", "income_bracket": 3},
            prompt_template="purchase_intent",
        )

        assert "Free shipping on orders over $50" in prompt
        assert "male" in prompt.lower()
        assert "$62,500" in prompt
        assert "feel about this offer" in prompt.lower()

    def test_create_elicitation_prompt_value_perception(self):
        """Test value perception prompt template."""
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)

        prompt = engine.create_elicitation_prompt(
            stimulus_text="20% off laptops",
            demographics={"age_bracket": 1, "income_bracket": 2},
            prompt_template="value_perception",
        )

        assert "20% off laptops" in prompt
        assert "value" in prompt.lower()
        assert "income" in prompt.lower()

    def test_create_elicitation_prompt_generic(self):
        """Test generic fallback prompt."""
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)

        prompt = engine.create_elicitation_prompt(
            stimulus_text="Premium quality electronics",
            demographics={},
            prompt_template="generic",
        )

        assert "Premium quality electronics" in prompt
        assert "honest feelings" in prompt.lower()


class TestLLMElicitation:
    """Test LLM elicitation with mocked API."""

    @patch("openai.OpenAI")
    def test_elicit_response_success(self, mock_openai):
        """Test successful LLM elicitation."""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This offer looks great for my budget!"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Create engine
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)
        engine.client = mock_client

        # Elicit response
        result = engine.elicit_response(
            stimulus_text="20% off",
            demographics={"age_bracket": 2, "gender": "M"},
        )

        # Verify result structure
        assert result["responses"] == ["This offer looks great for my budget!"]
        assert result["response"] == "This offer looks great for my budget!"
        assert "prompt" in result
        assert "model" in result
        assert result["generation_params"]["samples_per_prompt"] == 1
        assert "demographics" in result
        assert "stimulus" in result

        # Verify content
        assert result["stimulus"] == "20% off"
        assert result["demographics"]["age_bracket"] == 2

        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs["n"] == 1
        assert kwargs["temperature"] == 0.5

    @patch("openai.OpenAI")
    def test_elicit_response_multiple_samples(self, mock_openai):
        """Ensure multiple samples are returned when requested."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Sample A")),
            MagicMock(message=MagicMock(content="Sample B")),
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=2)
        engine.client = mock_client

        result = engine.elicit_response(
            stimulus_text="Bundle offer",
            demographics={"age_bracket": 1},
        )

        assert result["responses"] == ["Sample A", "Sample B"]
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["n"] == 2

    @patch("openai.OpenAI")
    def test_elicit_response_with_temperature_zero(self, mock_openai):
        """Ensure temperature=0 for deterministic responses."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Deterministic response"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        engine = LLMElicitationEngine(api_key="test-key", temperature=0.0, samples_per_prompt=1)
        engine.client = mock_client

        engine.elicit_response("Test", {})

        # Check that temperature=0 was passed to API
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.0

    @patch("openai.OpenAI")
    def test_elicit_response_error_fallback(self, mock_openai):
        """Test fallback response on API error."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai.return_value = mock_client

        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)
        engine.client = mock_client

        result = engine.elicit_response(
            stimulus_text="Free shipping",
            demographics={},
            retry_on_error=False,  # Don't retry to avoid recursion
        )

        # Should return fallback response
        assert result["model"] == "fallback"
        assert "error" in result
        assert result["stimulus"] in result["responses"][0]

    def test_initialization_without_api_key(self):
        """Should raise error if no API key provided."""
        # Ensure OPENAI_API_KEY is not set
        old_key = os.environ.pop("OPENAI_API_KEY", None)

        try:
            with pytest.raises(ValueError, match="API key required"):
                LLMElicitationEngine(samples_per_prompt=1)

        finally:
            # Restore old key if it existed
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-test-key"})
    @patch("openai.OpenAI")
    def test_initialization_from_env(self, mock_openai):
        """Should read API key from environment."""
        mock_openai.return_value = MagicMock()

        engine = LLMElicitationEngine(samples_per_prompt=1)

        # Should have initialized successfully with env key
        assert engine.model == "gpt-4o-mini"
        assert engine.temperature == 0.5

    @patch("openai.OpenAI")
    def test_elicit_batch(self, mock_openai):
        """Test batch elicitation."""
        mock_client = MagicMock()

        # Mock different responses for each call
        responses = [
            "Response 1",
            "Response 2",
            "Response 3",
        ]

        def mock_create(*args, **kwargs):
            response = MagicMock()
            response.choices = [
                MagicMock(message=MagicMock(content=responses.pop(0)))
            ]
            return response

        mock_client.chat.completions.create.side_effect = mock_create
        mock_openai.return_value = mock_client

        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)
        engine.client = mock_client

        # Batch of stimuli
        batch = [
            {"stimulus": "Free shipping", "demographics": {"age_bracket": 2}},
            {"stimulus": "20% off", "demographics": {"age_bracket": 3}},
            {"stimulus": "Premium quality", "demographics": {"age_bracket": 1}},
        ]

        results = engine.elicit_batch(batch, show_progress=False)

        # Verify results
        assert len(results) == 3
        assert results[0]["responses"][0] == "Response 1"
        assert results[1]["responses"][0] == "Response 2"
        assert results[2]["responses"][0] == "Response 3"

        # Verify all had correct stimuli
        assert results[0]["stimulus"] == "Free shipping"
        assert results[1]["stimulus"] == "20% off"
        assert results[2]["stimulus"] == "Premium quality"


class TestIntegrationScenario:
    """Integration test for complete SSR elicitation workflow."""

    @patch("openai.OpenAI")
    def test_end_to_end_elicitation_workflow(self, mock_openai):
        """
        Simulate complete workflow:
        1. Extract demographics from persona vector
        2. Create elicitation prompt
        3. Get LLM response
        4. Verify response structure for SSR training
        """
        # Mock LLM
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="As a budget-conscious shopper, I find this offer very appealing!"
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Step 1: Start with OPeRA persona vector
        age_norm = (40 - 18) / 82  # Mid 30s-40s
        income_norm = 62_500 / 200_000
        persona_vec = [
            0.6, 0.7, 0.5, 0.8, 0.4,  # OCEAN
            0.9, 0.2, 0.6, 0.5,  # Psychographic (high thrift)
            age_norm, 1.0, income_norm,  # Demographics (age≈40, male, income≈$62.5K)
        ]

        # Step 2: Extract demographics
        demographics = persona_vec_to_demographics(persona_vec)

        # Step 3: Elicit LLM response
        engine = LLMElicitationEngine(api_key="test-key", samples_per_prompt=1)
        engine.client = mock_client

        result = engine.elicit_response(
            stimulus_text="Free shipping on orders over $25",
            demographics=demographics,
        )

        # Step 4: Verify result ready for SSR training
        assert result["responses"]  # Has text response(s)
        assert result["demographics"]  # Has demographic context
        assert result["stimulus"]  # Has original stimulus

        # Demographics should influence prompt
        assert "$62,500" in result["prompt"]  # Income bucket from persona vector
        assert "male" in result["prompt"].lower()  # Gender from persona_vec[10]

        # Response should be suitable for embedding
        first_response = result["responses"][0]
        assert len(first_response) > 10  # Not trivially short
        assert isinstance(first_response, str)

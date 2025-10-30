"""
LLM Gateway for airline twin decisions.
Phase 4: OpenAI/Anthropic API integration with retry logic and validation.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMGateway:
    """
    Gateway for calling LLM APIs (OpenAI or Anthropic) with retry logic.
    """

    def __init__(self, config_path: Path):
        """
        Initialize LLM gateway.

        Args:
            config_path: Path to twin_config.yaml
        """
        self.config = self._load_config(config_path)
        self.llm_config = self.config["llm"]

        # API settings
        self.provider = self.llm_config["provider"]
        self.model = self.llm_config["model"]
        self.temperature = self.llm_config["temperature"]
        self.top_p = self.llm_config["top_p"]
        self.max_tokens = self.llm_config["max_tokens"]
        self.seed = self.llm_config.get("seed", 42)
        self.timeout = self.llm_config.get("timeout", 30)

        # Initialize API client
        self.client = self._init_client()

        logger.info(f"LLMGateway initialized: provider={self.provider}, model={self.model}")

    def _load_config(self, config_path: Path) -> dict:
        """Load configuration from YAML."""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _init_client(self):
        """Initialize API client based on provider."""
        if self.provider == "openai":
            return self._init_openai()
        elif self.provider == "anthropic":
            return self._init_anthropic()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not found in environment. "
                    "Please set it: export OPENAI_API_KEY=your_key"
                )

            client = OpenAI(api_key=api_key, timeout=self.timeout)
            logger.info("OpenAI client initialized")
            return client

        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not found in environment. "
                    "Please set it: export ANTHROPIC_API_KEY=your_key"
                )

            client = Anthropic(api_key=api_key, timeout=self.timeout)
            logger.info("Anthropic client initialized")
            return client

        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        seed: Optional[int] = None,
        use_json_mode: bool = True
    ) -> Tuple[str, Dict]:
        """
        Call LLM API and return response.

        Args:
            system_prompt: System prompt (twin profile + instructions)
            user_prompt: User prompt (offer details + context)
            seed: Optional seed for determinism
            use_json_mode: Whether to use JSON response format (default True)

        Returns:
            Tuple of (response_text, metadata)
        """
        if seed is None:
            seed = self.seed

        if self.provider == "openai":
            return self._call_openai(system_prompt, user_prompt, seed, use_json_mode)
        elif self.provider == "anthropic":
            return self._call_anthropic(system_prompt, user_prompt, seed)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        seed: int,
        use_json_mode: bool = True
    ) -> Tuple[str, Dict]:
        """Call OpenAI API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # OpenAI call parameters
        call_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "seed": seed,
        }

        # Add response format for JSON mode if supported and requested
        if use_json_mode and ("gpt-4" in self.model or "gpt-3.5" in self.model):
            call_params["response_format"] = {"type": "json_object"}

        logger.debug(f"Calling OpenAI: model={self.model}, seed={seed}")

        try:
            response = self.client.chat.completions.create(**call_params)

            response_text = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            metadata = {
                "provider": "openai",
                "model": self.model,
                "finish_reason": finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "seed": seed
            }

            logger.debug(f"OpenAI response: {len(response_text)} chars, finish={finish_reason}")

            return response_text, metadata

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        seed: int
    ) -> Tuple[str, Dict]:
        """Call Anthropic API."""
        logger.debug(f"Calling Anthropic: model={self.model}")

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response_text = response.content[0].text

            metadata = {
                "provider": "anthropic",
                "model": self.model,
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

            logger.debug(f"Anthropic response: {len(response_text)} chars")

            return response_text, metadata

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def call_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 2,
        seed: Optional[int] = None
    ) -> Tuple[str, Dict]:
        """
        Call LLM with retry logic on failure.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_retries: Maximum number of retries
            seed: Optional seed

        Returns:
            Tuple of (response_text, metadata)
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response_text, metadata = self.call_llm(system_prompt, user_prompt, seed)
                metadata["attempt"] = attempt + 1
                return response_text, metadata

            except Exception as e:
                last_error = e
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")

                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        # All retries failed
        logger.error(f"LLM call failed after {max_retries + 1} attempts")
        raise last_error

    def parse_decision_response(self, response_text: str) -> Dict:
        """
        Parse JSON decision response from LLM.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed decision dict with keys: decision, probability, rationale

        Raises:
            ValueError: If response is not valid JSON or missing required fields
        """
        # Try to parse JSON
        try:
            response_data = json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            raise ValueError(f"Invalid JSON response: {e}")

        # Validate required fields
        required_fields = ["decision", "probability", "rationale"]
        missing_fields = [f for f in required_fields if f not in response_data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate decision value
        decision = response_data["decision"].lower()
        if decision not in ["yes", "no"]:
            raise ValueError(f"Invalid decision value: {decision} (must be 'yes' or 'no')")

        # Validate probability
        try:
            probability = float(response_data["probability"])
            if not (0.0 <= probability <= 1.0):
                raise ValueError(f"Probability out of range: {probability}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid probability: {response_data['probability']}")

        # Validate rationale
        rationale = str(response_data["rationale"]).strip()
        if not rationale or len(rationale) < 10:
            raise ValueError("Rationale too short or empty")

        return {
            "decision": decision,
            "probability": probability,
            "rationale": rationale
        }

    def get_decision(
        self,
        system_prompt: str,
        user_prompt: str,
        seed: Optional[int] = None,
        max_retries: int = 2
    ) -> Tuple[Dict, Dict]:
        """
        High-level method to get a validated decision from LLM.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            seed: Optional seed
            max_retries: Max retries for API calls

        Returns:
            Tuple of (decision_dict, metadata)
        """
        # Call LLM with retry
        response_text, metadata = self.call_with_retry(
            system_prompt,
            user_prompt,
            max_retries=max_retries,
            seed=seed
        )

        # Try to parse decision
        try:
            decision = self.parse_decision_response(response_text)
            metadata["parse_success"] = True
            return decision, metadata

        except ValueError as e:
            logger.error(f"Failed to parse decision: {e}")

            # If we have retries left, try once more
            if max_retries > 0:
                logger.info("Retrying with explicit JSON instruction...")

                # Add explicit JSON reminder to user prompt
                user_prompt_retry = user_prompt + "\n\nREMINDER: Respond with ONLY valid JSON, no other text."

                response_text, metadata = self.call_with_retry(
                    system_prompt,
                    user_prompt_retry,
                    max_retries=1,
                    seed=seed
                )

                decision = self.parse_decision_response(response_text)
                metadata["parse_success"] = True
                metadata["retry_with_reminder"] = True
                return decision, metadata

            # No retries, raise error
            metadata["parse_success"] = False
            metadata["parse_error"] = str(e)
            raise


def main():
    """Test LLM gateway."""
    # Paths
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "CONFIGS" / "airline" / "twin_config.yaml"

    # Initialize gateway
    logger.info("Initializing LLM Gateway...")
    gateway = LLMGateway(config_path)

    # Simple test
    system_prompt = "You are a helpful assistant that responds in JSON."
    user_prompt = """
    Answer this question in JSON format:
    {"answer": "yes or no", "reason": "brief explanation"}

    Question: Is the sky blue?
    """

    logger.info("Testing LLM call...")
    try:
        decision, metadata = gateway.get_decision(system_prompt, user_prompt)
        logger.info(f"✅ Decision: {decision}")
        logger.info(f"✅ Metadata: {metadata}")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main()

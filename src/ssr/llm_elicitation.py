from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import numpy as np
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMElicitationEngine:
    """
    LLM-based textual elicitation for SSR (Semantic Similarity Rating).

    Implements demographic conditioning as described in the paper:
    "LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation".

    Elicits persona-conditioned free-text responses, optionally drawing multiple
    samples per prompt, and records generation parameters for reproducibility.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 100,
        samples_per_prompt: int = 2,
        provider: str = "openai",
        seed: Optional[int] = None,
    ):
        """
        Args:
            model: Model identifier understood by the chosen provider.
            api_key: Optional API key. Falls back to provider-specific env var.
            temperature: Sampling temperature (paper uses ≈0.5).
            max_tokens: Maximum tokens to generate per completion.
            samples_per_prompt: Number of completions to draw per persona/concept.
            provider: "openai" (default) or "google" (Gemini family).
            seed: Optional base seed for deterministic sampling (if provider supports).
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.samples_per_prompt = samples_per_prompt
        self.provider = provider.lower()
        self.base_seed = seed

        if self.samples_per_prompt < 1:
            raise ValueError("samples_per_prompt must be >= 1")

        if self.provider == "openai":
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY or pass api_key."
                )
            self.client = openai.OpenAI(api_key=key)

        elif self.provider in {"google", "gemini"}:
            key = api_key or os.getenv("GOOGLE_API_KEY")
            if not key:
                raise ValueError(
                    "Google API key required for provider='google'. "
                    "Set GOOGLE_API_KEY or pass api_key."
                )
            try:
                import google.generativeai as genai  # type: ignore[import]
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise ImportError(
                    "google-generativeai must be installed to use provider='google'. "
                    "Install via `pip install google-generativeai`."
                ) from exc

            genai.configure(api_key=key)
            self.client = genai.GenerativeModel(model_name=model)
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unsupported provider '{provider}'.")

        logger.info(
            "LLM engine initialised (provider=%s, model=%s, temperature=%.2f, samples=%d)",
            self.provider,
            self.model,
            self.temperature,
            self.samples_per_prompt,
        )

    # ------------------------------------------------------------------ #
    # Prompt construction helpers
    # ------------------------------------------------------------------ #

    def format_demographics(
        self,
        age_bracket: Optional[int] = None,
        gender: Optional[str] = None,
        income_bracket: Optional[int] = None,
        education: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Format demographic attributes into natural language prompt scaffolding.

        The paper found age & income conditioning particularly impactful.
        """
        age_map = {
            0: "18-24",
            1: "25-34",
            2: "35-44",
            3: "45-54",
            4: "55-64",
            5: "65+",
        }

        income_map = {
            0: "$25,000",
            1: "$37,500",
            2: "$50,000",
            3: "$62,500",
            4: "$87,500",
            5: "$125,000",
            6: "$175,000",
        }

        gender_map = {
            "M": "male",
            "F": "female",
            "O": "non-binary",
            0: "male",
            1: "female",
            2: "non-binary",
        }

        education_map = {
            "high_school": "a high school diploma",
            "bachelor": "a bachelor's degree",
            "graduate": "a graduate degree",
            0: "a high school diploma",
            1: "some college education",
            2: "a bachelor's degree",
            3: "a graduate degree",
        }

        parts: List[str] = []

        if age_bracket is not None:
            age_range = age_map.get(age_bracket, "adult")
            if isinstance(age_range, str) and "-" in age_range:
                start, end = [int(x) for x in age_range.split("-")]
                midpoint = (start + end) // 2
                parts.append(f"a {midpoint}-year-old")
            else:
                parts.append(str(age_range))

        if gender is not None:
            parts.append(gender_map.get(gender, "person"))

        description = " ".join(parts) if parts else "a person"

        if income_bracket is not None:
            income_text = income_map.get(income_bracket, "$50,000")
            description += f" with an annual income around {income_text}"

        if education is not None:
            description += f" and {education_map.get(education, 'some education')}"

        return description

    def create_elicitation_prompt(
        self,
        stimulus_text: str,
        demographics: Dict,
        prompt_template: str = "purchase_intent",
    ) -> str:
        """Construct a persona-conditioned prompt."""
        demo_description = self.format_demographics(**demographics)

        if prompt_template == "purchase_intent":
            return (
                f"You are {demo_description}. "
                f"You are considering an e-commerce offer: \"{stimulus_text}\".\n\n"
                "In 1-2 sentences, honestly express how you feel about this offer. "
                "Consider your demographics and preferences. Be natural and conversational."
            )

        if prompt_template == "value_perception":
            return (
                f"You are {demo_description}. "
                f"You see this product offer: \"{stimulus_text}\".\n\n"
                "In 1-2 sentences, describe the value of this offer given your situation."
            )

        return (
            f"You are {demo_description}. "
            f"React to: \"{stimulus_text}\".\n\n"
            "Share your honest feelings in 1-2 sentences."
        )

    # ------------------------------------------------------------------ #
    # Generation entry points
    # ------------------------------------------------------------------ #

    def elicit_response(
        self,
        stimulus_text: str,
        demographics: Dict,
        prompt_template: str = "purchase_intent",
        retry_on_error: bool = True,
        *,
        samples_per_prompt: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Generate one or more persona-conditioned responses.

        Returns a dictionary containing the list of generated responses and metadata.
        """
        prompt = self.create_elicitation_prompt(
            stimulus_text, demographics, prompt_template
        )

        requested_samples = samples_per_prompt or self.samples_per_prompt
        call_temperature = temperature if temperature is not None else self.temperature
        call_seed = seed if seed is not None else self.base_seed

        try:
            if self.provider == "openai":
                responses = self._generate_openai(
                    prompt=prompt,
                    samples=requested_samples,
                    temperature=call_temperature,
                    seed=call_seed,
                )
            else:
                responses = self._generate_google(
                    prompt=prompt,
                    samples=requested_samples,
                    temperature=call_temperature,
                    seed=call_seed,
                )

            if not responses:
                raise RuntimeError("No responses returned by provider.")

            logger.debug("Elicited %d response(s); first=%s", len(responses), responses[0][:100])

            return {
                "responses": responses,
                "response": responses[0],
                "prompt": prompt,
                "model": self.model,
                "provider": self.provider,
                "demographics": demographics,
                "stimulus": stimulus_text,
                "generation_params": {
                    "samples_per_prompt": requested_samples,
                    "temperature": call_temperature,
                    "seed": call_seed,
                    "max_tokens": self.max_tokens,
                },
            }

        except Exception as exc:
            logger.error("LLM elicitation failed: %s", exc)

            if retry_on_error:
                logger.info("Retrying elicitation once without retry flag...")
                return self.elicit_response(
                    stimulus_text,
                    demographics,
                    prompt_template,
                    retry_on_error=False,
                    samples_per_prompt=requested_samples,
                    temperature=call_temperature,
                    seed=call_seed,
                )

            fallback = f"I would consider this offer: {stimulus_text}"
            return {
                "responses": [fallback],
                "response": fallback,
                "prompt": prompt,
                "model": "fallback",
                "provider": self.provider,
                "demographics": demographics,
                "stimulus": stimulus_text,
                "error": str(exc),
                "generation_params": {
                    "samples_per_prompt": requested_samples,
                    "temperature": call_temperature,
                    "seed": call_seed,
                    "max_tokens": self.max_tokens,
                },
            }

    def elicit_batch(
        self,
        stimuli_and_demographics: List[Dict],
        prompt_template: str = "purchase_intent",
        show_progress: bool = True,
        *,
        samples_per_prompt: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> List[Dict]:
        """Batch version of :meth:`elicit_response` with optional progress logging."""
        results: List[Dict] = []

        if show_progress:
            try:
                from tqdm import tqdm

                iterator = tqdm(stimuli_and_demographics, desc="Eliciting responses")
            except ImportError:  # pragma: no cover - optional dependency
                logger.warning("tqdm not available, progress bar disabled")
                iterator = stimuli_and_demographics
        else:
            iterator = stimuli_and_demographics

        base_seed = seed if seed is not None else self.base_seed

        for idx, item in enumerate(iterator):
            stimulus = item["stimulus"]
            demographics = item["demographics"]
            item_seed = base_seed + idx if base_seed is not None else None

            result = self.elicit_response(
                stimulus,
                demographics,
                prompt_template,
                samples_per_prompt=samples_per_prompt,
                temperature=temperature,
                seed=item_seed,
            )
            results.append(result)

        logger.info("Elicited %d prompts (%d total responses).", len(results), sum(len(r["responses"]) for r in results))
        return results

    # ------------------------------------------------------------------ #
    # Provider-specific helpers
    # ------------------------------------------------------------------ #

    def _generate_openai(
        self,
        prompt: str,
        samples: int,
        temperature: float,
        seed: Optional[int],
    ) -> List[str]:
        """Generate completions using OpenAI Chat Completions API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are roleplaying as a real person with specific demographics. "
                        "Respond naturally and honestly based on the persona described. "
                        "Keep responses concise (1-2 sentences)."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=self.max_tokens,
            n=samples,
            seed=seed,
        )

        return [
            choice.message.content.strip()
            for choice in response.choices
            if choice.message and choice.message.content
        ]

    def _generate_google(
        self,
        prompt: str,
        samples: int,
        temperature: float,
        seed: Optional[int],
    ) -> List[str]:
        """Generate completions using Google Generative AI (Gemini) SDK."""
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": self.max_tokens,
            "candidate_count": samples,
        }
        request_options = {"seed": seed} if seed is not None else None

        response = self.client.generate_content(
            prompt,
            generation_config=generation_config,
            request_options=request_options,
        )

        candidates = getattr(response, "candidates", None)
        if not candidates:
            text = getattr(response, "text", None)
            return [text.strip()] if text else []

        texts: List[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            # Each candidate content may consist of multiple parts with text segments.
            parts = getattr(content, "parts", None)
            if not parts:
                continue
            fragments = [getattr(part, "text", "") for part in parts]
            candidate_text = " ".join(fragment.strip() for fragment in fragments if fragment)
            if candidate_text:
                texts.append(candidate_text)

        return texts


def persona_vec_to_demographics(persona_vec: List[float]) -> Dict:
    """
    Convert the 12-D persona vector (OCEAN + psychographic + demographic)
    into discrete demographic attributes suitable for prompting.

    Expected layout (from OPeRA pipeline):
        indices 0-4  -> OCEAN traits
        indices 5-8  -> Psychographic indicators
        indices 9-11 -> Demographic signals (age, gender, income) in [0, 1]
    """
    if len(persona_vec) < 12:
        raise ValueError(f"Persona vector must be 12-D, got {len(persona_vec)}")

    age_norm = float(np.clip(persona_vec[9], 0.0, 1.0))
    gender_norm = float(np.clip(persona_vec[10], 0.0, 1.0))
    income_norm = float(np.clip(persona_vec[11], 0.0, 1.0))

    estimated_age = 18 + age_norm * 82  # Map back to ~18-100 years
    if estimated_age < 25:
        age_bracket = 0
    elif estimated_age < 35:
        age_bracket = 1
    elif estimated_age < 45:
        age_bracket = 2
    elif estimated_age < 55:
        age_bracket = 3
    elif estimated_age < 65:
        age_bracket = 4
    else:
        age_bracket = 5

    if gender_norm >= 0.75:
        gender_bucket = 0  # male
    elif gender_norm >= 0.25:
        gender_bucket = 1  # female
    else:
        gender_bucket = 2  # non-binary / other

    estimated_income = income_norm * 200_000
    if estimated_income < 30_000:
        income_bracket = 0
    elif estimated_income < 45_000:
        income_bracket = 1
    elif estimated_income < 60_000:
        income_bracket = 2
    elif estimated_income < 80_000:
        income_bracket = 3
    elif estimated_income < 110_000:
        income_bracket = 4
    elif estimated_income < 160_000:
        income_bracket = 5
    else:
        income_bracket = 6

    return {
        "age_bracket": age_bracket,
        "age_estimate": round(estimated_age, 1),
        "gender": gender_bucket,
        "income_bracket": income_bracket,
        "income_estimate": round(estimated_income, 2),
    }

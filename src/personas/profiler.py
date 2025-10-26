from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PersonaProfiler:
    """
    Generate human-readable persona descriptions using LLM summarization.

    Uses GPT-4o-mini to create natural language descriptions from cluster statistics.
    """

    def __init__(self, openai_api_key: Optional[str] = None, use_llm: bool = True):
        self.use_llm = use_llm
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if self.use_llm and not self.openai_api_key:
            logger.warning(
                "OpenAI API key not found. Set OPENAI_API_KEY env var or pass to constructor."
            )
            self.use_llm = False

    def generate_persona_description(
        self,
        cluster_profile: Dict[str, Any],
        sample_users: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Generate persona label and description from cluster profile.

        Args:
            cluster_profile: Dict with ocean_scores, psychographic_tags, demographics
            sample_users: Optional list of sample user IDs for context

        Returns:
            Dict with "id", "label", "description"
        """
        cluster_id = cluster_profile["cluster_id"]

        if self.use_llm:
            return self._generate_with_llm(cluster_profile, sample_users)
        else:
            return self._generate_template_based(cluster_profile)

    def _generate_with_llm(
        self,
        cluster_profile: Dict[str, Any],
        sample_users: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Generate persona description using GPT-4o-mini."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.openai_api_key)

            # Build prompt
            ocean = cluster_profile["ocean_scores"]
            tags = cluster_profile.get("psychographic_tags", [])
            demo = cluster_profile.get("demographics", {})
            size = cluster_profile.get("size", 0)

            prompt = f"""You are a marketing researcher analyzing e-commerce shopper personas.

Based on the following behavioral and psychological data, create a concise persona profile:

**Cluster Statistics:**
- Cluster size: {size} users
- OCEAN Personality Scores (0-1 scale):
  - Openness: {ocean.get('O', 0.5):.2f}
  - Conscientiousness: {ocean.get('C', 0.5):.2f}
  - Extraversion: {ocean.get('E', 0.5):.2f}
  - Agreeableness: {ocean.get('A', 0.5):.2f}
  - Neuroticism: {ocean.get('N', 0.5):.2f}

- Psychographic Tags: {', '.join(tags) if tags else 'general shopper'}

- Demographics:
  - Age (normalized): {demo.get('age_norm', 0.5):.2f}
  - Income (normalized): {demo.get('income_norm', 0.5):.2f}

**Task:**
1. Create a short, memorable persona label (3-5 words, e.g., "The Deal Seeker", "Premium Quality Buyer")
2. Write a 1-2 sentence description capturing their shopping behavior and motivations

**Output format (JSON):**
{{
  "label": "The [Persona Name]",
  "description": "Brief description of shopping behavior and motivations."
}}

Keep it concise, actionable, and focused on e-commerce behavior."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150,
                response_format={"type": "json_object"},
            )

            import json

            result = json.loads(response.choices[0].message.content)
            label = result.get("label", f"Persona {cluster_profile['cluster_id']}")
            description = result.get("description", "E-commerce shopper")

            # Generate persona ID
            persona_id = self._generate_persona_id(label, cluster_profile["cluster_id"])

            logger.info(f"Generated LLM persona: {persona_id} - {label}")
            return {
                "id": persona_id,
                "label": label,
                "description": description,
            }

        except Exception as e:
            logger.error(f"LLM generation failed: {e}. Falling back to template.")
            return self._generate_template_based(cluster_profile)

    def _generate_template_based(self, cluster_profile: Dict[str, Any]) -> Dict[str, str]:
        """Generate persona description using templates (no API calls)."""
        cluster_id = cluster_profile["cluster_id"]
        ocean = cluster_profile["ocean_scores"]
        tags = cluster_profile.get("psychographic_tags", [])
        demo = cluster_profile.get("demographics", {})

        # Determine dominant traits
        dominant_traits = []

        if "price_sensitive" in tags:
            dominant_traits.append("budget-conscious")
        if "quality_focused" in tags:
            dominant_traits.append("quality-driven")
        if "spontaneous" in tags:
            dominant_traits.append("impulsive")
        if "analytical" in tags:
            dominant_traits.append("methodical")

        # OCEAN-based traits
        if ocean.get("O", 0.5) > 0.6:
            dominant_traits.append("explorative")
        if ocean.get("C", 0.5) > 0.6:
            dominant_traits.append("planful")
        if ocean.get("E", 0.5) > 0.6:
            dominant_traits.append("social")

        # Income-based
        income_norm = demo.get("income_norm", 0.5)
        if income_norm > 0.7:
            income_desc = "high-income"
        elif income_norm < 0.3:
            income_desc = "budget"
        else:
            income_desc = "mid-range"

        # Generate label and description
        if "price_sensitive" in tags or income_norm < 0.4:
            label = "The Deal Seeker"
            description = "Price-sensitive shopper who compares prices extensively and waits for sales."
        elif "quality_focused" in tags or income_norm > 0.7:
            label = "The Premium Buyer"
            description = "Quality-focused shopper willing to pay more for trusted brands and superior products."
        elif "spontaneous" in tags:
            label = "The Impulse Buyer"
            description = "Makes quick purchasing decisions based on emotional appeal and immediate gratification."
        elif "analytical" in tags:
            label = "The Research-Oriented Shopper"
            description = "Thoroughly researches products, reads reviews, and makes data-driven purchasing decisions."
        else:
            label = f"Persona Group {cluster_id + 1}"
            description = f"E-commerce shopper with {', '.join(dominant_traits[:3]) if dominant_traits else 'balanced'} shopping preferences."

        persona_id = self._generate_persona_id(label, cluster_id)

        logger.info(f"Generated template persona: {persona_id} - {label}")
        return {
            "id": persona_id,
            "label": label,
            "description": description,
        }

    def _generate_persona_id(self, label: str, cluster_id: int) -> str:
        """Generate persona ID from label."""
        # Extract key words from label
        words = label.lower().replace("the ", "").strip().split()
        # Use first 2-3 words, underscore-separated
        id_parts = "_".join(words[:3])
        # Add cluster ID prefix
        return f"p{cluster_id:02d}_{id_parts}"

    def enrich_persona_profile(
        self,
        persona: Dict[str, str],
        cluster_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrich persona with full profile data.

        Args:
            persona: Dict with id, label, description
            cluster_profile: Full cluster statistics

        Returns:
            Complete persona profile.
        """
        return {
            **persona,
            "cluster_id": cluster_profile["cluster_id"],
            "size": cluster_profile["size"],
            "centroid": cluster_profile["centroid"],
            "ocean_scores": cluster_profile["ocean_scores"],
            "psychographic_tags": cluster_profile["psychographic_tags"],
            "demographics": cluster_profile["demographics"],
            "mean_probability": cluster_profile["mean_probability"],
        }

    def generate_all_personas(
        self,
        cluster_profiles: List[Dict[str, Any]],
        sample_users_map: Optional[Dict[int, List[str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate personas for all clusters.

        Args:
            cluster_profiles: List of cluster profile dicts
            sample_users_map: Optional dict mapping cluster_id -> sample user IDs

        Returns:
            List of enriched persona profiles.
        """
        personas = []

        for profile in cluster_profiles:
            cluster_id = profile["cluster_id"]
            sample_users = (
                sample_users_map.get(cluster_id) if sample_users_map else None
            )

            # Generate description
            persona_desc = self.generate_persona_description(profile, sample_users)

            # Enrich with full profile
            persona_full = self.enrich_persona_profile(persona_desc, profile)

            personas.append(persona_full)

        logger.info(f"Generated {len(personas)} complete persona profiles")
        return personas

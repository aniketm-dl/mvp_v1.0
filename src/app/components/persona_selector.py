from __future__ import annotations

from typing import List, Optional

import streamlit as st


class PersonaSelector:
    """
    UI component for selecting and displaying personas.

    Allows users to filter predictions by persona or view persona details.
    """

    def __init__(self, personas: Optional[List[dict]] = None):
        """
        Initialize persona selector.

        Args:
            personas: List of persona dicts from persona_profiles.json
        """
        self.personas = personas or []

    def render(self) -> Optional[dict]:
        """
        Render persona selector dropdown.

        Returns:
            Selected persona dict or None if "All Users" selected
        """
        if not self.personas:
            st.info("ℹ️ No personas available. Predicting for all users.")
            return None

        options = ["All Users"] + [p.get("label", f"Persona {p['id']}") for p in self.personas]

        selected = st.selectbox(
            "Filter by Persona (Optional)",
            options,
            help="Select a persona to condition predictions, or choose 'All Users' for general predictions",
        )

        if selected == "All Users":
            return None

        # Find selected persona
        for persona in self.personas:
            if persona.get("label") == selected:
                return persona

        return None

    def render_persona_details(self):
        """Render detailed persona information in expanders."""
        if not self.personas:
            st.warning("No personas to display")
            return

        st.markdown(f"**Total Personas:** {len(self.personas)}")
        st.divider()

        for persona in self.personas:
            persona_id = persona.get("id", "unknown")
            label = persona.get("label", f"Persona {persona_id}")
            description = persona.get("description", "No description available")
            cluster_size = persona.get("cluster_size", 0)

            with st.expander(f"**{label}** (ID: {persona_id}, Size: {cluster_size} users)"):
                st.markdown(f"**Description:**\n{description}")

                # Display cluster profile
                if "cluster_profile" in persona:
                    st.markdown("**Cluster Profile:**")
                    profile = persona["cluster_profile"]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Demographics:**")
                        demo = profile.get("demographics", {})
                        st.metric("Age (mean)", f"{demo.get('age_mean', 0):.1f}")
                        st.metric("Income (mean)", f"${demo.get('income_mean', 0):.0f}")

                        gender_dist = demo.get("gender_distribution", {})
                        if gender_dist:
                            st.markdown("**Gender Distribution:**")
                            for gender, pct in gender_dist.items():
                                st.text(f"  {gender}: {pct:.1%}")

                    with col2:
                        st.markdown("**Psychographics (OCEAN):**")
                        ocean = profile.get("ocean", {})
                        for trait, value in ocean.items():
                            st.metric(trait.capitalize(), f"{value:.2f}")

                # Display psychographic tags if available
                if "psychographic_tags" in profile:
                    tags = profile["psychographic_tags"]
                    if tags:
                        st.markdown("**Psychographic Tags:**")
                        st.write(", ".join(tags))

    def render_persona_card(self, persona: dict):
        """
        Render compact persona card.

        Args:
            persona: Persona dict
        """
        label = persona.get("label", f"Persona {persona['id']}")
        description = persona.get("description", "")
        cluster_size = persona.get("cluster_size", 0)

        st.markdown(
            f"""
            <div class="metric-box">
                <h4>{label}</h4>
                <p><strong>Size:</strong> {cluster_size} users</p>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

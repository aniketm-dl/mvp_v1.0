from __future__ import annotations

from typing import List

import streamlit as st


class ScenarioBuilder:
    """
    UI component for building and managing multiple scenarios.

    Allows users to add, edit, and remove scenarios for comparison.
    """

    def __init__(self):
        """Initialize scenario builder."""
        if "scenarios" not in st.session_state:
            st.session_state.scenarios = []

    def render(self) -> List[dict]:
        """
        Render scenario builder interface.

        Returns:
            List of scenario dicts with 'id' and 'text' fields
        """
        st.markdown("**Build Scenarios to Compare:**")

        # Scenario input form
        with st.form("add_scenario_form"):
            scenario_text = st.text_input(
                "Scenario Text",
                placeholder="e.g., 'Free shipping', '50% off', 'Premium quality'",
            )
            submit = st.form_submit_button("Add Scenario", type="primary")

            if submit and scenario_text.strip():
                scenario_id = f"scenario_{len(st.session_state.scenarios) + 1}"
                st.session_state.scenarios.append({
                    "id": scenario_id,
                    "text": scenario_text.strip(),
                })

        # Display current scenarios
        if st.session_state.scenarios:
            st.markdown(f"**Current Scenarios ({len(st.session_state.scenarios)}):**")

            for i, scenario in enumerate(st.session_state.scenarios):
                col1, col2 = st.columns([5, 1])

                with col1:
                    st.markdown(f"**{i+1}.** {scenario['text']}")

                with col2:
                    if st.button("🗑️", key=f"delete_{scenario['id']}", help="Remove scenario"):
                        st.session_state.scenarios.pop(i)
                        st.rerun()

            # Clear all button
            if st.button("Clear All Scenarios", type="secondary"):
                st.session_state.scenarios = []
                st.rerun()

        else:
            st.info("No scenarios added yet. Add your first scenario above.")

        return st.session_state.scenarios

    def render_with_templates(self) -> List[dict]:
        """
        Render scenario builder with example templates.

        Returns:
            List of scenario dicts
        """
        # Template examples
        st.markdown("**Quick Templates:**")
        templates = {
            "Discount": "20% off all orders this weekend",
            "Free Shipping": "Free shipping on orders over $50",
            "Bundle Deal": "Buy 2 get 1 free on select items",
            "Premium": "Premium quality products with lifetime warranty",
            "Urgency": "Limited time offer - ends tonight!",
        }

        cols = st.columns(len(templates))
        for i, (name, text) in enumerate(templates.items()):
            with cols[i]:
                if st.button(name, key=f"template_{name}", use_container_width=True):
                    scenario_id = f"scenario_{len(st.session_state.scenarios) + 1}"
                    st.session_state.scenarios.append({
                        "id": scenario_id,
                        "text": text,
                    })
                    st.rerun()

        st.divider()

        return self.render()

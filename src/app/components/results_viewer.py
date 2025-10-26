from __future__ import annotations

from typing import Dict, List

import numpy as np
import plotly.graph_objects as go
import streamlit as st


class ResultsViewer:
    """
    UI component for displaying SSR prediction results.

    Renders predictions, distributions, and comparison charts.
    """

    def render_single_prediction(self, prediction_data: dict):
        """
        Render results for a single prediction.

        Args:
            prediction_data: Dict with 'stimulus', 'prediction', and optional 'persona'
        """
        stimulus = prediction_data.get("stimulus", "")
        prediction = prediction_data.get("prediction", {})
        persona = prediction_data.get("persona")

        st.markdown("---")
        st.header("📊 Prediction Results")

        # Display input
        st.markdown("**Input Scenario:**")
        st.code(stimulus, language="text")

        if persona:
            st.markdown(f"**Persona:** {persona.get('label', 'Unknown')}")

        # Display metrics
        st.markdown("### Key Metrics")
        col1, col2, col3, col4 = st.columns(4)

        mean_rating = prediction.get("mean", 0)
        std_rating = prediction.get("std", 0)
        mode_rating = prediction.get("mode", 0)
        distribution = prediction.get("distribution", [])

        with col1:
            st.metric("Mean Rating", f"{mean_rating:.2f}", help="Expected rating (1-5)")

        with col2:
            st.metric("Std Dev", f"±{std_rating:.2f}", help="Rating variability")

        with col3:
            st.metric("Mode", f"{mode_rating}", help="Most likely rating")

        with col4:
            confidence = max(distribution) if distribution else 0
            st.metric("Confidence", f"{confidence:.1%}", help="Probability of mode")

        # Distribution chart
        if distribution:
            st.markdown("### Rating Distribution")
            fig = self._create_distribution_chart(distribution, mean_rating, mode_rating)
            st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        st.markdown("### Interpretation")
        interpretation = self._interpret_rating(mean_rating, std_rating, confidence)
        st.markdown(
            f"""
            <div class="{'success-box' if mean_rating >= 4 else 'warning-box' if mean_rating >= 3 else 'metric-box'}">
                {interpretation}
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render_scenario_comparison(self, comparison_data: dict):
        """
        Render comparison of multiple scenarios.

        Args:
            comparison_data: Dict with 'scenarios' list
        """
        scenarios = comparison_data.get("scenarios", [])

        if not scenarios:
            st.warning("No scenarios to compare")
            return

        st.markdown("---")
        st.header("📊 Scenario Comparison")

        # Comparison table
        st.markdown("### Summary Table")
        table_data = []
        for scenario in scenarios:
            pred = scenario["prediction"]
            table_data.append({
                "Scenario": scenario["text"][:50] + ("..." if len(scenario["text"]) > 50 else ""),
                "Mean Rating": f"{pred['mean']:.2f}",
                "Std Dev": f"±{pred['std']:.2f}",
                "Mode": pred["mode"],
            })

        st.table(table_data)

        # Comparison bar chart
        st.markdown("### Mean Rating Comparison")
        fig = self._create_comparison_chart(scenarios)
        st.plotly_chart(fig, use_container_width=True)

        # Distribution comparison
        st.markdown("### Distribution Comparison")
        fig = self._create_multi_distribution_chart(scenarios)
        st.plotly_chart(fig, use_container_width=True)

        # Winner analysis
        st.markdown("### Best Performing Scenario")
        best_scenario = max(scenarios, key=lambda s: s["prediction"]["mean"])
        st.markdown(
            f"""
            <div class="success-box">
                <strong>🏆 Winner:</strong> {best_scenario['text']}<br>
                <strong>Mean Rating:</strong> {best_scenario['prediction']['mean']:.2f}<br>
                <strong>Mode:</strong> {best_scenario['prediction']['mode']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _create_distribution_chart(
        self, distribution: List[float], mean: float, mode: int
    ) -> go.Figure:
        """Create bar chart for Likert distribution."""
        likert_values = ["1", "2", "3", "4", "5"]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=likert_values,
                    y=distribution,
                    marker_color="steelblue",
                    text=[f"{p:.1%}" for p in distribution],
                    textposition="outside",
                )
            ]
        )

        # Highlight mode
        colors = [
            "orange" if i + 1 == mode else "steelblue"
            for i in range(len(distribution))
        ]
        fig.data[0].marker.color = colors

        fig.update_layout(
            xaxis_title="Likert Rating",
            yaxis_title="Probability",
            yaxis_range=[0, max(distribution) * 1.2],
            showlegend=False,
            height=400,
        )

        return fig

    def _create_comparison_chart(self, scenarios: List[dict]) -> go.Figure:
        """Create bar chart comparing mean ratings."""
        ids = [s["id"] for s in scenarios]
        means = [s["prediction"]["mean"] for s in scenarios]

        # Color by rating quality
        colors = [
            "green" if m >= 4 else "orange" if m >= 3 else "red"
            for m in means
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=ids,
                    y=means,
                    marker_color=colors,
                    text=[f"{m:.2f}" for m in means],
                    textposition="outside",
                )
            ]
        )

        fig.update_layout(
            xaxis_title="Scenario",
            yaxis_title="Mean Rating",
            yaxis_range=[1, 5],
            showlegend=False,
            height=400,
        )

        return fig

    def _create_multi_distribution_chart(self, scenarios: List[dict]) -> go.Figure:
        """Create grouped bar chart for multiple distributions."""
        likert_values = ["1", "2", "3", "4", "5"]

        fig = go.Figure()

        for scenario in scenarios:
            distribution = scenario["prediction"]["distribution"]
            fig.add_trace(
                go.Bar(
                    x=likert_values,
                    y=distribution,
                    name=scenario["id"],
                )
            )

        fig.update_layout(
            xaxis_title="Likert Rating",
            yaxis_title="Probability",
            barmode="group",
            height=500,
        )

        return fig

    def _interpret_rating(self, mean: float, std: float, confidence: float) -> str:
        """Generate human-readable interpretation."""
        if mean >= 4.5:
            sentiment = "**Excellent** 🎉"
            desc = "Users are highly likely to respond very positively to this scenario."
        elif mean >= 4.0:
            sentiment = "**Very Good** ✅"
            desc = "Users are likely to respond positively."
        elif mean >= 3.5:
            sentiment = "**Good** 👍"
            desc = "Users are moderately positive about this scenario."
        elif mean >= 3.0:
            sentiment = "**Neutral** 😐"
            desc = "Users have mixed feelings about this scenario."
        elif mean >= 2.0:
            sentiment = "**Below Average** 👎"
            desc = "Users are likely to respond negatively."
        else:
            sentiment = "**Poor** ❌"
            desc = "Users are very unlikely to respond positively."

        uncertainty = ""
        if std > 1.0:
            uncertainty = " **High variability** suggests diverse user opinions."
        elif confidence >= 0.5:
            uncertainty = f" **High confidence** ({confidence:.0%}) in the prediction."

        return f"{sentiment}: {desc}{uncertainty}"

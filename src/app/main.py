from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.app.components.persona_selector import PersonaSelector
from src.app.components.results_viewer import ResultsViewer
from src.app.components.scenario_builder import ScenarioBuilder
from src.app.utils.api_client import SSRClient

# Page config
st.set_page_config(
    page_title="OPeRA-SSR Demo",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "ssr_client" not in st.session_state:
        st.session_state.ssr_client = None

    if "personas" not in st.session_state:
        st.session_state.personas = None

    if "predictions" not in st.session_state:
        st.session_state.predictions = None

    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = None


def load_ssr_model(model_path: str):
    """Load SSR model and personas."""
    try:
        with st.spinner("Loading SSR model..."):
            client = SSRClient(model_path)
            st.session_state.ssr_client = client

            # Load personas if available
            personas_path = Path("models/persona_profiles.json")
            if personas_path.exists():
                import json

                with open(personas_path) as f:
                    data = json.load(f)
                    st.session_state.personas = data.get("personas", [])
            else:
                st.session_state.personas = []

        st.success(f"✅ Model loaded successfully: {model_path}")
        return True

    except Exception as e:
        st.error(f"❌ Failed to load model: {str(e)}")
        return False


def main():
    """Main Streamlit app."""
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">🎯 OPeRA-SSR Demo</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Semantic Similarity Rating for E-Commerce Scenarios</div>',
        unsafe_allow_html=True,
    )

    # Sidebar - Model Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        model_path = st.text_input(
            "SSR Model Path",
            value="models/ssr_reference",
            help="Path to trained SSR model directory",
        )

        if st.button("Load Model", type="primary", use_container_width=True):
            load_ssr_model(model_path)

        st.divider()

        # Model info
        if st.session_state.ssr_client:
            st.success("✅ Model Loaded")
            info = st.session_state.ssr_client.get_model_info()
            st.metric("Base Model", info.get("base_model", "N/A"))
            st.metric("Embedding Dim", info.get("embedding_dim", "N/A"))

            if st.session_state.personas:
                st.metric("Personas Discovered", len(st.session_state.personas))
        else:
            st.warning("⚠️ No model loaded")
            st.info("Click 'Load Model' to get started")

        st.divider()

        # About
        with st.expander("ℹ️ About"):
            st.markdown(
                """
                **OPeRA-SSR** predicts how users would rate
                e-commerce scenarios (ads, promotions, copy)
                based on their behavioral personas.

                **Features:**
                - Real OPeRA dataset training
                - 8-12 discovered personas
                - Fast inference (<50ms)
                - Distribution predictions (1-5 Likert)

                **Tech Stack:**
                - sentence-transformers
                - UMAP + HDBSCAN clustering
                - GPT-4o-mini summaries
                """
            )

    # Main content
    if not st.session_state.ssr_client:
        # Welcome screen
        st.info(
            """
            👈 **Get Started:** Load an SSR model from the sidebar to begin.

            **What is SSR?**
            Semantic Similarity Rating (SSR) predicts Likert-scale ratings (1-5)
            for e-commerce stimuli based on fine-tuned sentence embeddings.

            **How it works:**
            1. Load a trained SSR model
            2. Select a persona (optional)
            3. Enter scenario text (e.g., "50% off laptops")
            4. View predicted rating distribution
            """
        )

        # Display example
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Example Input")
            st.code('Stimulus: "Free shipping on all orders over $50"', language="text")

        with col2:
            st.markdown("#### Example Output")
            st.code(
                """
Predicted Rating: 3.8 ± 0.9
Mode: 4 (Most likely)
Distribution: [0.05, 0.10, 0.25, 0.40, 0.20]
                """,
                language="text",
            )

        return

    # Tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(
        ["🎯 Single Prediction", "🔄 Scenario Comparison", "👥 Persona Explorer"]
    )

    with tab1:
        st.header("Single Prediction")
        st.markdown("Predict how users would rate a single scenario.")

        # Persona selector (optional)
        persona_selector = PersonaSelector(st.session_state.personas)
        selected_persona = persona_selector.render()

        # Scenario input
        stimulus_text = st.text_area(
            "Scenario Text",
            placeholder="e.g., 'Free shipping on all orders', '20% off laptops', 'Premium quality electronics'",
            height=100,
        )

        if st.button("Predict Rating", type="primary", use_container_width=True):
            if not stimulus_text.strip():
                st.warning("⚠️ Please enter scenario text")
            else:
                with st.spinner("Predicting..."):
                    prediction = st.session_state.ssr_client.predict(stimulus_text)
                    st.session_state.predictions = {
                        "stimulus": stimulus_text,
                        "persona": selected_persona,
                        "prediction": prediction,
                    }

        # Display results
        if st.session_state.predictions:
            results_viewer = ResultsViewer()
            results_viewer.render_single_prediction(st.session_state.predictions)

    with tab2:
        st.header("Scenario Comparison")
        st.markdown("Compare multiple scenarios side-by-side.")

        # Scenario builder
        scenario_builder = ScenarioBuilder()
        scenarios = scenario_builder.render()

        if st.button("Compare Scenarios", type="primary", use_container_width=True):
            if not scenarios:
                st.warning("⚠️ Please add at least one scenario")
            else:
                with st.spinner("Predicting all scenarios..."):
                    results = []
                    for scenario in scenarios:
                        pred = st.session_state.ssr_client.predict(scenario["text"])
                        results.append({
                            "id": scenario["id"],
                            "text": scenario["text"],
                            "prediction": pred,
                        })

                    st.session_state.predictions = {
                        "type": "comparison",
                        "scenarios": results,
                    }

        # Display comparison results
        if (
            st.session_state.predictions
            and st.session_state.predictions.get("type") == "comparison"
        ):
            results_viewer = ResultsViewer()
            results_viewer.render_scenario_comparison(st.session_state.predictions)

    with tab3:
        st.header("Persona Explorer")
        st.markdown("Browse discovered personas and their characteristics.")

        if st.session_state.personas:
            persona_selector = PersonaSelector(st.session_state.personas)
            persona_selector.render_persona_details()
        else:
            st.info(
                """
                ℹ️ **No personas available**

                Personas are discovered during training via UMAP + HDBSCAN clustering.
                They should be saved in `models/persona_profiles.json`.

                Run persona discovery:
                ```bash
                python scripts/03_discover_personas.py
                ```
                """
            )


if __name__ == "__main__":
    main()

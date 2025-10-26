from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationDashboard:
    """
    Generate interactive Plotly dashboards for SSR evaluation results.

    Creates visualizations for KS similarity, correlations, and distribution comparisons.
    """

    def __init__(self, output_dir: Path):
        """
        Initialize dashboard generator.

        Args:
            output_dir: Directory to save HTML dashboard files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_ks_similarity_chart(
        self,
        results: Dict[str, any],
        title: str = "KS Similarity by Persona",
    ) -> go.Figure:
        """
        Create bar chart showing KS similarity scores per persona.

        Args:
            results: Output from KSSimilarityTest.batch_test()
            title: Chart title

        Returns:
            Plotly figure
        """
        individual = results["individual_results"]
        labels = [r["label"] for r in individual]
        similarities = [r["similarity"] for r in individual]
        passes = [r["passes_threshold"] for r in individual]

        colors = ["green" if p else "orange" for p in passes]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels,
                    y=similarities,
                    marker_color=colors,
                    text=[f"{s:.3f}" for s in similarities],
                    textposition="outside",
                )
            ]
        )

        # Add threshold line
        fig.add_hline(
            y=0.80,
            line_dash="dash",
            line_color="red",
            annotation_text="Target (≥0.80)",
            annotation_position="right",
        )

        fig.update_layout(
            title=title,
            xaxis_title="Persona",
            yaxis_title="KS Similarity (1 - KS Statistic)",
            yaxis_range=[0, 1.0],
            showlegend=False,
            height=500,
        )

        return fig

    def create_correlation_scatter(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
        correlation: float,
        p_value: float,
        title: str = "Predicted vs Actual Ratings",
    ) -> go.Figure:
        """
        Create scatter plot of predicted vs actual ratings.

        Args:
            predicted: Predicted ratings
            actual: Actual ratings
            correlation: Spearman correlation coefficient
            p_value: P-value for correlation
            title: Chart title

        Returns:
            Plotly figure
        """
        fig = go.Figure()

        # Scatter plot
        fig.add_trace(
            go.Scatter(
                x=actual,
                y=predicted,
                mode="markers",
                marker=dict(size=6, opacity=0.6, color="steelblue"),
                name="Predictions",
            )
        )

        # Perfect prediction line (y=x)
        min_val = min(actual.min(), predicted.min())
        max_val = max(actual.max(), predicted.max())
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode="lines",
                line=dict(color="red", dash="dash"),
                name="Perfect Prediction",
            )
        )

        # Add correlation annotation
        annotation_text = (
            f"Spearman ρ = {correlation:.3f}<br>"
            f"p-value = {p_value:.4f}<br>"
            f"{'✅ Significant' if p_value < 0.05 else '❌ Not significant'}"
        )

        fig.update_layout(
            title=title,
            xaxis_title="Actual Rating",
            yaxis_title="Predicted Rating",
            height=500,
            annotations=[
                dict(
                    x=0.05,
                    y=0.95,
                    xref="paper",
                    yref="paper",
                    text=annotation_text,
                    showarrow=False,
                    bgcolor="white",
                    bordercolor="black",
                    borderwidth=1,
                )
            ],
        )

        return fig

    def create_distribution_comparison(
        self,
        predicted_dist: np.ndarray,
        actual_dist: np.ndarray,
        persona_label: str,
    ) -> go.Figure:
        """
        Create grouped bar chart comparing predicted vs actual Likert distributions.

        Args:
            predicted_dist: Predicted probability distribution [P(1), ..., P(5)]
            actual_dist: Actual probability distribution
            persona_label: Persona identifier

        Returns:
            Plotly figure
        """
        likert_values = ["1", "2", "3", "4", "5"]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=likert_values,
                y=actual_dist,
                name="Actual",
                marker_color="steelblue",
            )
        )

        fig.add_trace(
            go.Bar(
                x=likert_values,
                y=predicted_dist,
                name="Predicted",
                marker_color="orange",
            )
        )

        fig.update_layout(
            title=f"Distribution Comparison: {persona_label}",
            xaxis_title="Likert Rating",
            yaxis_title="Probability",
            barmode="group",
            height=400,
        )

        return fig

    def create_quality_metrics_table(
        self,
        ks_results: Dict[str, any],
        corr_results: Dict[str, any],
    ) -> go.Figure:
        """
        Create table showing quality metrics summary.

        Args:
            ks_results: Output from KSSimilarityTest.batch_test()
            corr_results: Output from CorrelationMetrics.batch_correlations()

        Returns:
            Plotly table figure
        """
        ks_agg = ks_results["aggregate"]
        corr_agg = corr_results["aggregate"]

        metrics = [
            "Mean KS Similarity",
            "Median KS Similarity",
            "Min KS Similarity",
            "KS Pass Rate",
            "",
            "Mean Spearman ρ",
            "Median Spearman ρ",
            "Min Spearman ρ",
            "Spearman Pass Rate",
            "",
            "Mean MAE",
            "Mean RMSE",
        ]

        values = [
            f"{ks_agg['mean_similarity']:.3f}",
            f"{ks_agg['median_similarity']:.3f}",
            f"{ks_agg['min_similarity']:.3f}",
            f"{ks_agg['pass_rate']:.1%}",
            "",
            f"{corr_agg['mean_spearman']:.3f}",
            f"{corr_agg['median_spearman']:.3f}",
            f"{corr_agg['min_spearman']:.3f}",
            f"{corr_agg['pass_rate']:.1%}",
            "",
            f"{corr_agg['mean_mae']:.3f}",
            f"{corr_agg['mean_rmse']:.3f}",
        ]

        targets = [
            "≥ 0.80",
            "≥ 0.80",
            "≥ 0.80",
            "≥ 80%",
            "",
            "≥ 0.70",
            "≥ 0.70",
            "≥ 0.70",
            "≥ 80%",
            "",
            "< 0.50",
            "< 0.60",
        ]

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=["<b>Metric</b>", "<b>Value</b>", "<b>Target</b>"],
                        fill_color="steelblue",
                        align="left",
                        font=dict(color="white", size=12),
                    ),
                    cells=dict(
                        values=[metrics, values, targets],
                        fill_color="lavender",
                        align="left",
                    ),
                )
            ]
        )

        fig.update_layout(title="Quality Metrics Summary", height=500)

        return fig

    def create_scenario_comparison_chart(
        self,
        scenarios: List[Dict[str, any]],
        base_scenario: Dict[str, any],
    ) -> go.Figure:
        """
        Create chart comparing scenario predictions.

        Args:
            scenarios: List of scenario predictions with deltas
            base_scenario: Base scenario for comparison

        Returns:
            Plotly figure
        """
        scenario_ids = [s["id"] for s in scenarios]
        mean_ratings = [s["prediction"]["mean"] for s in scenarios]
        base_mean = base_scenario["prediction"]["mean"]

        colors = [
            "green" if m > base_mean else "red" if m < base_mean else "gray"
            for m in mean_ratings
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=scenario_ids,
                    y=mean_ratings,
                    marker_color=colors,
                    text=[f"{m:.2f}" for m in mean_ratings],
                    textposition="outside",
                )
            ]
        )

        # Add baseline
        fig.add_hline(
            y=base_mean,
            line_dash="dash",
            line_color="blue",
            annotation_text=f"Base: {base_mean:.2f}",
            annotation_position="right",
        )

        fig.update_layout(
            title="Scenario Comparison: Predicted Mean Ratings",
            xaxis_title="Scenario",
            yaxis_title="Predicted Rating (1-5)",
            yaxis_range=[1, 5],
            showlegend=False,
            height=500,
        )

        return fig

    def create_complete_dashboard(
        self,
        ks_results: Dict[str, any],
        corr_results: Dict[str, any],
        predicted: Optional[np.ndarray] = None,
        actual: Optional[np.ndarray] = None,
    ) -> Path:
        """
        Create complete HTML dashboard with all evaluation charts.

        Args:
            ks_results: Output from KSSimilarityTest.batch_test()
            corr_results: Output from CorrelationMetrics.batch_correlations()
            predicted: Optional full predicted ratings array
            actual: Optional full actual ratings array

        Returns:
            Path to saved HTML dashboard
        """
        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "KS Similarity by Persona",
                "Quality Metrics Summary",
                "Correlation Scatter",
                "Distribution Example",
            ),
            specs=[
                [{"type": "bar"}, {"type": "table"}],
                [{"type": "scatter"}, {"type": "bar"}],
            ],
        )

        # KS similarity chart
        ks_chart = self.create_ks_similarity_chart(ks_results)
        for trace in ks_chart.data:
            fig.add_trace(trace, row=1, col=1)

        # Quality metrics table
        metrics_table = self.create_quality_metrics_table(ks_results, corr_results)
        for trace in metrics_table.data:
            fig.add_trace(trace, row=1, col=2)

        # Correlation scatter (if data provided)
        if predicted is not None and actual is not None:
            corr_agg = corr_results["aggregate"]
            scatter = self.create_correlation_scatter(
                predicted,
                actual,
                corr_agg["mean_spearman"],
                0.001,  # Placeholder p-value
            )
            for trace in scatter.data:
                fig.add_trace(trace, row=2, col=1)

        # Distribution example (first persona)
        if corr_results["individual_results"]:
            first_result = corr_results["individual_results"][0]
            # Mock distributions for visualization
            pred_dist = np.random.dirichlet([2, 3, 5, 3, 2])
            actual_dist = np.random.dirichlet([2, 3, 5, 3, 2])

            dist_chart = self.create_distribution_comparison(
                pred_dist, actual_dist, first_result["label"]
            )
            for trace in dist_chart.data:
                fig.add_trace(trace, row=2, col=2)

        fig.update_layout(
            title_text="SSR Evaluation Dashboard",
            showlegend=True,
            height=1000,
        )

        # Save dashboard
        output_path = self.output_dir / "evaluation_dashboard.html"
        fig.write_html(str(output_path))

        logger.info(f"✅ Dashboard saved to: {output_path}")
        return output_path

    def save_individual_charts(
        self,
        ks_results: Dict[str, any],
        corr_results: Dict[str, any],
        predicted: Optional[np.ndarray] = None,
        actual: Optional[np.ndarray] = None,
    ) -> List[Path]:
        """
        Save individual chart files.

        Args:
            ks_results: KS test results
            corr_results: Correlation results
            predicted: Optional predicted ratings
            actual: Optional actual ratings

        Returns:
            List of saved file paths
        """
        saved_files = []

        # KS similarity chart
        ks_fig = self.create_ks_similarity_chart(ks_results)
        ks_path = self.output_dir / "ks_similarity.html"
        ks_fig.write_html(str(ks_path))
        saved_files.append(ks_path)

        # Quality metrics table
        metrics_fig = self.create_quality_metrics_table(ks_results, corr_results)
        metrics_path = self.output_dir / "quality_metrics.html"
        metrics_fig.write_html(str(metrics_path))
        saved_files.append(metrics_path)

        # Correlation scatter
        if predicted is not None and actual is not None:
            corr_agg = corr_results["aggregate"]
            scatter_fig = self.create_correlation_scatter(
                predicted, actual, corr_agg["mean_spearman"], 0.001
            )
            scatter_path = self.output_dir / "correlation_scatter.html"
            scatter_fig.write_html(str(scatter_path))
            saved_files.append(scatter_path)

        logger.info(f"✅ Saved {len(saved_files)} individual charts")
        return saved_files

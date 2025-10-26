#!/usr/bin/env python3
"""
Sprint Review Report Generator

Generates comprehensive sprint review reports after each development cycle,
including persona quality assessments, version comparisons, and recommendations
for the next sprint.

Usage:
    # Generate report for a completed sprint
    python scripts/generate_sprint_report.py --sprint "Sprint 1" --version v1.0
    
    # Generate report comparing two versions
    python scripts/generate_sprint_report.py --sprint "Sprint 2" --version v2.0 --previous v1.0
    
    # Output to specific directory
    python scripts/generate_sprint_report.py --sprint "Sprint 1" --version v1.0 --output reports/sprints/
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

console = Console()


@dataclass
class SprintReport:
    """Complete sprint review report"""
    sprint_name: str
    version: str
    previous_version: Optional[str]
    start_date: str
    end_date: str
    
    # Goals and achievements
    sprint_goals: List[str]
    achievements: List[str]
    challenges: List[str]
    
    # Quality metrics
    overall_quality_score: float
    quality_gate_status: str
    persona_count: int
    
    # Metrics
    key_metrics: Dict[str, float]
    metric_changes: Dict[str, float]
    
    # Per-persona results
    persona_results: List[Dict[str, Any]]
    
    # Recommendations
    improvements: List[str]
    regressions: List[str]
    next_sprint_recommendations: List[str]
    
    # Technical details
    training_details: Dict[str, Any]
    evaluation_summary: Dict[str, Any]
    
    timestamp: str


class SprintReportGenerator:
    """Generate comprehensive sprint review reports"""
    
    def __init__(self, sprint_name: str, version: str, previous_version: Optional[str] = None):
        self.sprint_name = sprint_name
        self.version = version
        self.previous_version = previous_version
        
        # Load data
        self.evaluation = self._load_evaluation(version)
        self.previous_evaluation = self._load_evaluation(previous_version) if previous_version else None
        self.version_metadata = self._load_version_metadata(version)
        
        console.print(f"\n[bold cyan]📊 Generating Sprint Report: {sprint_name}[/bold cyan]")
        console.print(f"Version: {version}")
        if previous_version:
            console.print(f"Previous: {previous_version}\n")
    
    def _load_evaluation(self, version: str) -> Optional[Dict]:
        """Load evaluation results for a version"""
        if not version:
            return None
        
        eval_dir = Path("reports/persona_evaluation")
        if not eval_dir.exists():
            return None
        
        eval_files = list(eval_dir.glob(f"{version}_*.json"))
        if not eval_files:
            console.print(f"[yellow]⚠️  No evaluation found for {version}[/yellow]")
            return None
        
        latest_eval = sorted(eval_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        
        with open(latest_eval, 'r') as f:
            return json.load(f)
    
    def _load_version_metadata(self, version: str) -> Optional[Dict]:
        """Load version metadata"""
        metadata_path = Path(f"trained_models/{version}/metadata/model_inventory.json")
        if not metadata_path.exists():
            return {}
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def generate_report(self) -> SprintReport:
        """Generate complete sprint report"""
        
        if not self.evaluation:
            console.print("[red]❌ Cannot generate report without evaluation data[/red]")
            console.print(f"Run: python scripts/persona_assessment.py --version {self.version}")
            sys.exit(1)
        
        # Extract data
        agg_metrics = self.evaluation.get('aggregate_metrics', {})
        persona_evals = self.evaluation.get('persona_evaluations', [])
        
        # Determine quality gate status
        quality_gates_passed = self.evaluation.get('quality_gates_passed', False)
        quality_gate_status = "✅ PASSED" if quality_gates_passed else "❌ FAILED"
        
        # Get metric changes if previous version available
        metric_changes = {}
        improvements = []
        regressions = []
        
        if self.previous_evaluation:
            prev_agg = self.previous_evaluation.get('aggregate_metrics', {})
            
            for metric, value in agg_metrics.items():
                if metric in prev_agg:
                    prev_value = prev_agg[metric]
                    if prev_value != 0:
                        change = ((value - prev_value) / prev_value) * 100
                        metric_changes[metric] = change
                        
                        if change > 2:
                            improvements.append(f"{metric}: +{change:.1f}%")
                        elif change < -2:
                            regressions.append(f"{metric}: {change:.1f}%")
        
        # Extract persona results
        persona_results = []
        for p_eval in persona_evals:
            persona_results.append({
                'id': p_eval['persona_id'],
                'label': p_eval['persona_label'],
                'score': p_eval['overall_score'],
                'metrics': {
                    name: result['score']
                    for name, result in p_eval['metrics'].items()
                }
            })
        
        # Sort by score
        persona_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Training details
        training_details = {
            'base_model': self.version_metadata.get('base_model', 'Unknown'),
            'training_config': self.version_metadata.get('training_config', {}),
            'download_date': self.version_metadata.get('download_date', 'Unknown'),
            'training_completion': self.version_metadata.get('training_completion', 'Unknown')
        }
        
        # Evaluation summary
        evaluation_summary = {
            'timestamp': self.evaluation.get('timestamp', 'Unknown'),
            'total_personas': len(persona_evals),
            'evaluation_time': sum(p['evaluation_time'] for p in persona_evals) if persona_evals else 0
        }
        
        # Generate recommendations
        next_sprint_recommendations = self._generate_recommendations(
            agg_metrics,
            persona_results,
            improvements,
            regressions
        )
        
        # Identify achievements and challenges
        achievements, challenges = self._identify_achievements_and_challenges(
            agg_metrics,
            improvements,
            quality_gates_passed
        )
        
        # Create report
        report = SprintReport(
            sprint_name=self.sprint_name,
            version=self.version,
            previous_version=self.previous_version,
            start_date=self.evaluation.get('timestamp', 'Unknown')[:10],
            end_date=datetime.now().isoformat()[:10],
            sprint_goals=self._get_sprint_goals(),
            achievements=achievements,
            challenges=challenges,
            overall_quality_score=agg_metrics.get('overall_score', 0.0),
            quality_gate_status=quality_gate_status,
            persona_count=len(persona_evals),
            key_metrics=agg_metrics,
            metric_changes=metric_changes,
            persona_results=persona_results,
            improvements=improvements,
            regressions=regressions,
            next_sprint_recommendations=next_sprint_recommendations,
            training_details=training_details,
            evaluation_summary=evaluation_summary,
            timestamp=datetime.now().isoformat()
        )
        
        # Display summary
        self._display_summary(report)
        
        return report
    
    def _get_sprint_goals(self) -> List[str]:
        """Get sprint goals (could be loaded from config file)"""
        # Default goals based on sprint
        if "1" in self.sprint_name:
            return [
                "Establish baseline with all 18 personas",
                "Complete training pipeline",
                "Achieve >60% overall quality score",
                "Ensure all personas are distinguishable"
            ]
        elif "2" in self.sprint_name:
            return [
                "Improve response quality >70%",
                "Enhance persona consistency",
                "Better multi-turn coherence",
                "Reduce training time"
            ]
        else:
            return [
                "Improve overall quality",
                "Optimize performance",
                "Enhance differentiation"
            ]
    
    def _identify_achievements_and_challenges(
        self,
        metrics: Dict[str, float],
        improvements: List[str],
        quality_gates_passed: bool
    ) -> tuple[List[str], List[str]]:
        """Identify sprint achievements and challenges"""
        achievements = []
        challenges = []
        
        # Check achievements
        if quality_gates_passed:
            achievements.append("✓ All quality gates passed")
        
        if metrics.get('overall_score', 0) >= 0.70:
            achievements.append("✓ Exceeded overall quality target (0.70)")
        
        if metrics.get('persona_differentiation', 0) >= 0.55:
            achievements.append("✓ Strong persona differentiation maintained")
        
        if metrics.get('pass_rate', 0) >= 0.80:
            achievements.append("✓ High metric pass rate (>80%)")
        
        if len(improvements) > len(self.evaluation.get('regressions', [])):
            achievements.append(f"✓ More improvements ({len(improvements)}) than regressions")
        
        # Check challenges
        if not quality_gates_passed:
            challenges.append("✗ Quality gates not met")
        
        if metrics.get('overall_score', 0) < 0.60:
            challenges.append("✗ Below minimum quality threshold (0.60)")
        
        if metrics.get('avg_multi_turn_coherence', 0) < 0.35:
            challenges.append("⚠️  Multi-turn coherence needs improvement")
        
        if metrics.get('avg_persona_consistency', 0) < 0.75:
            challenges.append("⚠️  Persona consistency below target")
        
        if metrics.get('std_persona_consistency', 1.0) > 0.25:
            challenges.append("⚠️  High variance in persona quality")
        
        return achievements, challenges
    
    def _generate_recommendations(
        self,
        metrics: Dict[str, float],
        persona_results: List[Dict],
        improvements: List[str],
        regressions: List[str]
    ) -> List[str]:
        """Generate recommendations for next sprint"""
        recommendations = []
        
        # Quality-based recommendations
        if metrics.get('overall_score', 0) < 0.70:
            recommendations.append(
                "🎯 Priority: Increase overall quality to >0.70 through improved training data"
            )
        
        if metrics.get('persona_differentiation', 0) < 0.55:
            recommendations.append(
                "🎯 Priority: Enhance persona differentiation with more diverse examples"
            )
        
        if metrics.get('avg_multi_turn_coherence', 0) < 0.40:
            recommendations.append(
                "📈 Focus: Add multi-turn conversation training data"
            )
        
        # Persona-specific recommendations
        weak_personas = [p for p in persona_results if p['score'] < 0.60]
        if weak_personas:
            recommendations.append(
                f"🔧 Improve: Focus on {len(weak_personas)} underperforming personas: " +
                ", ".join([p['label'] for p in weak_personas[:3]])
            )
        
        # Optimization recommendations
        if metrics.get('overall_score', 0) >= 0.70:
            recommendations.append(
                "⚡ Optimize: Consider efficiency improvements (faster inference, smaller adapters)"
            )
        
        # Continue what's working
        if improvements and not regressions:
            recommendations.append(
                "✅ Continue: Current training approach is working well"
            )
        
        if not recommendations:
            recommendations.append(
                "🎉 Excellent: All metrics look good! Focus on production readiness."
            )
        
        return recommendations
    
    def _display_summary(self, report: SprintReport):
        """Display sprint report summary"""
        # Header
        console.print("\n" + "="*80)
        console.print(Panel(
            f"[bold green]{report.sprint_name} - Complete[/bold green]\n\n"
            f"Version: {report.version}\n"
            f"Quality Score: {report.overall_quality_score:.3f}\n"
            f"Status: {report.quality_gate_status}",
            title="Sprint Summary",
            border_style="green" if "PASSED" in report.quality_gate_status else "red"
        ))
        
        # Key metrics table
        table = Table(title="Key Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", justify="right")
        if report.metric_changes:
            table.add_column("Change", justify="right")
        
        key_metrics_display = [
            ('overall_score', 'Overall Score'),
            ('avg_persona_consistency', 'Persona Consistency'),
            ('avg_response_quality', 'Response Quality'),
            ('avg_multi_turn_coherence', 'Multi-turn Coherence'),
            ('persona_differentiation', 'Differentiation'),
            ('pass_rate', 'Pass Rate')
        ]
        
        for key, name in key_metrics_display:
            value = report.key_metrics.get(key, 0.0)
            row = [name, f"{value:.3f}"]
            
            if report.metric_changes and key in report.metric_changes:
                change = report.metric_changes[key]
                color = "green" if change > 0 else "red" if change < 0 else "yellow"
                row.append(f"[{color}]{change:+.1f}%[/{color}]")
            elif report.metric_changes:
                row.append("-")
            
            table.add_row(*row)
        
        console.print("\n")
        console.print(table)
        
        # Achievements
        if report.achievements:
            console.print("\n[bold green]🎯 Achievements:[/bold green]")
            for achievement in report.achievements:
                console.print(f"  {achievement}")
        
        # Challenges
        if report.challenges:
            console.print("\n[bold yellow]⚠️  Challenges:[/bold yellow]")
            for challenge in report.challenges:
                console.print(f"  {challenge}")
        
        # Recommendations
        if report.next_sprint_recommendations:
            console.print("\n[bold cyan]📋 Next Sprint Recommendations:[/bold cyan]")
            for i, rec in enumerate(report.next_sprint_recommendations, 1):
                console.print(f"  {i}. {rec}")
        
        # Top/Bottom personas
        if report.persona_results:
            console.print("\n[bold]🏆 Top Performing Personas:[/bold]")
            for p in report.persona_results[:3]:
                console.print(f"  • {p['label']}: {p['score']:.3f}")
            
            if len(report.persona_results) > 3:
                console.print("\n[bold]⚠️  Needs Improvement:[/bold]")
                for p in report.persona_results[-3:]:
                    console.print(f"  • {p['label']}: {p['score']:.3f}")
        
        console.print("\n" + "="*80 + "\n")
    
    def save_report(self, output_dir: Path):
        """Save sprint report to files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report()
        
        # Save as JSON
        json_path = output_dir / f"{self.sprint_name.replace(' ', '_')}_{self.version}.json"
        
        # Convert report to dict
        report_dict = asdict(report)
        
        with open(json_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        console.print(f"[green]✓ JSON report saved to: {json_path}[/green]")
        
        # Save as Markdown
        md_path = output_dir / f"{self.sprint_name.replace(' ', '_')}_{self.version}.md"
        self._save_markdown_report(report, md_path)
        console.print(f"[green]✓ Markdown report saved to: {md_path}[/green]")
        
        # Save as HTML (simple)
        html_path = output_dir / f"{self.sprint_name.replace(' ', '_')}_{self.version}.html"
        self._save_html_report(report, html_path)
        console.print(f"[green]✓ HTML report saved to: {html_path}[/green]")
    
    def _save_markdown_report(self, report: SprintReport, output_path: Path):
        """Save detailed markdown report"""
        lines = [
            f"# {report.sprint_name} - Sprint Review Report",
            f"\n**Version:** {report.version}",
            f"**Date:** {report.end_date}",
            f"**Generated:** {report.timestamp}",
            f"\n## Executive Summary",
            f"\n- **Overall Quality Score:** {report.overall_quality_score:.3f}",
            f"- **Quality Gates:** {report.quality_gate_status}",
            f"- **Personas Evaluated:** {report.persona_count}",
            f"- **Improvements:** {len(report.improvements)}",
            f"- **Regressions:** {len(report.regressions)}",
        ]
        
        # Sprint goals
        if report.sprint_goals:
            lines.extend([
                f"\n## Sprint Goals",
                ""
            ])
            for goal in report.sprint_goals:
                lines.append(f"- {goal}")
        
        # Achievements
        if report.achievements:
            lines.extend([
                f"\n## Achievements ✓",
                ""
            ])
            for achievement in report.achievements:
                lines.append(f"- {achievement}")
        
        # Challenges
        if report.challenges:
            lines.extend([
                f"\n## Challenges ⚠️",
                ""
            ])
            for challenge in report.challenges:
                lines.append(f"- {challenge}")
        
        # Key metrics
        lines.extend([
            f"\n## Key Metrics",
            "\n| Metric | Score | Change |",
            "|--------|-------|--------|"
        ])
        
        for key, value in report.key_metrics.items():
            if key.startswith('avg_') or key in ['overall_score', 'pass_rate', 'persona_differentiation']:
                display_name = key.replace('avg_', '').replace('_', ' ').title()
                change_str = ""
                if key in report.metric_changes:
                    change = report.metric_changes[key]
                    emoji = "✓" if change > 0 else "✗" if change < 0 else "="
                    change_str = f"{emoji} {change:+.1f}%"
                else:
                    change_str = "-"
                
                lines.append(f"| {display_name} | {value:.3f} | {change_str} |")
        
        # Per-persona results
        lines.extend([
            f"\n## Persona Performance",
            "\n| Persona | Overall Score | Consistency | Quality | Coherence |",
            "|---------|---------------|-------------|---------|-----------|"
        ])
        
        for p in report.persona_results:
            lines.append(
                f"| {p['label']} | {p['score']:.3f} | "
                f"{p['metrics'].get('persona_consistency', 0):.3f} | "
                f"{p['metrics'].get('response_quality', 0):.3f} | "
                f"{p['metrics'].get('multi_turn_coherence', 0):.3f} |"
            )
        
        # Recommendations
        if report.next_sprint_recommendations:
            lines.extend([
                f"\n## Next Sprint Recommendations",
                ""
            ])
            for i, rec in enumerate(report.next_sprint_recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        # Training details
        lines.extend([
            f"\n## Training Details",
            f"\n- **Base Model:** {report.training_details.get('base_model', 'Unknown')}",
            f"- **Training Completion:** {report.training_details.get('training_completion', 'Unknown')}",
            f"- **Download Date:** {report.training_details.get('download_date', 'Unknown')}",
        ])
        
        config = report.training_details.get('training_config', {})
        if config:
            lines.append(f"\n### Training Configuration")
            for key, value in config.items():
                lines.append(f"- **{key}:** {value}")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
    
    def _save_html_report(self, report: SprintReport, output_path: Path):
        """Save simple HTML report"""
        status_color = "green" if "PASSED" in report.quality_gate_status else "red"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{report.sprint_name} - Sprint Review</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .metric-name {{ font-weight: bold; color: #2c3e50; }}
        .metric-value {{ float: right; font-size: 1.2em; color: #3498db; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #3498db; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .status {{ padding: 5px 15px; border-radius: 20px; color: white; font-weight: bold; }}
        .status-passed {{ background: {status_color}; }}
        .achievement {{ color: green; margin: 5px 0; }}
        .challenge {{ color: orange; margin: 5px 0; }}
        .recommendation {{ background: #e8f4f8; padding: 10px; margin: 5px 0; border-left: 4px solid #3498db; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report.sprint_name} - Sprint Review Report</h1>
        <p><strong>Version:</strong> {report.version}</p>
        <p><strong>Date:</strong> {report.end_date}</p>
        <p><strong>Status:</strong> <span class="status status-passed">{report.quality_gate_status}</span></p>
        
        <h2>Executive Summary</h2>
        <div class="metric">
            <span class="metric-name">Overall Quality Score</span>
            <span class="metric-value">{report.overall_quality_score:.3f}</span>
        </div>
        <div class="metric">
            <span class="metric-name">Personas Evaluated</span>
            <span class="metric-value">{report.persona_count}</span>
        </div>
        <div class="metric">
            <span class="metric-name">Improvements</span>
            <span class="metric-value" style="color: green;">{len(report.improvements)}</span>
        </div>
        <div class="metric">
            <span class="metric-name">Regressions</span>
            <span class="metric-value" style="color: red;">{len(report.regressions)}</span>
        </div>
        
        <h2>Achievements</h2>
        {"".join(f'<div class="achievement">✓ {a}</div>' for a in report.achievements)}
        
        <h2>Challenges</h2>
        {"".join(f'<div class="challenge">⚠️  {c}</div>' for c in report.challenges)}
        
        <h2>Key Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Score</th>
                <th>Change</th>
            </tr>
"""
        
        for key, value in report.key_metrics.items():
            if key.startswith('avg_') or key in ['overall_score', 'pass_rate', 'persona_differentiation']:
                display_name = key.replace('avg_', '').replace('_', ' ').title()
                change_str = "-"
                if key in report.metric_changes:
                    change = report.metric_changes[key]
                    change_str = f"{change:+.1f}%"
                
                html += f"""
            <tr>
                <td>{display_name}</td>
                <td>{value:.3f}</td>
                <td>{change_str}</td>
            </tr>
"""
        
        html += f"""
        </table>
        
        <h2>Next Sprint Recommendations</h2>
        {"".join(f'<div class="recommendation">{r}</div>' for r in report.next_sprint_recommendations)}
        
        <hr style="margin: 30px 0;">
        <p style="color: #7f8c8d; font-size: 0.9em;">
            Generated: {report.timestamp}<br>
            Darpan Labs - Digital Twin Persona System
        </p>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html)


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive sprint review reports"
    )
    parser.add_argument('--sprint', required=True, help='Sprint name (e.g., "Sprint 1")')
    parser.add_argument('--version', required=True, help='Version to report on (e.g., v1.0)')
    parser.add_argument('--previous', help='Previous version for comparison')
    parser.add_argument('--output', default='reports/sprints/', help='Output directory')
    
    args = parser.parse_args()
    
    generator = SprintReportGenerator(
        sprint_name=args.sprint,
        version=args.version,
        previous_version=args.previous
    )
    
    generator.save_report(Path(args.output))


if __name__ == '__main__':
    main()


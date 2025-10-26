#!/usr/bin/env python3
"""
Enhanced Version Comparison Tool with Evaluation Metrics

Compare different versions of trained persona models with comprehensive
quality metrics from automated evaluations.

Usage:
    # Compare two versions
    python scripts/compare_persona_versions.py v1.0 v2.0
    
    # Generate detailed comparison report
    python scripts/compare_persona_versions.py v1.0 v2.0 --detailed --output reports/
    
    # Show performance trends across all versions
    python scripts/compare_persona_versions.py --trend-analysis
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sys
from datetime import datetime
from dataclasses import dataclass
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

@dataclass
class VersionComparison:
    """Results of comparing two versions"""
    version1: str
    version2: str
    improvements: List[str]
    regressions: List[str]
    metric_deltas: Dict[str, float]
    recommendation: str
    timestamp: str


def load_evaluation_results(version: str) -> Optional[Dict[str, Any]]:
    """Load evaluation results for a version"""
    eval_dir = Path("reports/persona_evaluation")
    if not eval_dir.exists():
        return None
    
    # Find evaluation files for this version
    eval_files = list(eval_dir.glob(f"{version}_*.json"))
    if not eval_files:
        return None
    
    # Get most recent
    latest_eval = sorted(eval_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    
    with open(latest_eval, 'r') as f:
        return json.load(f)


def compute_metric_delta(value1: float, value2: float) -> Tuple[float, str]:
    """Compute change in metric and direction"""
    if value1 == 0:
        return 0.0, "neutral"
    
    delta = ((value2 - value1) / value1) * 100
    
    if abs(delta) < 1.0:
        direction = "neutral"
    elif delta > 0:
        direction = "improvement"
    else:
        direction = "regression"
    
    return delta, direction


def compare_versions(
    version1: str,
    version2: str,
    detailed: bool = False
) -> VersionComparison:
    """Compare two model versions"""
    console.print(f"\n[bold cyan]🔍 Comparing versions: {version1} vs {version2}[/bold cyan]\n")
    
    # Load evaluation results
    eval1 = load_evaluation_results(version1)
    eval2 = load_evaluation_results(version2)
    
    if not eval1:
        console.print(f"[red]❌ Evaluation results not found for {version1}[/red]")
        console.print(f"Run: python scripts/persona_assessment.py --version {version1}")
        return None
    
    if not eval2:
        console.print(f"[red]❌ Evaluation results not found for {version2}[/red]")
        console.print(f"Run: python scripts/persona_assessment.py --version {version2}")
        return None
    
    # Basic information
    info_text = f"""
[bold]Version 1:[/bold] {version1} ({eval1.get('timestamp', 'Unknown')[:10]})
[bold]Version 2:[/bold] {version2} ({eval2.get('timestamp', 'Unknown')[:10]})

[bold]Personas Evaluated:[/bold]
  v1: {len(eval1.get('persona_evaluations', []))}
  v2: {len(eval2.get('persona_evaluations', []))}
    """
    
    console.print(Panel(info_text, title="Comparison Overview", border_style="cyan"))
    
    # Compare metrics
    improvements = []
    regressions = []
    metric_deltas = {}
    
    console.print("\n[bold]📊 Metric Comparison:[/bold]\n")
    
    # Get aggregate metrics
    agg1 = eval1.get('aggregate_metrics', {})
    agg2 = eval2.get('aggregate_metrics', {})
    
    # Create comparison table
    table = Table(title="Quality Metric Changes")
    table.add_column("Metric", style="cyan")
    table.add_column("v1", justify="right")
    table.add_column("v2", justify="right")
    table.add_column("Δ%", justify="right")
    table.add_column("Status", justify="center")
    
    # Compare key metrics
    key_metrics = [
        ('overall_score', 'Overall Score'),
        ('avg_persona_consistency', 'Persona Consistency'),
        ('avg_response_quality', 'Response Quality'),
        ('avg_multi_turn_coherence', 'Multi-turn Coherence'),
        ('persona_differentiation', 'Persona Differentiation'),
        ('pass_rate', 'Pass Rate')
    ]
    
    for metric_key, metric_name in key_metrics:
        if metric_key in agg1 and metric_key in agg2:
            v1_val = agg1[metric_key]
            v2_val = agg2[metric_key]
            delta, direction = compute_metric_delta(v1_val, v2_val)
            
            metric_deltas[metric_key] = delta
            
            # Determine status
            if direction == "improvement":
                status = "✓"
                status_color = "green"
                improvements.append(f"{metric_name}: +{delta:.1f}%")
            elif direction == "regression":
                status = "✗"
                status_color = "red"
                regressions.append(f"{metric_name}: {delta:.1f}%")
            else:
                status = "="
                status_color = "yellow"
            
            # Add to table
            table.add_row(
                metric_name,
                f"{v1_val:.3f}",
                f"{v2_val:.3f}",
                f"{delta:+.1f}%",
                f"[{status_color}]{status}[/{status_color}]"
            )
    
    console.print(table)
    
    # Show improvements and regressions
    if improvements:
        console.print("\n[bold green]✓ Improvements:[/bold green]")
        for imp in improvements:
            console.print(f"  • {imp}")
    
    if regressions:
        console.print("\n[bold red]✗ Regressions:[/bold red]")
        for reg in regressions:
            console.print(f"  • {reg}")
    
    if not improvements and not regressions:
        console.print("\n[yellow]= No significant changes detected[/yellow]")
    
    # Generate recommendation
    recommendation = generate_recommendation(improvements, regressions, metric_deltas)
    
    console.print(f"\n[bold]🎯 Recommendation:[/bold] {recommendation}\n")
    
    # Detailed comparison
    if detailed:
        console.print("\n[bold]📋 Detailed Per-Persona Comparison:[/bold]\n")
        compare_personas_detailed(eval1, eval2)
    
    return VersionComparison(
        version1=version1,
        version2=version2,
        improvements=improvements,
        regressions=regressions,
        metric_deltas=metric_deltas,
        recommendation=recommendation,
        timestamp=datetime.now().isoformat()
    )


def compare_personas_detailed(eval1: Dict, eval2: Dict):
    """Detailed per-persona comparison"""
    personas1 = {p['persona_id']: p for p in eval1.get('persona_evaluations', [])}
    personas2 = {p['persona_id']: p for p in eval2.get('persona_evaluations', [])}
    
    # Find common personas
    common_personas = set(personas1.keys()) & set(personas2.keys())
    
    if not common_personas:
        console.print("[yellow]No common personas found[/yellow]")
        return
    
    # Create comparison table
    table = Table(title="Per-Persona Score Changes")
    table.add_column("Persona", style="cyan", width=30)
    table.add_column("v1 Score", justify="right")
    table.add_column("v2 Score", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Status", justify="center")
    
    improvements = []
    regressions = []
    
    for persona_id in sorted(common_personas):
        p1 = personas1[persona_id]
        p2 = personas2[persona_id]
        
        score1 = p1['overall_score']
        score2 = p2['overall_score']
        delta, direction = compute_metric_delta(score1, score2)
        
        if direction == "improvement":
            change_color = "green"
            status = "↑"
            if delta > 5:
                improvements.append((p1['persona_label'], delta))
        elif direction == "regression":
            change_color = "red"
            status = "↓"
            if delta < -5:
                regressions.append((p1['persona_label'], delta))
        else:
            change_color = "yellow"
            status = "="
        
        table.add_row(
            p1['persona_label'],
            f"{score1:.3f}",
            f"{score2:.3f}",
            f"[{change_color}]{delta:+.1f}%[/{change_color}]",
            status
        )
    
    console.print(table)
    
    # Highlight top improvements and regressions
    if improvements:
        console.print("\n[bold green]Top Improvements:[/bold green]")
        for persona, delta in sorted(improvements, key=lambda x: x[1], reverse=True)[:3]:
            console.print(f"  ✓ {persona}: +{delta:.1f}%")
    
    if regressions:
        console.print("\n[bold red]Top Regressions:[/bold red]")
        for persona, delta in sorted(regressions, key=lambda x: x[1])[:3]:
            console.print(f"  ✗ {persona}: {delta:.1f}%")


def generate_recommendation(
    improvements: List[str],
    regressions: List[str],
    metric_deltas: Dict[str, float]
) -> str:
    """Generate deployment recommendation"""
    # Check for critical regressions
    critical_metrics = ['overall_score', 'pass_rate']
    critical_regressions = [
        metric for metric in critical_metrics
        if metric in metric_deltas and metric_deltas[metric] < -10
    ]
    
    if critical_regressions:
        return "🚫 DO NOT DEPLOY - Critical regressions detected"
    
    # Check for major regressions
    major_regressions = [
        metric for metric, delta in metric_deltas.items()
        if delta < -5
    ]
    
    if major_regressions:
        return "⚠️  CAUTION - Major regressions present, review carefully"
    
    # Check for improvements
    overall_delta = metric_deltas.get('overall_score', 0)
    
    if overall_delta > 5:
        return "✅ RECOMMENDED - Significant improvements, deploy to latest"
    elif overall_delta > 0:
        return "✓ APPROVED - Minor improvements, safe to deploy"
    elif overall_delta >= -2:
        return "= NEUTRAL - No significant changes, deployment optional"
    else:
        return "⚠️  REVIEW NEEDED - Some regressions detected"


def save_comparison_report(
    comparison: VersionComparison,
    output_dir: Path
):
    """Save comparison report to file"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"comparison_{comparison.version1}_vs_{comparison.version2}_{timestamp}"
    
    # Save markdown report
    md_path = output_dir / f"{filename}.md"
    lines = [
        f"# Version Comparison Report",
        f"\n**Generated:** {comparison.timestamp}",
        f"\n## Versions",
        f"\n- **Version 1:** {comparison.version1}",
        f"- **Version 2:** {comparison.version2}",
        f"\n## Summary",
        f"\n**Recommendation:** {comparison.recommendation}",
        f"\n### Improvements ({len(comparison.improvements)})",
        ""
    ]
    
    if comparison.improvements:
        for imp in comparison.improvements:
            lines.append(f"- ✓ {imp}")
    else:
        lines.append("- None")
    
    lines.extend([
        f"\n### Regressions ({len(comparison.regressions)})",
        ""
    ])
    
    if comparison.regressions:
        for reg in comparison.regressions:
            lines.append(f"- ✗ {reg}")
    else:
        lines.append("- None")
    
    lines.extend([
        f"\n## Metric Changes",
        "\n| Metric | Change |",
        "|--------|--------|"
    ])
    
    for metric, delta in sorted(comparison.metric_deltas.items()):
        display_name = metric.replace('_', ' ').replace('avg ', '').title()
        emoji = "✓" if delta > 0 else "✗" if delta < 0 else "="
        lines.append(f"| {display_name} | {emoji} {delta:+.1f}% |")
    
    lines.extend([
        f"\n## Decision Matrix",
        f"\n| Criteria | Status |",
        f"|----------|--------|",
        f"| Critical Regressions | {'✗ Present' if any(d < -10 for d in comparison.metric_deltas.values()) else '✓ None'} |",
        f"| Major Regressions | {'⚠️  Present' if any(d < -5 for d in comparison.metric_deltas.values()) else '✓ None'} |",
        f"| Improvements | {'✓ Present' if comparison.improvements else '= None'} |",
        f"| Overall Change | {comparison.metric_deltas.get('overall_score', 0):+.1f}% |"
    ])
    
    with open(md_path, 'w') as f:
        f.write('\n'.join(lines))
    
    console.print(f"\n[green]✓ Markdown report saved to: {md_path}[/green]")
    
    # Save JSON
    json_path = output_dir / f"{filename}.json"
    with open(json_path, 'w') as f:
        json.dump({
            'version1': comparison.version1,
            'version2': comparison.version2,
            'improvements': comparison.improvements,
            'regressions': comparison.regressions,
            'metric_deltas': comparison.metric_deltas,
            'recommendation': comparison.recommendation,
            'timestamp': comparison.timestamp
        }, f, indent=2)
    
    console.print(f"[green]✓ JSON data saved to: {json_path}[/green]")


def trend_analysis():
    """Analyze trends across all available versions"""
    console.print("\n[bold cyan]📈 Version Trend Analysis[/bold cyan]\n")
    
    # Find all evaluation results
    eval_dir = Path("reports/persona_evaluation")
    if not eval_dir.exists():
        console.print("[red]❌ No evaluation results found[/red]")
        return
    
    # Group by version
    version_evals = {}
    for eval_file in eval_dir.glob("*.json"):
        # Extract version from filename (format: version_timestamp.json)
        parts = eval_file.stem.split('_')
        if len(parts) >= 1:
            # Handle timestamp-based versions or semantic versions
            if parts[0].startswith('v') or parts[0].startswith('auto'):
                version = parts[0]
            else:
                version = '_'.join(parts[:2]) if len(parts) > 1 else parts[0]
            
            if version not in version_evals:
                with open(eval_file, 'r') as f:
                    version_evals[version] = json.load(f)
    
    if not version_evals:
        console.print("[yellow]No evaluation results found for analysis[/yellow]")
        return
    
    # Create trend table
    table = Table(title="Version Performance Trends")
    table.add_column("Version", style="cyan")
    table.add_column("Date", style="dim")
    table.add_column("Overall", justify="right")
    table.add_column("Consistency", justify="right")
    table.add_column("Quality", justify="right")
    table.add_column("Coherence", justify="right")
    table.add_column("Pass Rate", justify="right")
    
    sorted_versions = sorted(
        version_evals.items(),
        key=lambda x: x[1].get('timestamp', '')
    )
    
    for version, eval_data in sorted_versions:
        agg = eval_data.get('aggregate_metrics', {})
        timestamp = eval_data.get('timestamp', 'Unknown')[:10]
        
        table.add_row(
            version,
            timestamp,
            f"{agg.get('overall_score', 0):.3f}",
            f"{agg.get('avg_persona_consistency', 0):.3f}",
            f"{agg.get('avg_response_quality', 0):.3f}",
            f"{agg.get('avg_multi_turn_coherence', 0):.3f}",
            f"{agg.get('pass_rate', 0):.3f}"
        )
    
    console.print(table)
    
    # Show best version
    if sorted_versions:
        best_version = max(
            sorted_versions,
            key=lambda x: x[1].get('aggregate_metrics', {}).get('overall_score', 0)
        )
        
        console.print(f"\n[bold green]🏆 Best Version:[/bold green] {best_version[0]}")
        console.print(f"   Overall Score: {best_version[1].get('aggregate_metrics', {}).get('overall_score', 0):.3f}")


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced version comparison with quality metrics"
    )
    parser.add_argument('version1', nargs='?', help='First version to compare')
    parser.add_argument('version2', nargs='?', help='Second version to compare')
    parser.add_argument('--detailed', action='store_true', help='Show detailed per-persona comparison')
    parser.add_argument('--output', help='Output directory for comparison reports')
    parser.add_argument('--trend-analysis', action='store_true', help='Show performance trends across all versions')
    
    args = parser.parse_args()
    
    if args.trend_analysis:
        trend_analysis()
        return
    
    if not args.version1 or not args.version2:
        console.print("[red]❌ Please specify two versions to compare[/red]")
        console.print("Usage: python scripts/compare_persona_versions.py v1.0 v2.0")
        console.print("   or: python scripts/compare_persona_versions.py --trend-analysis")
        sys.exit(1)
    
    comparison = compare_versions(args.version1, args.version2, args.detailed)
    
    if comparison and args.output:
        save_comparison_report(comparison, Path(args.output))


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
LLM-as-Judge Comprehensive Persona Evaluation

Uses a powerful judge LLM (GPT-4) to:
1. Generate diverse test scenarios
2. Evaluate persona responses
3. Score against defined metrics
4. Generate comprehensive reports

Usage:
    python scripts/llm_judge_evaluation.py --version v1.0 --examples 100
    python scripts/llm_judge_evaluation.py --version v1.0 --examples 10 --quick
"""

from __future__ import annotations
import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import openai
except ImportError:
    console.print("[yellow]⚠️  OpenAI library not installed. Install with: pip install openai[/yellow]")
    sys.exit(1)


@dataclass
class JudgmentResult:
    """Result of judging a single response"""
    scenario: str
    persona_id: str
    persona_label: str
    response: str
    
    # Scores (0-10 scale)
    consistency_score: float
    quality_score: float
    relevance_score: float
    persona_adherence_score: float
    overall_score: float
    
    # Judge feedback
    strengths: List[str]
    weaknesses: List[str]
    judge_reasoning: str
    
    timestamp: str


@dataclass
class PersonaEvaluationReport:
    """Complete evaluation for one persona"""
    persona_id: str
    persona_label: str
    total_examples: int
    
    # Aggregate scores
    avg_consistency: float
    avg_quality: float
    avg_relevance: float
    avg_persona_adherence: float
    overall_average: float
    
    # Individual judgments
    judgments: List[JudgmentResult]
    
    # Summary
    top_strengths: List[str]
    top_weaknesses: List[str]
    recommendation: str
    
    timestamp: str


class LLMJudgeEvaluator:
    """LLM-as-Judge evaluation system"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        judge_model: str = "gpt-4",
        temperature: float = 0.3
    ):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            console.print("[red]❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable.[/red]")
            sys.exit(1)
        
        openai.api_key = self.api_key
        self.judge_model = judge_model
        self.temperature = temperature
        
        # Load personas
        self.personas = self._load_personas()
        
        console.print(f"\n[bold cyan]🤖 LLM-as-Judge Evaluator Initialized[/bold cyan]")
        console.print(f"Judge Model: {judge_model}")
        console.print(f"Personas: {len(self.personas)}\n")
    
    def _load_personas(self) -> List[Dict]:
        """Load persona definitions"""
        personas_file = project_root / "DATA" / "personas.json"
        if not personas_file.exists():
            console.print("[red]❌ Personas file not found[/red]")
            sys.exit(1)
        
        with open(personas_file, 'r') as f:
            data = json.load(f)
        return data.get('personas', [])
    
    def generate_test_scenarios(self, num_examples: int = 100) -> List[str]:
        """Generate diverse test scenarios using the judge LLM"""
        console.print(f"[cyan]Generating {num_examples} test scenarios...[/cyan]")
        
        prompt = f"""Generate {num_examples} diverse shopping and e-commerce related scenarios for testing digital shopping personas.

Each scenario should be a realistic question or situation a shopper might face. Cover:
- Product recommendations
- Purchase decisions
- Price comparisons
- Brand choices
- Urgency situations
- Budget constraints
- Multi-turn conversations
- Gift buying
- Subscription decisions
- Ethical/sustainable shopping

Return as a JSON array of strings, one scenario per string.

Example format:
["I need new headphones for my daily commute, budget is $150", "Should I wait for Black Friday to buy this laptop?", ...]

Generate exactly {num_examples} unique, realistic scenarios:"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.judge_model,
                messages=[
                    {"role": "system", "content": "You are an expert in e-commerce and shopping behavior, helping generate realistic test scenarios."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON
            scenarios = json.loads(content)
            
            console.print(f"[green]✓ Generated {len(scenarios)} scenarios[/green]\n")
            return scenarios[:num_examples]
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Error generating scenarios: {e}[/yellow]")
            # Fallback to predefined scenarios
            return self._get_fallback_scenarios(num_examples)
    
    def _get_fallback_scenarios(self, num: int) -> List[str]:
        """Fallback predefined scenarios"""
        base_scenarios = [
            "I need new running shoes for marathon training, what should I consider?",
            "Should I buy this $800 smartphone now or wait for the next model?",
            "Looking for eco-friendly cleaning products, any recommendations?",
            "Need a gift for my tech-savvy friend, budget around $50",
            "Is it worth buying in bulk from warehouse stores?",
            "Comparing Nike vs Adidas, which brand is better?",
            "This deal ends in 2 hours, should I buy now?",
            "Want to subscribe to meal kit service, which one?",
            "Need laptop for college, how do I choose?",
            "Looking for quality over price, what matters most?",
        ]
        
        # Repeat and vary to reach desired number
        scenarios = []
        while len(scenarios) < num:
            scenarios.extend(base_scenarios)
        
        return scenarios[:num]
    
    def generate_persona_response(
        self,
        persona_id: str,
        scenario: str
    ) -> str:
        """Generate response as if from the persona (simulated for demo)"""
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        if not persona:
            return "No response available."
        
        # In production, this would load the actual trained model
        # For demo, we use GPT to simulate the persona
        
        prompt = f"""You are roleplaying as: {persona['label']}

Persona Description:
{persona.get('blurb', '')}

System Prompt:
{persona.get('system_prompt', '')}

Decision Constraints:
{persona.get('decision_constraints', '')}

Shopping Values: {', '.join(persona.get('shopping_values', []))}
Typical Behavior: {persona.get('typical_behavior', '')}

Now respond to this scenario AS THIS PERSONA:
"{scenario}"

Provide a natural, helpful response that clearly reflects this persona's characteristics and values. Keep it conversational and realistic (2-4 sentences)."""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Faster for persona simulation
                messages=[
                    {"role": "system", "content": f"You are {persona['label']}. {persona.get('system_prompt', '')}"},
                    {"role": "user", "content": scenario}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Error generating response: {e}[/yellow]")
            return f"[Simulated {persona['label']} response to: {scenario}]"
    
    def judge_response(
        self,
        persona_id: str,
        scenario: str,
        response: str
    ) -> JudgmentResult:
        """Judge a persona's response using the LLM judge"""
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        judge_prompt = f"""You are an expert evaluator of digital shopping personas. Evaluate this response:

PERSONA: {persona['label']}
Expected Characteristics:
- System Prompt: {persona.get('system_prompt', '')}
- Shopping Values: {', '.join(persona.get('shopping_values', []))}
- Decision Constraints: {persona.get('decision_constraints', '')}
- Typical Behavior: {persona.get('typical_behavior', '')}

SCENARIO: {scenario}

RESPONSE: {response}

Evaluate on a scale of 0-10 for each:
1. Consistency: Does the response align with the persona's defined characteristics?
2. Quality: Is the response helpful, coherent, and well-structured?
3. Relevance: Does it address the scenario appropriately?
4. Persona Adherence: How well does it embody this specific persona (vs a generic response)?

Also provide:
- 2-3 specific strengths
- 2-3 specific weaknesses or areas for improvement
- Brief reasoning for your scores

Return as JSON:
{{
  "consistency_score": 8.5,
  "quality_score": 9.0,
  "relevance_score": 8.0,
  "persona_adherence_score": 7.5,
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "reasoning": "explanation"
}}"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.judge_model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator. Provide objective, detailed assessments."},
                    {"role": "user", "content": judge_prompt}
                ],
                temperature=self.temperature,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON
            judgment = json.loads(content)
            
            # Calculate overall score
            overall = (
                judgment['consistency_score'] +
                judgment['quality_score'] +
                judgment['relevance_score'] +
                judgment['persona_adherence_score']
            ) / 4.0
            
            return JudgmentResult(
                scenario=scenario,
                persona_id=persona_id,
                persona_label=persona['label'],
                response=response,
                consistency_score=judgment['consistency_score'],
                quality_score=judgment['quality_score'],
                relevance_score=judgment['relevance_score'],
                persona_adherence_score=judgment['persona_adherence_score'],
                overall_score=overall,
                strengths=judgment.get('strengths', []),
                weaknesses=judgment.get('weaknesses', []),
                judge_reasoning=judgment.get('reasoning', ''),
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Error judging response: {e}[/yellow]")
            # Fallback to basic scoring
            return self._fallback_judgment(persona_id, scenario, response)
    
    def _fallback_judgment(self, persona_id: str, scenario: str, response: str) -> JudgmentResult:
        """Fallback judgment if LLM fails"""
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        
        # Simple heuristic scoring
        has_values = any(val.replace('_', ' ') in response.lower() 
                        for val in persona.get('shopping_values', []))
        
        base_score = 7.0 if has_values else 6.0
        
        return JudgmentResult(
            scenario=scenario,
            persona_id=persona_id,
            persona_label=persona['label'] if persona else persona_id,
            response=response,
            consistency_score=base_score,
            quality_score=base_score + 0.5,
            relevance_score=base_score + 0.3,
            persona_adherence_score=base_score - 0.2,
            overall_score=base_score,
            strengths=["Response provided", "Addresses scenario"],
            weaknesses=["Could be more specific"],
            judge_reasoning="Fallback scoring used",
            timestamp=datetime.now().isoformat()
        )
    
    def evaluate_persona(
        self,
        persona_id: str,
        scenarios: List[str],
        progress_bar: Optional[Progress] = None,
        task_id: Optional[int] = None
    ) -> PersonaEvaluationReport:
        """Evaluate one persona across all scenarios"""
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        console.print(f"\n[cyan]Evaluating: {persona['label']}[/cyan]")
        
        judgments = []
        
        for i, scenario in enumerate(scenarios):
            if progress_bar and task_id:
                progress_bar.update(task_id, advance=1, description=f"[cyan]{persona['label'][:30]}... ({i+1}/{len(scenarios)})[/cyan]")
            
            # Generate response
            response = self.generate_persona_response(persona_id, scenario)
            
            # Judge response
            judgment = self.judge_response(persona_id, scenario, response)
            judgments.append(judgment)
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
        
        # Calculate aggregates
        avg_consistency = sum(j.consistency_score for j in judgments) / len(judgments)
        avg_quality = sum(j.quality_score for j in judgments) / len(judgments)
        avg_relevance = sum(j.relevance_score for j in judgments) / len(judgments)
        avg_persona_adherence = sum(j.persona_adherence_score for j in judgments) / len(judgments)
        overall_avg = sum(j.overall_score for j in judgments) / len(judgments)
        
        # Collect strengths and weaknesses
        all_strengths = [s for j in judgments for s in j.strengths]
        all_weaknesses = [w for j in judgments for w in j.weaknesses]
        
        # Count frequency
        from collections import Counter
        strength_counts = Counter(all_strengths)
        weakness_counts = Counter(all_weaknesses)
        
        top_strengths = [s for s, _ in strength_counts.most_common(5)]
        top_weaknesses = [w for w, _ in weakness_counts.most_common(5)]
        
        # Generate recommendation
        if overall_avg >= 8.5:
            recommendation = "✅ EXCELLENT - Production ready"
        elif overall_avg >= 7.5:
            recommendation = "✓ GOOD - Minor improvements suggested"
        elif overall_avg >= 6.5:
            recommendation = "⚠️  ACCEPTABLE - Notable improvements needed"
        else:
            recommendation = "🚫 NEEDS WORK - Significant improvements required"
        
        return PersonaEvaluationReport(
            persona_id=persona_id,
            persona_label=persona['label'],
            total_examples=len(scenarios),
            avg_consistency=avg_consistency,
            avg_quality=avg_quality,
            avg_relevance=avg_relevance,
            avg_persona_adherence=avg_persona_adherence,
            overall_average=overall_avg,
            judgments=judgments,
            top_strengths=top_strengths,
            top_weaknesses=top_weaknesses,
            recommendation=recommendation,
            timestamp=datetime.now().isoformat()
        )
    
    def evaluate_all_personas(
        self,
        num_examples: int = 100,
        persona_ids: Optional[List[str]] = None
    ) -> Dict[str, PersonaEvaluationReport]:
        """Evaluate all personas"""
        # Generate test scenarios once
        scenarios = self.generate_test_scenarios(num_examples)
        
        # Determine which personas to evaluate
        if persona_ids:
            personas_to_eval = [p for p in self.personas if p['id'] in persona_ids]
        else:
            personas_to_eval = self.personas
        
        console.print(f"\n[bold green]🚀 Starting Comprehensive Evaluation[/bold green]")
        console.print(f"Personas: {len(personas_to_eval)}")
        console.print(f"Scenarios per persona: {num_examples}\n")
        
        reports = {}
        total_evaluations = len(personas_to_eval) * num_examples
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Evaluating personas...",
                total=total_evaluations
            )
            
            for persona in personas_to_eval:
                report = self.evaluate_persona(
                    persona['id'],
                    scenarios,
                    progress,
                    task
                )
                reports[persona['id']] = report
        
        return reports
    
    def save_reports(
        self,
        reports: Dict[str, PersonaEvaluationReport],
        output_dir: Path
    ):
        """Save evaluation reports"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save individual persona reports
        for persona_id, report in reports.items():
            # JSON
            json_path = output_dir / f"llm_judge_{persona_id}_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump(asdict(report), f, indent=2)
        
        # Save aggregate report
        aggregate = {
            'timestamp': datetime.now().isoformat(),
            'total_personas': len(reports),
            'total_examples_per_persona': reports[list(reports.keys())[0]].total_examples if reports else 0,
            'persona_summaries': [
                {
                    'persona_id': report.persona_id,
                    'persona_label': report.persona_label,
                    'overall_average': report.overall_average,
                    'recommendation': report.recommendation
                }
                for report in reports.values()
            ],
            'overall_average': sum(r.overall_average for r in reports.values()) / len(reports) if reports else 0
        }
        
        agg_path = output_dir / f"llm_judge_aggregate_{timestamp}.json"
        with open(agg_path, 'w') as f:
            json.dump(aggregate, f, indent=2)
        
        # Markdown summary
        md_path = output_dir / f"llm_judge_summary_{timestamp}.md"
        self._save_markdown_summary(reports, md_path)
        
        console.print(f"\n[green]✓ Reports saved to: {output_dir}[/green]")
        console.print(f"  • Individual reports: llm_judge_{{persona}}_*.json")
        console.print(f"  • Aggregate report: llm_judge_aggregate_*.json")
        console.print(f"  • Summary: llm_judge_summary_*.md")
    
    def _save_markdown_summary(
        self,
        reports: Dict[str, PersonaEvaluationReport],
        output_path: Path
    ):
        """Save markdown summary"""
        lines = [
            "# LLM-as-Judge Evaluation Summary",
            f"\n**Generated:** {datetime.now().isoformat()}",
            f"**Judge Model:** {self.judge_model}",
            f"**Personas Evaluated:** {len(reports)}",
            f"**Examples per Persona:** {reports[list(reports.keys())[0]].total_examples if reports else 0}",
            "\n## Overall Results",
            "\n| Persona | Overall Score | Recommendation |",
            "|---------|---------------|----------------|"
        ]
        
        for report in sorted(reports.values(), key=lambda r: r.overall_average, reverse=True):
            lines.append(
                f"| {report.persona_label} | {report.overall_average:.2f}/10 | {report.recommendation} |"
            )
        
        lines.extend([
            "\n## Detailed Scores",
            "\n| Persona | Consistency | Quality | Relevance | Adherence |",
            "|---------|-------------|---------|-----------|-----------|"
        ])
        
        for report in sorted(reports.values(), key=lambda r: r.overall_average, reverse=True):
            lines.append(
                f"| {report.persona_label} | {report.avg_consistency:.2f} | "
                f"{report.avg_quality:.2f} | {report.avg_relevance:.2f} | "
                f"{report.avg_persona_adherence:.2f} |"
            )
        
        # Add top performers
        lines.extend([
            "\n## Top Performing Personas",
            ""
        ])
        
        top_3 = sorted(reports.values(), key=lambda r: r.overall_average, reverse=True)[:3]
        for i, report in enumerate(top_3, 1):
            lines.append(f"{i}. **{report.persona_label}** - {report.overall_average:.2f}/10")
            lines.append(f"   - Strengths: {', '.join(report.top_strengths[:3])}")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description="LLM-as-Judge Persona Evaluation")
    parser.add_argument('--examples', type=int, default=100, help='Number of test examples per persona')
    parser.add_argument('--personas', nargs='+', help='Specific personas to evaluate')
    parser.add_argument('--judge-model', default='gpt-4', help='Judge model to use')
    parser.add_argument('--output', default='reports/llm_judge/', help='Output directory')
    parser.add_argument('--quick', action='store_true', help='Quick test (10 examples)')
    
    args = parser.parse_args()
    
    if args.quick:
        args.examples = 10
    
    # Initialize evaluator
    evaluator = LLMJudgeEvaluator(judge_model=args.judge_model)
    
    # Run evaluation
    reports = evaluator.evaluate_all_personas(
        num_examples=args.examples,
        persona_ids=args.personas
    )
    
    # Display summary
    console.print("\n" + "="*80)
    console.print(Panel(
        f"[bold green]Evaluation Complete[/bold green]\n\n"
        f"Personas: {len(reports)}\n"
        f"Examples each: {args.examples}\n"
        f"Overall Average: {sum(r.overall_average for r in reports.values()) / len(reports):.2f}/10",
        title="Summary",
        border_style="green"
    ))
    
    # Show results table
    table = Table(title="Persona Scores")
    table.add_column("Persona", style="cyan")
    table.add_column("Overall", justify="right")
    table.add_column("Recommendation", justify="center")
    
    for report in sorted(reports.values(), key=lambda r: r.overall_average, reverse=True):
        color = "green" if report.overall_average >= 8.0 else "yellow" if report.overall_average >= 7.0 else "red"
        table.add_row(
            report.persona_label,
            f"[{color}]{report.overall_average:.2f}/10[/{color}]",
            report.recommendation
        )
    
    console.print("\n")
    console.print(table)
    
    # Save reports
    evaluator.save_reports(reports, Path(args.output))


if __name__ == '__main__':
    main()


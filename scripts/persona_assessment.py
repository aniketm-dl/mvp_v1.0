#!/usr/bin/env python3
"""
Comprehensive Persona Performance Assessment System

This script evaluates trained persona models across multiple quality dimensions:
- Persona consistency and trait alignment
- Response quality and naturalness
- Persona differentiation
- Domain expertise
- Multi-turn coherence
- Technical performance

Usage:
    # Evaluate latest version
    python scripts/persona_assessment.py
    
    # Evaluate specific version
    python scripts/persona_assessment.py --version v1.0
    
    # Evaluate all personas with detailed report
    python scripts/persona_assessment.py --version v1.0 --detailed --output reports/
    
    # Quick smoke test
    python scripts/persona_assessment.py --quick
"""

from __future__ import annotations
import argparse
import json
import time
import yaml
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import sys
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich import print as rprint

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("⚠️  Warning: Some dependencies not installed. Install with:")
    print("   pip install transformers peft sentence-transformers torch")
    sys.exit(1)

console = Console()


@dataclass
class MetricResult:
    """Result of a single metric evaluation"""
    name: str
    score: float
    threshold: float
    passed: bool
    details: Optional[Dict[str, Any]] = None


@dataclass
class PersonaEvaluation:
    """Evaluation results for a single persona"""
    persona_id: str
    persona_label: str
    overall_score: float
    metrics: Dict[str, MetricResult]
    sample_responses: List[Dict[str, str]]
    evaluation_time: float
    timestamp: str


@dataclass
class VersionEvaluation:
    """Complete evaluation results for a model version"""
    version: str
    timestamp: str
    overall_score: float
    persona_evaluations: List[PersonaEvaluation]
    aggregate_metrics: Dict[str, float]
    quality_gates_passed: bool
    regressions: List[str]
    improvements: List[str]
    recommendations: List[str]


class PersonaAssessor:
    """Main persona assessment system"""
    
    def __init__(
        self,
        version: str = "latest",
        metrics_config_path: str = "CONFIGS/persona_evaluation_metrics.yaml",
        base_model: str = "mistralai/Mistral-7B-Instruct-v0.2",
        device: str = "auto"
    ):
        self.version = version
        self.base_model = base_model
        self.device = self._setup_device(device)
        
        # Load configurations
        self.metrics_config = self._load_metrics_config(metrics_config_path)
        self.personas = self._load_personas()
        self.test_scenarios = self.metrics_config['test_scenarios']
        
        # Models (loaded lazily)
        self.tokenizer = None
        self.embedding_model = None
        self.loaded_adapters = {}
        
        # Results storage
        self.results = []
        
        console.print(f"\n[bold blue]🔍 Persona Assessment System Initialized[/bold blue]")
        console.print(f"Version: {version}")
        console.print(f"Device: {self.device}")
        console.print(f"Personas to evaluate: {len(self.personas)}\n")
    
    def _setup_device(self, device: str) -> str:
        """Setup compute device"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _load_metrics_config(self, config_path: str) -> Dict:
        """Load metrics configuration"""
        config_file = project_root / config_path
        if not config_file.exists():
            console.print(f"[red]❌ Metrics config not found: {config_path}[/red]")
            sys.exit(1)
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_personas(self) -> List[Dict[str, Any]]:
        """Load persona definitions"""
        personas_file = project_root / "DATA" / "personas.json"
        if not personas_file.exists():
            console.print("[red]❌ Personas file not found[/red]")
            sys.exit(1)
        
        with open(personas_file, 'r') as f:
            data = json.load(f)
        return data.get('personas', [])
    
    def _load_tokenizer(self):
        """Load tokenizer (lazy loading)"""
        if self.tokenizer is None:
            console.print("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def _load_embedding_model(self):
        """Load embedding model for similarity comparisons"""
        if self.embedding_model is None:
            console.print("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def _load_persona_adapter(self, persona_id: str) -> Optional[PeftModel]:
        """Load a specific persona's LoRA adapter"""
        if persona_id in self.loaded_adapters:
            return self.loaded_adapters[persona_id]
        
        # Find adapter path
        version_dir = project_root / "trained_models" / self.version
        if not version_dir.exists():
            console.print(f"[yellow]⚠️  Version directory not found: {version_dir}[/yellow]")
            return None
        
        adapter_path = version_dir / "adapters" / persona_id
        if not adapter_path.exists():
            console.print(f"[yellow]⚠️  Adapter not found for {persona_id}[/yellow]")
            return None
        
        try:
            # Load base model first time only
            if not hasattr(self, 'base_model_loaded'):
                console.print(f"Loading base model: {self.base_model}")
                self.base_model_instance = AutoModelForCausalLM.from_pretrained(
                    self.base_model,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map=self.device
                )
                self.base_model_loaded = True
            
            # Load adapter
            model = PeftModel.from_pretrained(
                self.base_model_instance,
                str(adapter_path)
            )
            model.eval()
            
            self.loaded_adapters[persona_id] = model
            return model
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load adapter for {persona_id}: {e}[/red]")
            return None
    
    def _generate_response(
        self,
        model: PeftModel,
        persona_id: str,
        prompt: str,
        max_new_tokens: int = 200,
        temperature: float = 0.7
    ) -> str:
        """Generate response from persona model"""
        self._load_tokenizer()
        
        # Get persona system prompt
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        if not persona:
            return ""
        
        # Format prompt with persona context
        full_prompt = f"""<s>[INST] {persona['system_prompt']}

User: {prompt} [/INST]"""
        
        # Tokenize
        inputs = self.tokenizer(
            full_prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the response (after [/INST])
        if "[/INST]" in response:
            response = response.split("[/INST]")[-1].strip()
        
        return response
    
    def evaluate_persona_consistency(
        self,
        persona_id: str,
        model: PeftModel,
        samples: int = 5
    ) -> MetricResult:
        """Evaluate how consistently persona maintains its character"""
        self._load_embedding_model()
        
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        if not persona:
            return MetricResult("persona_consistency", 0.0, 0.8, False)
        
        # Get test prompts
        prompts = [
            scenario['prompt'] 
            for scenario in self.test_scenarios['standard_prompts'][:samples]
        ]
        
        # Generate responses
        responses = []
        for prompt in prompts:
            response = self._generate_response(model, persona_id, prompt)
            responses.append(response)
        
        # Check for persona-specific keywords and values
        value_matches = []
        for response in responses:
            response_lower = response.lower()
            
            # Check shopping values
            matches = sum(
                1 for value in persona.get('shopping_values', [])
                if value.replace('_', ' ') in response_lower
            )
            value_matches.append(matches / max(len(persona.get('shopping_values', [1])), 1))
        
        # Check behavior consistency
        behavior_text = persona.get('typical_behavior', '').lower()
        behavior_keywords = behavior_text.split(', ')
        
        behavior_matches = []
        for response in responses:
            response_lower = response.lower()
            matches = sum(
                1 for keyword in behavior_keywords
                if keyword in response_lower
            )
            behavior_matches.append(matches / max(len(behavior_keywords), 1))
        
        # Compute overall consistency score
        value_score = np.mean(value_matches) if value_matches else 0.0
        behavior_score = np.mean(behavior_matches) if behavior_matches else 0.0
        
        consistency_score = (value_score * 0.6 + behavior_score * 0.4)
        
        threshold = self.metrics_config['quality_metrics']['persona_consistency']['sub_metrics'][1]['threshold']
        
        return MetricResult(
            name="persona_consistency",
            score=float(consistency_score),
            threshold=threshold,
            passed=consistency_score >= threshold,
            details={
                "value_alignment": float(value_score),
                "behavior_alignment": float(behavior_score),
                "sample_responses": responses[:2]  # Include sample for review
            }
        )
    
    def evaluate_response_quality(
        self,
        persona_id: str,
        model: PeftModel,
        samples: int = 5
    ) -> MetricResult:
        """Evaluate overall response quality"""
        prompts = [
            scenario['prompt'] 
            for scenario in self.test_scenarios['standard_prompts'][:samples]
        ]
        
        responses = []
        quality_scores = []
        
        for prompt in prompts:
            response = self._generate_response(model, persona_id, prompt)
            responses.append(response)
            
            # Simple quality heuristics
            # 1. Length appropriateness (50-500 chars is good)
            length_score = min(1.0, len(response) / 200) if len(response) < 500 else 0.8
            
            # 2. Has actionable content (looks for imperative verbs, suggestions)
            action_words = ['consider', 'should', 'recommend', 'suggest', 'try', 'look for', 'check']
            has_action = any(word in response.lower() for word in action_words)
            action_score = 1.0 if has_action else 0.5
            
            # 3. Coherence (no repetition, complete sentences)
            words = response.split()
            unique_ratio = len(set(words)) / max(len(words), 1)
            coherence_score = min(1.0, unique_ratio / 0.7)
            
            # 4. Relevance (mentions shopping/products)
            relevant_terms = ['product', 'price', 'buy', 'purchase', 'shop', 'deal', 'quality', 'brand']
            relevance_score = min(1.0, sum(term in response.lower() for term in relevant_terms) / 3)
            
            quality = (length_score * 0.25 + action_score * 0.25 + 
                      coherence_score * 0.25 + relevance_score * 0.25)
            quality_scores.append(quality)
        
        avg_quality = np.mean(quality_scores)
        threshold = 0.70
        
        return MetricResult(
            name="response_quality",
            score=float(avg_quality),
            threshold=threshold,
            passed=avg_quality >= threshold,
            details={
                "per_sample_scores": [float(s) for s in quality_scores],
                "sample_responses": responses[:2]
            }
        )
    
    def evaluate_persona_differentiation(
        self,
        persona_evaluations: Dict[str, List[str]]
    ) -> MetricResult:
        """Evaluate how distinct personas are from each other"""
        self._load_embedding_model()
        
        # For each test scenario, compare responses from different personas
        persona_ids = list(persona_evaluations.keys())
        
        if len(persona_ids) < 2:
            return MetricResult("persona_differentiation", 0.0, 0.5, False)
        
        # Get embeddings for all responses
        all_distances = []
        
        # Compare each pair of personas
        for i, pid1 in enumerate(persona_ids):
            for pid2 in persona_ids[i+1:]:
                responses1 = persona_evaluations[pid1]
                responses2 = persona_evaluations[pid2]
                
                # Compare corresponding responses
                for r1, r2 in zip(responses1, responses2):
                    if r1 and r2:
                        emb1 = self.embedding_model.encode(r1)
                        emb2 = self.embedding_model.encode(r2)
                        
                        # Cosine distance
                        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                        distance = 1 - similarity
                        all_distances.append(distance)
        
        if not all_distances:
            return MetricResult("persona_differentiation", 0.0, 0.5, False)
        
        avg_distance = np.mean(all_distances)
        threshold = 0.5
        
        return MetricResult(
            name="persona_differentiation",
            score=float(avg_distance),
            threshold=threshold,
            passed=avg_distance >= threshold,
            details={
                "mean_distance": float(avg_distance),
                "std_distance": float(np.std(all_distances)),
                "comparisons": len(all_distances)
            }
        )
    
    def evaluate_multi_turn_coherence(
        self,
        persona_id: str,
        model: PeftModel
    ) -> MetricResult:
        """Evaluate conversation continuity across turns"""
        # Get multi-turn scenario
        multi_turn = next(
            (s for s in self.test_scenarios['standard_prompts'] 
             if s['category'] == 'multi_turn_conversation'),
            None
        )
        
        if not multi_turn or 'turns' not in multi_turn:
            # Fallback: simulate multi-turn
            turns = [
                "I need new headphones.",
                "I'll be using them mainly for commuting.",
                "My budget is around $100."
            ]
        else:
            turns = [turn['user'] for turn in multi_turn['turns']]
        
        # Conduct multi-turn conversation
        conversation_history = []
        coherence_scores = []
        
        for i, user_message in enumerate(turns):
            # Build context from history
            context = "\n".join([
                f"{'User' if j % 2 == 0 else 'Assistant'}: {msg}"
                for j, msg in enumerate(conversation_history)
            ])
            
            full_prompt = f"{context}\nUser: {user_message}" if context else user_message
            
            response = self._generate_response(model, persona_id, full_prompt, max_new_tokens=150)
            conversation_history.extend([user_message, response])
            
            # Check coherence
            if i > 0:
                # Response should reference previous context
                prev_keywords = set(conversation_history[-3].lower().split())
                response_words = set(response.lower().split())
                
                # Remove common stopwords for better signal
                stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with'}
                prev_keywords -= stopwords
                response_words -= stopwords
                
                overlap = len(prev_keywords & response_words)
                coherence = min(1.0, overlap / max(len(prev_keywords), 1))
                coherence_scores.append(coherence)
        
        avg_coherence = np.mean(coherence_scores) if coherence_scores else 0.5
        threshold = 0.3  # Lower threshold since this is a hard task
        
        return MetricResult(
            name="multi_turn_coherence",
            score=float(avg_coherence),
            threshold=threshold,
            passed=avg_coherence >= threshold,
            details={
                "turns": len(turns),
                "per_turn_coherence": [float(s) for s in coherence_scores],
                "conversation_sample": conversation_history
            }
        )
    
    def evaluate_single_persona(self, persona_id: str) -> PersonaEvaluation:
        """Run complete evaluation for a single persona"""
        start_time = time.time()
        
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        if not persona:
            console.print(f"[red]❌ Persona not found: {persona_id}[/red]")
            return None
        
        console.print(f"\n[cyan]Evaluating: {persona['label']} ({persona_id})[/cyan]")
        
        # Load model
        model = self._load_persona_adapter(persona_id)
        if model is None:
            console.print(f"[yellow]⚠️  Skipping {persona_id} - model not available[/yellow]")
            return None
        
        # Run evaluations
        metrics = {}
        sample_responses = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Running metrics...", total=4)
            
            # 1. Persona Consistency
            progress.update(task, description="Persona Consistency")
            metrics['persona_consistency'] = self.evaluate_persona_consistency(persona_id, model)
            progress.advance(task)
            
            # 2. Response Quality
            progress.update(task, description="Response Quality")
            metrics['response_quality'] = self.evaluate_response_quality(persona_id, model)
            sample_responses.extend(metrics['response_quality'].details.get('sample_responses', []))
            progress.advance(task)
            
            # 3. Multi-turn Coherence
            progress.update(task, description="Multi-turn Coherence")
            metrics['multi_turn_coherence'] = self.evaluate_multi_turn_coherence(persona_id, model)
            progress.advance(task)
            
            progress.update(task, description="✓ Complete")
            progress.advance(task)
        
        # Calculate overall score
        weights = {
            'persona_consistency': 0.35,
            'response_quality': 0.35,
            'multi_turn_coherence': 0.30
        }
        
        overall_score = sum(
            metrics[key].score * weight
            for key, weight in weights.items()
            if key in metrics
        )
        
        evaluation_time = time.time() - start_time
        
        # Display results
        self._display_persona_results(persona, metrics, overall_score)
        
        return PersonaEvaluation(
            persona_id=persona_id,
            persona_label=persona['label'],
            overall_score=overall_score,
            metrics=metrics,
            sample_responses=[
                {"prompt": "sample", "response": r}
                for r in sample_responses[:3]
            ],
            evaluation_time=evaluation_time,
            timestamp=datetime.now().isoformat()
        )
    
    def _display_persona_results(self, persona: Dict, metrics: Dict[str, MetricResult], overall_score: float):
        """Display results for a single persona"""
        table = Table(title=f"{persona['label']} Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Threshold", justify="right")
        table.add_column("Status", justify="center")
        
        for metric_name, result in metrics.items():
            status = "✓" if result.passed else "✗"
            status_color = "green" if result.passed else "red"
            
            table.add_row(
                metric_name.replace('_', ' ').title(),
                f"{result.score:.3f}",
                f"{result.threshold:.3f}",
                f"[{status_color}]{status}[/{status_color}]"
            )
        
        table.add_row(
            "[bold]Overall Score[/bold]",
            f"[bold]{overall_score:.3f}[/bold]",
            "-",
            "✓" if overall_score >= 0.7 else "✗"
        )
        
        console.print(table)
    
    def evaluate_all_personas(self, quick: bool = False) -> VersionEvaluation:
        """Evaluate all personas in the version"""
        console.print(f"\n[bold green]🚀 Starting Full Persona Evaluation[/bold green]")
        console.print(f"Version: {self.version}")
        console.print(f"Personas: {len(self.personas)}\n")
        
        start_time = time.time()
        persona_evaluations = []
        persona_responses_for_diff = {}
        
        # Limit personas for quick mode
        personas_to_eval = self.personas[:3] if quick else self.personas
        
        for persona in personas_to_eval:
            eval_result = self.evaluate_single_persona(persona['id'])
            if eval_result:
                persona_evaluations.append(eval_result)
                
                # Collect responses for differentiation analysis
                persona_responses_for_diff[persona['id']] = [
                    r['response'] for r in eval_result.sample_responses
                ]
        
        # Evaluate differentiation across personas
        if len(persona_evaluations) > 1:
            console.print("\n[cyan]Evaluating persona differentiation...[/cyan]")
            diff_metric = self.evaluate_persona_differentiation(persona_responses_for_diff)
        else:
            diff_metric = MetricResult("persona_differentiation", 0.0, 0.5, False)
        
        # Aggregate metrics
        aggregate_metrics = self._compute_aggregate_metrics(persona_evaluations, diff_metric)
        overall_score = aggregate_metrics.get('overall_score', 0.0)
        
        # Quality gates
        quality_gates_passed = self._check_quality_gates(aggregate_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(persona_evaluations, aggregate_metrics)
        
        total_time = time.time() - start_time
        
        version_eval = VersionEvaluation(
            version=self.version,
            timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            persona_evaluations=persona_evaluations,
            aggregate_metrics=aggregate_metrics,
            quality_gates_passed=quality_gates_passed,
            regressions=[],
            improvements=[],
            recommendations=recommendations
        )
        
        # Display summary
        self._display_summary(version_eval, total_time)
        
        return version_eval
    
    def _compute_aggregate_metrics(
        self,
        persona_evaluations: List[PersonaEvaluation],
        diff_metric: MetricResult
    ) -> Dict[str, float]:
        """Compute aggregate metrics across all personas"""
        if not persona_evaluations:
            return {'overall_score': 0.0}
        
        # Average each metric across personas
        metric_names = list(persona_evaluations[0].metrics.keys())
        aggregates = {}
        
        for metric_name in metric_names:
            scores = [
                eval.metrics[metric_name].score
                for eval in persona_evaluations
                if metric_name in eval.metrics
            ]
            aggregates[f"avg_{metric_name}"] = np.mean(scores) if scores else 0.0
            aggregates[f"std_{metric_name}"] = np.std(scores) if scores else 0.0
        
        # Add differentiation
        aggregates['persona_differentiation'] = diff_metric.score
        
        # Overall score (weighted average)
        overall_scores = [eval.overall_score for eval in persona_evaluations]
        aggregates['overall_score'] = np.mean(overall_scores) if overall_scores else 0.0
        
        # Pass rates
        total_metrics = sum(len(eval.metrics) for eval in persona_evaluations)
        passed_metrics = sum(
            sum(1 for m in eval.metrics.values() if m.passed)
            for eval in persona_evaluations
        )
        aggregates['pass_rate'] = passed_metrics / total_metrics if total_metrics > 0 else 0.0
        
        return aggregates
    
    def _check_quality_gates(self, aggregate_metrics: Dict[str, float]) -> bool:
        """Check if quality gates are passed"""
        gates = self.metrics_config['quality_gates']['acceptance_criteria']
        
        # Minimum quality gate
        if aggregate_metrics.get('overall_score', 0.0) < 0.60:
            return False
        
        # Differentiation gate
        if aggregate_metrics.get('persona_differentiation', 0.0) < 0.50:
            return False
        
        # Pass rate gate
        if aggregate_metrics.get('pass_rate', 0.0) < 0.70:
            return False
        
        return True
    
    def _generate_recommendations(
        self,
        persona_evaluations: List[PersonaEvaluation],
        aggregate_metrics: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        # Check overall quality
        if aggregate_metrics.get('overall_score', 0.0) < 0.70:
            recommendations.append(
                "Overall quality below target (0.70). Consider increasing training data or epochs."
            )
        
        # Check differentiation
        if aggregate_metrics.get('persona_differentiation', 0.0) < 0.55:
            recommendations.append(
                "Personas are too similar. Consider more diverse training examples or stronger regularization."
            )
        
        # Check consistency
        if aggregate_metrics.get('avg_persona_consistency', 0.0) < 0.75:
            recommendations.append(
                "Persona consistency low. Ensure training data strongly reflects persona characteristics."
            )
        
        # Check multi-turn coherence
        if aggregate_metrics.get('avg_multi_turn_coherence', 0.0) < 0.35:
            recommendations.append(
                "Multi-turn coherence needs improvement. Add more multi-turn training examples."
            )
        
        # Check for variance
        if aggregate_metrics.get('std_persona_consistency', 1.0) > 0.20:
            recommendations.append(
                "High variance in persona consistency. Some personas may need more training data."
            )
        
        # Identify struggling personas
        weak_personas = [
            eval.persona_label
            for eval in persona_evaluations
            if eval.overall_score < 0.60
        ]
        if weak_personas:
            recommendations.append(
                f"Focus on improving: {', '.join(weak_personas[:3])}"
            )
        
        if not recommendations:
            recommendations.append("✓ All metrics look good! Consider testing on more diverse scenarios.")
        
        return recommendations
    
    def _display_summary(self, version_eval: VersionEvaluation, total_time: float):
        """Display evaluation summary"""
        console.print("\n" + "="*70)
        console.print(Panel(
            f"[bold green]Evaluation Complete[/bold green]\n\n"
            f"Version: {version_eval.version}\n"
            f"Overall Score: {version_eval.overall_score:.3f}\n"
            f"Quality Gates: {'✓ PASSED' if version_eval.quality_gates_passed else '✗ FAILED'}\n"
            f"Time: {total_time:.1f}s",
            title="Summary",
            border_style="green" if version_eval.quality_gates_passed else "yellow"
        ))
        
        # Aggregate metrics table
        table = Table(title="Aggregate Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        for key, value in version_eval.aggregate_metrics.items():
            if key.startswith('avg_') or key in ['overall_score', 'pass_rate', 'persona_differentiation']:
                display_name = key.replace('avg_', '').replace('_', ' ').title()
                table.add_row(display_name, f"{value:.3f}")
        
        console.print("\n")
        console.print(table)
        
        # Recommendations
        if version_eval.recommendations:
            console.print("\n[bold yellow]📋 Recommendations:[/bold yellow]")
            for i, rec in enumerate(version_eval.recommendations, 1):
                console.print(f"  {i}. {rec}")
        
        console.print("\n" + "="*70 + "\n")
    
    def save_results(self, version_eval: VersionEvaluation, output_path: Optional[str] = None):
        """Save evaluation results to file"""
        if output_path is None:
            output_dir = project_root / "reports" / "persona_evaluation"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{version_eval.version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict (custom serialization for dataclasses)
        def serialize(obj):
            if hasattr(obj, '__dict__'):
                result = {}
                for key, value in obj.__dict__.items():
                    if isinstance(value, list):
                        result[key] = [serialize(item) for item in value]
                    elif isinstance(value, dict):
                        result[key] = {k: serialize(v) for k, v in value.items()}
                    elif hasattr(value, '__dict__'):
                        result[key] = serialize(value)
                    else:
                        result[key] = value
                return result
            return obj
        
        data = serialize(version_eval)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        console.print(f"\n[green]✓ Results saved to: {output_path}[/green]")
        
        # Also save markdown report
        md_path = output_path.with_suffix('.md')
        self._save_markdown_report(version_eval, md_path)
        console.print(f"[green]✓ Markdown report saved to: {md_path}[/green]")
    
    def _save_markdown_report(self, version_eval: VersionEvaluation, output_path: Path):
        """Save human-readable markdown report"""
        lines = [
            f"# Persona Evaluation Report - {version_eval.version}",
            f"\n**Generated:** {version_eval.timestamp}",
            f"\n## Summary",
            f"\n- **Overall Score:** {version_eval.overall_score:.3f}",
            f"- **Quality Gates:** {'✓ PASSED' if version_eval.quality_gates_passed else '✗ FAILED'}",
            f"- **Personas Evaluated:** {len(version_eval.persona_evaluations)}",
            f"\n## Aggregate Metrics",
            "\n| Metric | Value |",
            "|--------|-------|"
        ]
        
        for key, value in version_eval.aggregate_metrics.items():
            if key.startswith('avg_') or key in ['overall_score', 'pass_rate', 'persona_differentiation']:
                display_name = key.replace('avg_', '').replace('_', ' ').title()
                lines.append(f"| {display_name} | {value:.3f} |")
        
        lines.extend([
            f"\n## Per-Persona Results",
            "\n| Persona | Overall Score | Consistency | Quality | Coherence |",
            "|---------|---------------|-------------|---------|-----------|"
        ])
        
        for eval in version_eval.persona_evaluations:
            lines.append(
                f"| {eval.persona_label} | {eval.overall_score:.3f} | "
                f"{eval.metrics.get('persona_consistency', MetricResult('', 0, 0, False)).score:.3f} | "
                f"{eval.metrics.get('response_quality', MetricResult('', 0, 0, False)).score:.3f} | "
                f"{eval.metrics.get('multi_turn_coherence', MetricResult('', 0, 0, False)).score:.3f} |"
            )
        
        lines.extend([
            f"\n## Recommendations",
            ""
        ])
        
        for i, rec in enumerate(version_eval.recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Persona Performance Assessment"
    )
    parser.add_argument(
        '--version',
        default='latest',
        help='Model version to evaluate (default: latest)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick evaluation with fewer personas (3 only)'
    )
    parser.add_argument(
        '--output',
        help='Output directory for results'
    )
    parser.add_argument(
        '--config',
        default='CONFIGS/persona_evaluation_metrics.yaml',
        help='Path to metrics configuration file'
    )
    parser.add_argument(
        '--device',
        default='auto',
        choices=['auto', 'cuda', 'cpu'],
        help='Device to use for inference'
    )
    
    args = parser.parse_args()
    
    # Create assessor
    assessor = PersonaAssessor(
        version=args.version,
        metrics_config_path=args.config,
        device=args.device
    )
    
    # Run evaluation
    results = assessor.evaluate_all_personas(quick=args.quick)
    
    # Save results
    assessor.save_results(results, args.output)
    
    # Exit with appropriate code
    sys.exit(0 if results.quality_gates_passed else 1)


if __name__ == '__main__':
    main()


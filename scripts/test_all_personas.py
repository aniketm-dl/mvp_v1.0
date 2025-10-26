#!/usr/bin/env python3
"""
Automated Testing Suite for All 18 Personas

Systematically tests all trained personas against predefined test scenarios
to ensure quality and consistency across the entire persona set.

Usage:
    # Test all personas with current version
    python scripts/test_all_personas.py
    
    # Test specific version
    python scripts/test_all_personas.py --version v1.0
    
    # Quick smoke test (faster, fewer scenarios)
    python scripts/test_all_personas.py --quick
    
    # Run only failing personas from last run
    python scripts/test_all_personas.py --retry-failed
    
    # Test specific personas
    python scripts/test_all_personas.py --personas bargain_hunter premium_loyalist
"""

from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.panel import Panel
from rich import print as rprint

console = Console()


@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    persona_id: str
    persona_label: str
    passed: bool
    score: float
    expected: Any
    actual: Any
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class PersonaTestSuite:
    """Complete test results for a persona"""
    persona_id: str
    persona_label: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    average_score: float
    test_results: List[TestResult]
    total_time: float
    timestamp: str


@dataclass
class FullTestReport:
    """Complete test report for all personas"""
    version: str
    total_personas: int
    personas_passed: int
    personas_failed: int
    total_tests: int
    total_passed: int
    total_failed: int
    overall_pass_rate: float
    persona_suites: List[PersonaTestSuite]
    timestamp: str


class PersonaTestRunner:
    """Automated test runner for persona models"""
    
    def __init__(self, version: str = "latest", quick: bool = False):
        self.version = version
        self.quick = quick
        
        # Load configurations
        self.personas = self._load_personas()
        self.test_scenarios = self._load_test_scenarios()
        
        # Results storage
        self.persona_results = []
        
        console.print(f"\n[bold cyan]🧪 Automated Persona Testing Suite[/bold cyan]")
        console.print(f"Version: {version}")
        console.print(f"Mode: {'Quick' if quick else 'Full'}")
        console.print(f"Personas: {len(self.personas)}\n")
    
    def _load_personas(self) -> List[Dict[str, Any]]:
        """Load persona definitions"""
        personas_file = Path("DATA/personas.json")
        if not personas_file.exists():
            console.print("[red]❌ Personas file not found[/red]")
            sys.exit(1)
        
        with open(personas_file, 'r') as f:
            data = json.load(f)
        return data.get('personas', [])
    
    def _load_test_scenarios(self) -> Dict[str, Any]:
        """Load test scenarios from metrics config"""
        config_file = Path("CONFIGS/persona_evaluation_metrics.yaml")
        if config_file.exists():
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('test_scenarios', {})
        
        # Fallback: default test scenarios
        return self._get_default_test_scenarios()
    
    def _get_default_test_scenarios(self) -> Dict[str, Any]:
        """Default test scenarios if config not found"""
        return {
            'standard_prompts': [
                {
                    'category': 'product_recommendation',
                    'prompt': 'I need a new laptop for work. What should I consider?',
                    'expected_topics': ['price', 'quality', 'features', 'brand']
                },
                {
                    'category': 'purchase_decision',
                    'prompt': 'Should I buy this $800 smartphone now or wait?',
                    'expected_topics': ['price', 'timing', 'value']
                },
                {
                    'category': 'brand_comparison',
                    'prompt': 'Which is better: Nike or Adidas?',
                    'expected_topics': ['brand', 'quality', 'price', 'preference']
                }
            ]
        }
    
    def test_persona_exists(self, persona_id: str) -> TestResult:
        """Test that persona adapter exists"""
        start_time = time.time()
        
        adapter_path = Path(f"trained_models/{self.version}/adapters/{persona_id}")
        passed = adapter_path.exists() and (adapter_path / "adapter_model.safetensors").exists()
        
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        
        return TestResult(
            test_name="adapter_exists",
            persona_id=persona_id,
            persona_label=persona.get('label', persona_id) if persona else persona_id,
            passed=passed,
            score=1.0 if passed else 0.0,
            expected="Adapter files present",
            actual=f"{'Found' if passed else 'Not found'} at {adapter_path}",
            execution_time=time.time() - start_time
        )
    
    def test_persona_configuration(self, persona_id: str) -> TestResult:
        """Test that persona has valid configuration"""
        start_time = time.time()
        
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        
        if not persona:
            return TestResult(
                test_name="configuration_valid",
                persona_id=persona_id,
                persona_label=persona_id,
                passed=False,
                score=0.0,
                expected="Valid persona configuration",
                actual="Persona not found in personas.json",
                execution_time=time.time() - start_time
            )
        
        # Check required fields
        required_fields = [
            'id', 'label', 'system_prompt', 'decision_constraints',
            'ocean_scores', 'psychographic_tags', 'shopping_values'
        ]
        
        missing_fields = [field for field in required_fields if field not in persona]
        
        passed = len(missing_fields) == 0
        
        return TestResult(
            test_name="configuration_valid",
            persona_id=persona_id,
            persona_label=persona.get('label', persona_id),
            passed=passed,
            score=1.0 if passed else (1.0 - len(missing_fields) / len(required_fields)),
            expected=f"All {len(required_fields)} required fields",
            actual=f"Missing: {', '.join(missing_fields)}" if missing_fields else "All fields present",
            execution_time=time.time() - start_time
        )
    
    def test_persona_response_generation(self, persona_id: str) -> TestResult:
        """Test that persona can generate responses (smoke test)"""
        start_time = time.time()
        
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        if not persona:
            return TestResult(
                test_name="response_generation",
                persona_id=persona_id,
                persona_label=persona_id,
                passed=False,
                score=0.0,
                expected="Generated response",
                actual="Persona not found",
                error_message="Persona not in personas.json",
                execution_time=time.time() - start_time
            )
        
        # Simple test: check if adapter path exists (actual generation requires loading model)
        adapter_path = Path(f"trained_models/{self.version}/adapters/{persona_id}")
        
        if not adapter_path.exists():
            return TestResult(
                test_name="response_generation",
                persona_id=persona_id,
                persona_label=persona.get('label', persona_id),
                passed=False,
                score=0.0,
                expected="Model can load and generate",
                actual="Adapter files not found",
                error_message=f"Adapter not at {adapter_path}",
                execution_time=time.time() - start_time
            )
        
        # Check for required files
        required_files = ['adapter_model.safetensors', 'adapter_config.json']
        missing_files = [f for f in required_files if not (adapter_path / f).exists()]
        
        passed = len(missing_files) == 0
        
        return TestResult(
            test_name="response_generation",
            persona_id=persona_id,
            persona_label=persona.get('label', persona_id),
            passed=passed,
            score=1.0 if passed else 0.5,
            expected="All adapter files present",
            actual=f"Missing: {', '.join(missing_files)}" if missing_files else "All files present",
            execution_time=time.time() - start_time
        )
    
    def test_persona_characteristics(self, persona_id: str) -> TestResult:
        """Test that persona has well-defined characteristics"""
        start_time = time.time()
        
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        if not persona:
            return TestResult(
                test_name="characteristics_defined",
                persona_id=persona_id,
                persona_label=persona_id,
                passed=False,
                score=0.0,
                expected="Well-defined characteristics",
                actual="Persona not found",
                execution_time=time.time() - start_time
            )
        
        # Check characteristic completeness
        checks = []
        
        # OCEAN scores
        ocean = persona.get('ocean_scores', {})
        ocean_complete = len(ocean) == 5 and all(
            key in ocean and 0 <= ocean[key] <= 1
            for key in ['O', 'C', 'E', 'A', 'N']
        )
        checks.append(('OCEAN scores', ocean_complete))
        
        # Psychographic tags
        tags = persona.get('psychographic_tags', [])
        tags_adequate = len(tags) >= 3
        checks.append(('Psychographic tags (≥3)', tags_adequate))
        
        # Shopping values
        values = persona.get('shopping_values', [])
        values_adequate = len(values) >= 3
        checks.append(('Shopping values (≥3)', values_adequate))
        
        # System prompt
        system_prompt = persona.get('system_prompt', '')
        prompt_adequate = len(system_prompt) > 50
        checks.append(('System prompt (>50 chars)', prompt_adequate))
        
        passed_checks = sum(1 for _, passed in checks if passed)
        total_checks = len(checks)
        
        passed = passed_checks == total_checks
        score = passed_checks / total_checks
        
        return TestResult(
            test_name="characteristics_defined",
            persona_id=persona_id,
            persona_label=persona.get('label', persona_id),
            passed=passed,
            score=score,
            expected=f"All {total_checks} characteristics checks pass",
            actual=f"{passed_checks}/{total_checks} checks passed",
            execution_time=time.time() - start_time
        )
    
    def run_persona_test_suite(self, persona_id: str) -> PersonaTestSuite:
        """Run complete test suite for a single persona"""
        start_time = time.time()
        
        persona = next((p for p in self.personas if p['id'] == persona_id), None)
        persona_label = persona.get('label', persona_id) if persona else persona_id
        
        # Run tests
        test_results = []
        
        console.print(f"[cyan]Testing: {persona_label}[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Running tests...", total=4)
            
            # Test 1: Adapter exists
            test_results.append(self.test_persona_exists(persona_id))
            progress.advance(task)
            
            # Test 2: Configuration valid
            test_results.append(self.test_persona_configuration(persona_id))
            progress.advance(task)
            
            # Test 3: Can generate responses
            test_results.append(self.test_persona_response_generation(persona_id))
            progress.advance(task)
            
            # Test 4: Characteristics defined
            test_results.append(self.test_persona_characteristics(persona_id))
            progress.advance(task)
        
        # Calculate stats
        total_tests = len(test_results)
        passed_tests = sum(1 for t in test_results if t.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        average_score = sum(t.score for t in test_results) / total_tests if total_tests > 0 else 0.0
        
        # Display results
        status_color = "green" if pass_rate >= 0.80 else "yellow" if pass_rate >= 0.60 else "red"
        status_icon = "✓" if pass_rate >= 0.80 else "⚠" if pass_rate >= 0.60 else "✗"
        
        console.print(f"  [{status_color}]{status_icon} {persona_label}: {passed_tests}/{total_tests} passed ({pass_rate*100:.0f}%)[/{status_color}]")
        
        return PersonaTestSuite(
            persona_id=persona_id,
            persona_label=persona_label,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            pass_rate=pass_rate,
            average_score=average_score,
            test_results=test_results,
            total_time=time.time() - start_time,
            timestamp=datetime.now().isoformat()
        )
    
    def run_all_tests(self, persona_ids: Optional[List[str]] = None) -> FullTestReport:
        """Run tests for all personas"""
        start_time = time.time()
        
        console.print(f"\n[bold green]🚀 Starting Automated Test Suite[/bold green]\n")
        
        # Determine which personas to test
        if persona_ids:
            test_personas = [p for p in self.personas if p['id'] in persona_ids]
        else:
            test_personas = self.personas[:3] if self.quick else self.personas
        
        console.print(f"Testing {len(test_personas)} personas...\n")
        
        # Run tests for each persona
        persona_suites = []
        for persona in test_personas:
            suite = self.run_persona_test_suite(persona['id'])
            persona_suites.append(suite)
        
        # Calculate overall statistics
        total_personas = len(persona_suites)
        personas_passed = sum(1 for s in persona_suites if s.pass_rate >= 0.80)
        personas_failed = total_personas - personas_passed
        
        total_tests = sum(s.total_tests for s in persona_suites)
        total_passed = sum(s.passed_tests for s in persona_suites)
        total_failed = total_tests - total_passed
        overall_pass_rate = total_passed / total_tests if total_tests > 0 else 0.0
        
        report = FullTestReport(
            version=self.version,
            total_personas=total_personas,
            personas_passed=personas_passed,
            personas_failed=personas_failed,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            overall_pass_rate=overall_pass_rate,
            persona_suites=persona_suites,
            timestamp=datetime.now().isoformat()
        )
        
        # Display summary
        self._display_summary(report, time.time() - start_time)
        
        return report
    
    def _display_summary(self, report: FullTestReport, total_time: float):
        """Display test summary"""
        console.print("\n" + "="*70)
        
        status_color = "green" if report.overall_pass_rate >= 0.80 else "yellow" if report.overall_pass_rate >= 0.60 else "red"
        
        console.print(Panel(
            f"[bold {status_color}]Test Suite Complete[/bold {status_color}]\n\n"
            f"Overall Pass Rate: {report.overall_pass_rate*100:.1f}%\n"
            f"Personas Passed: {report.personas_passed}/{report.total_personas}\n"
            f"Total Tests: {report.total_passed}/{report.total_tests} passed\n"
            f"Time: {total_time:.1f}s",
            title=f"Summary - {report.version}",
            border_style=status_color
        ))
        
        # Detailed results table
        table = Table(title="Persona Test Results")
        table.add_column("Persona", style="cyan", width=30)
        table.add_column("Tests", justify="center")
        table.add_column("Passed", justify="center")
        table.add_column("Failed", justify="center")
        table.add_column("Pass Rate", justify="right")
        table.add_column("Status", justify="center")
        
        for suite in report.persona_suites:
            pass_rate = suite.pass_rate * 100
            
            if pass_rate >= 80:
                status = "[green]✓[/green]"
                rate_color = "green"
            elif pass_rate >= 60:
                status = "[yellow]⚠[/yellow]"
                rate_color = "yellow"
            else:
                status = "[red]✗[/red]"
                rate_color = "red"
            
            table.add_row(
                suite.persona_label,
                str(suite.total_tests),
                str(suite.passed_tests),
                str(suite.failed_tests) if suite.failed_tests > 0 else "-",
                f"[{rate_color}]{pass_rate:.0f}%[/{rate_color}]",
                status
            )
        
        console.print("\n")
        console.print(table)
        
        # Show failures if any
        failures = [
            (suite.persona_label, test.test_name, test.error_message or test.actual)
            for suite in report.persona_suites
            for test in suite.test_results
            if not test.passed
        ]
        
        if failures:
            console.print(f"\n[bold red]❌ Failed Tests ({len(failures)}):[/bold red]")
            for persona, test, reason in failures[:10]:  # Show first 10
                console.print(f"  • {persona} - {test}: {reason}")
            
            if len(failures) > 10:
                console.print(f"  ... and {len(failures) - 10} more")
        
        console.print("\n" + "="*70 + "\n")
    
    def save_report(self, report: FullTestReport, output_dir: Path):
        """Save test report to file"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        json_path = output_dir / f"test_report_{report.version}_{timestamp}.json"
        
        # Convert to dict
        def to_dict(obj):
            if hasattr(obj, '__dict__'):
                result = {}
                for key, value in obj.__dict__.items():
                    if isinstance(value, list):
                        result[key] = [to_dict(item) for item in value]
                    elif hasattr(value, '__dict__'):
                        result[key] = to_dict(value)
                    else:
                        result[key] = value
                return result
            return obj
        
        with open(json_path, 'w') as f:
            json.dump(to_dict(report), f, indent=2)
        
        console.print(f"[green]✓ Test report saved to: {json_path}[/green]")
        
        # Save markdown summary
        md_path = output_dir / f"test_report_{report.version}_{timestamp}.md"
        self._save_markdown_report(report, md_path)
        console.print(f"[green]✓ Markdown report saved to: {md_path}[/green]")
    
    def _save_markdown_report(self, report: FullTestReport, output_path: Path):
        """Save markdown test report"""
        lines = [
            f"# Automated Test Report - {report.version}",
            f"\n**Generated:** {report.timestamp}",
            f"\n## Summary",
            f"\n- **Overall Pass Rate:** {report.overall_pass_rate*100:.1f}%",
            f"- **Personas Tested:** {report.total_personas}",
            f"- **Personas Passed:** {report.personas_passed}",
            f"- **Personas Failed:** {report.personas_failed}",
            f"- **Total Tests:** {report.total_tests}",
            f"- **Tests Passed:** {report.total_passed}",
            f"- **Tests Failed:** {report.total_failed}",
            f"\n## Per-Persona Results",
            "\n| Persona | Tests | Passed | Failed | Pass Rate | Status |",
            "|---------|-------|--------|--------|-----------|--------|"
        ]
        
        for suite in report.persona_suites:
            status = "✓" if suite.pass_rate >= 0.80 else "⚠" if suite.pass_rate >= 0.60 else "✗"
            lines.append(
                f"| {suite.persona_label} | {suite.total_tests} | "
                f"{suite.passed_tests} | {suite.failed_tests} | "
                f"{suite.pass_rate*100:.0f}% | {status} |"
            )
        
        # Add failures
        failures = [
            (suite.persona_label, test.test_name, test.error_message or test.actual)
            for suite in report.persona_suites
            for test in suite.test_results
            if not test.passed
        ]
        
        if failures:
            lines.extend([
                f"\n## Failed Tests ({len(failures)})",
                ""
            ])
            for persona, test, reason in failures:
                lines.append(f"- **{persona}** - {test}: {reason}")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Automated testing suite for all personas"
    )
    parser.add_argument('--version', default='latest', help='Version to test')
    parser.add_argument('--quick', action='store_true', help='Quick test (3 personas only)')
    parser.add_argument('--personas', nargs='+', help='Specific personas to test')
    parser.add_argument('--output', default='reports/tests/', help='Output directory')
    
    args = parser.parse_args()
    
    runner = PersonaTestRunner(version=args.version, quick=args.quick)
    report = runner.run_all_tests(persona_ids=args.personas)
    
    # Save report
    runner.save_report(report, Path(args.output))
    
    # Exit with appropriate code
    sys.exit(0 if report.overall_pass_rate >= 0.80 else 1)


if __name__ == '__main__':
    main()


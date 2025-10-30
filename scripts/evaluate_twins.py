#!/usr/bin/env python3
"""
Run comprehensive evaluation of airline twins.
Phase 5: Generate detailed evaluation report with all test results.

Usage:
    python scripts/evaluate_twins.py
    python scripts/evaluate_twins.py --save-report DATA/airline/evaluation_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.airline.evaluator import TwinEvaluator


def generate_markdown_report(report, output_path: Path):
    """Generate a detailed markdown report."""

    lines = [
        "# Airline Digital Twin Evaluation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"**Overall Status:** {'✅ PASSED' if report.overall_passed() else '❌ FAILED'}",
        "",
        "| Test Category | Passed | Total | Pass Rate | Target |",
        "|--------------|--------|-------|-----------|--------|",
        f"| Monotonicity | {report.passed_count('monotonicity')} | {report.total_count('monotonicity')} | {report.pass_rate('monotonicity')*100:.0f}% | ≥95% |",
        f"| Face Validity | {report.passed_count('face_validity')} | {report.total_count('face_validity')} | {report.pass_rate('face_validity')*100:.0f}% | ≥95% |",
        f"| Stability | {report.passed_count('stability')} | {report.total_count('stability')} | {report.pass_rate('stability')*100:.0f}% | 100% |",
        "",
        "---",
        "",
        "## 1. Monotonicity Tests",
        "",
        "**Purpose:** Verify that higher discounts do not decrease acceptance probability.",
        "",
        "**Methodology:** Test each twin across increasing discount levels (10%, 20%, 30%, 40%) and ensure probabilities are non-decreasing (with 5% tolerance).",
        ""
    ]

    for result in report.monotonicity_results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        lines.append(f"### {result.details['twin_id']} - {result.details['offer']}")
        lines.append(f"**Status:** {status}")
        lines.append("")
        lines.append("| Discount | Probability |")
        lines.append("|----------|-------------|")
        for discount, prob in zip(result.details['discounts'], result.details['probabilities']):
            lines.append(f"| {discount*100:.0f}% | {prob:.3f} |")
        lines.append("")

        if result.details['violations']:
            lines.append("**Violations:**")
            for v in result.details['violations']:
                lines.append(f"- {v['discount_from']*100:.0f}% → {v['discount_to']*100:.0f}%: probability dropped from {v['prob_from']:.3f} to {v['prob_to']:.3f} (Δ={v['drop']:.3f})")
            lines.append("")
        else:
            lines.append("✅ No violations detected.")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 2. Face Validity Tests",
        "",
        "**Purpose:** Verify that twins with specific traits behave as expected relative to each other.",
        "",
        "**Methodology:** Compare acceptance probabilities between twins with different psychographic profiles for relevant offers.",
        ""
    ])

    for result in report.face_validity_results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        details = result.details

        lines.append(f"### {details['scenario']}")
        lines.append(f"**Status:** {status}")
        lines.append("")
        lines.append(f"- **Twin A:** {details['twin_a']} (Probability: {details['prob_a']:.3f})")
        lines.append(f"- **Twin B:** {details['twin_b']} (Probability: {details['prob_b']:.3f})")
        lines.append(f"- **Expected:** {details['expected_ordering']}")
        lines.append(f"- **Difference:** {details['actual_difference']:.3f}")
        lines.append("")

        if result.passed:
            lines.append("✅ Expectation met: behavior aligns with twin characteristics.")
        else:
            lines.append("❌ Expectation not met: twins behaved contrary to their profiles.")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Stability Tests",
        "",
        "**Purpose:** Verify that decisions are deterministic when using the same random seed.",
        "",
        "**Methodology:** Run the same decision 3 times with the same seed and ensure identical results.",
        ""
    ])

    for result in report.stability_results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        details = result.details

        lines.append(f"### {details['twin_id']}")
        lines.append(f"**Status:** {status}")
        lines.append("")
        lines.append(f"- **Offer:** {details['offer']}")
        lines.append(f"- **Discount:** {details['discount']*100:.0f}%")
        lines.append(f"- **Seed:** {details['seed']}")
        lines.append(f"- **Trials:** {details['num_trials']}")
        lines.append("")
        lines.append("**Results:**")
        for i, prob in enumerate(details['probabilities'], 1):
            lines.append(f"- Trial {i}: {prob:.6f}")
        lines.append("")

        if result.passed:
            lines.append("✅ All trials produced identical results (deterministic).")
        else:
            lines.append("❌ Results varied across trials (non-deterministic).")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Conclusions",
        ""
    ])

    if report.overall_passed():
        lines.extend([
            "### ✅ All Critical Tests Passed",
            "",
            "The airline digital twin system demonstrates:",
            "",
            "1. **Rational behavior:** Twins respond more favorably to larger discounts (monotonicity)",
            "2. **Realistic preferences:** Twins with specific traits (e.g., comfort-seeking) behave as expected (face validity)",
            "3. **Reproducibility:** Decisions are deterministic and stable across repeated queries (stability)",
            "",
            "The system is ready for production use and further evaluation with real-world scenarios."
        ])
    else:
        lines.extend([
            "### ❌ Some Tests Failed",
            "",
            "**Issues Detected:**",
            ""
        ])

        if report.pass_rate('monotonicity') < 0.95:
            lines.append("- **Monotonicity failures:** Some twins show decreased acceptance at higher discounts")
        if report.pass_rate('face_validity') < 0.95:
            lines.append("- **Face validity failures:** Some twins behave contrary to their profile traits")
        if report.pass_rate('stability') < 1.0:
            lines.append("- **Stability failures:** Non-deterministic behavior detected")

        lines.extend([
            "",
            "**Recommendations:**",
            "",
            "1. Review failed test cases and twin prompts",
            "2. Adjust temperature settings or use a different LLM model",
            "3. Refine cohort prior hints for better grounding",
            "4. Add more explicit instructions in system prompts"
        ])

    lines.extend([
        "",
        "---",
        "",
        f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ])

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive evaluation of airline twins"
    )

    parser.add_argument(
        "--save-report",
        type=str,
        default=None,
        help="Save detailed markdown report to file"
    )

    parser.add_argument(
        "--save-json",
        type=str,
        default=None,
        help="Save results as JSON"
    )

    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    config_path = project_root / "CONFIGS" / "airline" / "twin_config.yaml"
    templates_dir = project_root / "PROMPTS" / "airline"
    twins_dir = project_root / "DATA" / "airline" / "twins"

    # Create evaluator
    print("Initializing evaluator...")
    evaluator = TwinEvaluator(config_path, templates_dir, twins_dir)

    # Run evaluation
    print("\nRunning evaluation suite...")
    print("This may take a few minutes as we call the LLM API multiple times...")
    print("")

    report = evaluator.run_all_tests()

    # Save markdown report
    if args.save_report:
        output_path = Path(args.save_report)
        print(f"\nGenerating detailed report: {output_path}")
        generate_markdown_report(report, output_path)
        print(f"✅ Report saved!")

    # Save JSON
    if args.save_json:
        output_path = Path(args.save_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert report to dict
        report_dict = {
            "timestamp": datetime.now().isoformat(),
            "overall_passed": report.overall_passed(),
            "monotonicity": {
                "passed": report.passed_count("monotonicity"),
                "total": report.total_count("monotonicity"),
                "pass_rate": report.pass_rate("monotonicity"),
                "results": [
                    {
                        "test_name": r.test_name,
                        "passed": r.passed,
                        "details": r.details,
                        "message": r.message
                    }
                    for r in report.monotonicity_results
                ]
            },
            "face_validity": {
                "passed": report.passed_count("face_validity"),
                "total": report.total_count("face_validity"),
                "pass_rate": report.pass_rate("face_validity"),
                "results": [
                    {
                        "test_name": r.test_name,
                        "passed": r.passed,
                        "details": r.details,
                        "message": r.message
                    }
                    for r in report.face_validity_results
                ]
            },
            "stability": {
                "passed": report.passed_count("stability"),
                "total": report.total_count("stability"),
                "pass_rate": report.pass_rate("stability"),
                "results": [
                    {
                        "test_name": r.test_name,
                        "passed": r.passed,
                        "details": r.details,
                        "message": r.message
                    }
                    for r in report.stability_results
                ]
            }
        }

        with open(output_path, "w") as f:
            json.dump(report_dict, f, indent=2)

        print(f"✅ JSON results saved to: {output_path}")

    return 0 if report.overall_passed() else 1


if __name__ == "__main__":
    sys.exit(main())

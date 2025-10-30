"""
Unit tests for airline twin evaluator.
Phase 5: Test evaluation framework functionality.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.airline.evaluator import TestResult, EvaluationReport


def test_test_result_creation():
    """Test TestResult creation."""
    result = TestResult(
        test_name="test_monotonicity_twin_001",
        passed=True,
        details={"twin_id": "twin_001", "discounts": [0.1, 0.2]},
        message="Test passed"
    )

    assert result.test_name == "test_monotonicity_twin_001"
    assert result.passed is True
    assert "twin_id" in result.details


def test_evaluation_report():
    """Test EvaluationReport aggregation."""
    monotonicity_results = [
        TestResult("test1", True, {}, "pass"),
        TestResult("test2", True, {}, "pass"),
        TestResult("test3", False, {}, "fail")
    ]

    face_validity_results = [
        TestResult("test4", True, {}, "pass")
    ]

    stability_results = [
        TestResult("test5", True, {}, "pass"),
        TestResult("test6", True, {}, "pass")
    ]

    report = EvaluationReport(
        monotonicity_results=monotonicity_results,
        face_validity_results=face_validity_results,
        stability_results=stability_results,
        cohort_coherence_results=[]
    )

    # Test counts
    assert report.passed_count("monotonicity") == 2
    assert report.total_count("monotonicity") == 3
    assert report.pass_rate("monotonicity") == 2/3

    assert report.passed_count("face_validity") == 1
    assert report.total_count("face_validity") == 1
    assert report.pass_rate("face_validity") == 1.0

    assert report.passed_count("stability") == 2
    assert report.total_count("stability") == 2
    assert report.pass_rate("stability") == 1.0

    # Test overall pass/fail
    # Should pass: monotonicity 67% (< 95%, should fail)
    assert not report.overall_passed()


def test_evaluation_report_all_pass():
    """Test EvaluationReport when all tests pass."""
    monotonicity_results = [TestResult(f"test{i}", True, {}, "pass") for i in range(20)]
    face_validity_results = [TestResult(f"test{i}", True, {}, "pass") for i in range(10)]
    stability_results = [TestResult(f"test{i}", True, {}, "pass") for i in range(5)]

    report = EvaluationReport(
        monotonicity_results=monotonicity_results,
        face_validity_results=face_validity_results,
        stability_results=stability_results,
        cohort_coherence_results=[]
    )

    assert report.pass_rate("monotonicity") == 1.0
    assert report.pass_rate("face_validity") == 1.0
    assert report.pass_rate("stability") == 1.0
    assert report.overall_passed()


if __name__ == "__main__":
    test_test_result_creation()
    test_evaluation_report()
    test_evaluation_report_all_pass()
    print("✅ All evaluator tests passed!")

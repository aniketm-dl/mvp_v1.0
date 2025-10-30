"""
Evaluation framework for airline twin behavior.
Phase 5: Test monotonicity, face validity, stability, and coherence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.airline.twin_card import load_twin_card, list_twin_cards
from src.airline.schemas import (
    OfferAcceptanceTask,
    DecisionContext,
    create_legroom_offer,
    create_wifi_offer,
    create_lounge_offer,
    create_priority_boarding_offer,
    create_baggage_offer
)
from src.airline.prompt_composer import compose_prompts
from src.airline.llm_gateway import LLMGateway

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result from a single test."""
    test_name: str
    passed: bool
    details: Dict
    message: str


@dataclass
class EvaluationReport:
    """Complete evaluation report."""
    monotonicity_results: List[TestResult]
    face_validity_results: List[TestResult]
    stability_results: List[TestResult]
    cohort_coherence_results: List[TestResult]

    def passed_count(self, category: str) -> int:
        """Count passed tests in a category."""
        results = getattr(self, f"{category}_results")
        return sum(1 for r in results if r.passed)

    def total_count(self, category: str) -> int:
        """Count total tests in a category."""
        results = getattr(self, f"{category}_results")
        return len(results)

    def pass_rate(self, category: str) -> float:
        """Calculate pass rate for a category."""
        total = self.total_count(category)
        if total == 0:
            return 0.0
        return self.passed_count(category) / total

    def overall_passed(self) -> bool:
        """Check if all critical tests passed."""
        return (
            self.pass_rate("monotonicity") >= 0.95 and
            self.pass_rate("face_validity") >= 0.95 and
            self.pass_rate("stability") >= 1.0
        )


class TwinEvaluator:
    """Evaluator for airline twin behavior."""

    def __init__(self, config_path: Path, templates_dir: Path, twins_dir: Path):
        """
        Initialize evaluator.

        Args:
            config_path: Path to twin_config.yaml
            templates_dir: Path to prompt templates
            twins_dir: Path to twin cards directory
        """
        self.config_path = config_path
        self.templates_dir = templates_dir
        self.twins_dir = twins_dir
        self.gateway = LLMGateway(config_path)

        # Load twins
        self.twins = list_twin_cards(twins_dir)
        logger.info(f"Loaded {len(self.twins)} twins for evaluation")

    def get_decision_probability(
        self,
        twin_id: str,
        offer_factory,
        discount_pct: float,
        context: DecisionContext,
        seed: int = 42
    ) -> float:
        """
        Get decision probability for a twin given offer and context.

        Args:
            twin_id: Twin identifier
            offer_factory: Function to create offer
            discount_pct: Discount percentage
            context: Decision context
            seed: Random seed

        Returns:
            Probability of acceptance (0.0 to 1.0)
        """
        # Load twin
        twin = load_twin_card(self.twins_dir / f"{twin_id}.json")

        # Create task
        offer = offer_factory(discount_pct=discount_pct)
        task = OfferAcceptanceTask(offer=offer, context=context)

        # Compose prompts
        system_prompt, user_prompt = compose_prompts(twin, task, self.templates_dir)

        # Get decision
        try:
            decision, metadata = self.gateway.get_decision(
                system_prompt,
                user_prompt,
                seed=seed
            )
            return decision["probability"]

        except Exception as e:
            logger.error(f"Failed to get decision: {e}")
            return 0.5  # Neutral if failed

    def test_monotonicity(
        self,
        twin_id: str,
        offer_factory,
        discounts: List[float],
        context: DecisionContext
    ) -> TestResult:
        """
        Test monotonicity: higher discount should not decrease acceptance probability.

        Args:
            twin_id: Twin to test
            offer_factory: Offer creation function
            discounts: List of discount levels (ascending)
            context: Decision context

        Returns:
            TestResult
        """
        probabilities = []

        for discount in discounts:
            prob = self.get_decision_probability(
                twin_id,
                offer_factory,
                discount,
                context
            )
            probabilities.append(prob)

        # Check monotonicity
        violations = []
        for i in range(len(probabilities) - 1):
            if probabilities[i+1] < probabilities[i] - 0.05:  # Allow 5% tolerance
                violations.append({
                    "discount_from": discounts[i],
                    "discount_to": discounts[i+1],
                    "prob_from": probabilities[i],
                    "prob_to": probabilities[i+1],
                    "drop": probabilities[i] - probabilities[i+1]
                })

        passed = len(violations) == 0

        details = {
            "twin_id": twin_id,
            "offer": offer_factory.__name__,
            "discounts": discounts,
            "probabilities": probabilities,
            "violations": violations
        }

        message = f"Monotonicity test for {twin_id}: {'PASS' if passed else 'FAIL'}"
        if violations:
            message += f" ({len(violations)} violations)"

        return TestResult(
            test_name=f"monotonicity_{twin_id}_{offer_factory.__name__}",
            passed=passed,
            details=details,
            message=message
        )

    def test_face_validity(
        self,
        scenario_name: str,
        twin_a_id: str,
        twin_b_id: str,
        offer_factory,
        discount: float,
        context: DecisionContext,
        expected_ordering: str  # "a_higher" or "b_higher"
    ) -> TestResult:
        """
        Test face validity: certain twins should be more likely to accept certain offers.

        Args:
            scenario_name: Description of scenario
            twin_a_id: First twin
            twin_b_id: Second twin
            offer_factory: Offer creation function
            discount: Discount level
            context: Decision context
            expected_ordering: Which twin should have higher acceptance

        Returns:
            TestResult
        """
        prob_a = self.get_decision_probability(twin_a_id, offer_factory, discount, context)
        prob_b = self.get_decision_probability(twin_b_id, offer_factory, discount, context)

        if expected_ordering == "a_higher":
            passed = prob_a >= prob_b - 0.05  # 5% tolerance
            expected_msg = f"{twin_a_id} >= {twin_b_id}"
        else:
            passed = prob_b >= prob_a - 0.05
            expected_msg = f"{twin_b_id} >= {twin_a_id}"

        details = {
            "scenario": scenario_name,
            "twin_a": twin_a_id,
            "twin_b": twin_b_id,
            "prob_a": prob_a,
            "prob_b": prob_b,
            "expected_ordering": expected_ordering,
            "actual_difference": prob_a - prob_b
        }

        message = f"Face validity '{scenario_name}': {'PASS' if passed else 'FAIL'} " \
                  f"(expected {expected_msg}, got {prob_a:.2f} vs {prob_b:.2f})"

        return TestResult(
            test_name=f"face_validity_{scenario_name}",
            passed=passed,
            details=details,
            message=message
        )

    def test_stability(
        self,
        twin_id: str,
        offer_factory,
        discount: float,
        context: DecisionContext,
        num_trials: int = 3
    ) -> TestResult:
        """
        Test stability: same seed should produce identical results.

        Args:
            twin_id: Twin to test
            offer_factory: Offer creation function
            discount: Discount level
            context: Decision context
            num_trials: Number of repeated trials

        Returns:
            TestResult
        """
        seed = 42
        probabilities = []

        for _ in range(num_trials):
            prob = self.get_decision_probability(
                twin_id,
                offer_factory,
                discount,
                context,
                seed=seed
            )
            probabilities.append(prob)

        # Check if all identical
        passed = all(p == probabilities[0] for p in probabilities)

        details = {
            "twin_id": twin_id,
            "offer": offer_factory.__name__,
            "discount": discount,
            "seed": seed,
            "num_trials": num_trials,
            "probabilities": probabilities,
            "all_identical": passed
        }

        message = f"Stability test for {twin_id}: {'PASS' if passed else 'FAIL'}"
        if not passed:
            message += f" (got {probabilities})"

        return TestResult(
            test_name=f"stability_{twin_id}",
            passed=passed,
            details=details,
            message=message
        )

    def run_monotonicity_tests(self, sample_twins: List[str] = None) -> List[TestResult]:
        """Run monotonicity tests on sample twins."""
        logger.info("=" * 80)
        logger.info("MONOTONICITY TESTS")
        logger.info("=" * 80)

        if sample_twins is None:
            sample_twins = ["twin_001", "twin_002", "twin_006"]

        context = DecisionContext(
            flight_length="medium",
            trip_purpose="business",
            time_pressure="medium",
            recent_delays="minor"
        )

        results = []

        # Test legroom offer across discount range
        discounts = [0.10, 0.20, 0.30, 0.40]

        for twin_id in sample_twins:
            logger.info(f"\nTesting {twin_id} with legroom offer...")
            result = self.test_monotonicity(
                twin_id,
                create_legroom_offer,
                discounts,
                context
            )
            results.append(result)
            logger.info(f"  {result.message}")

        logger.info(f"\n✅ Monotonicity: {sum(r.passed for r in results)}/{len(results)} passed")
        return results

    def run_face_validity_tests(self) -> List[TestResult]:
        """Run face validity tests with curated scenarios."""
        logger.info("=" * 80)
        logger.info("FACE VALIDITY TESTS")
        logger.info("=" * 80)

        context = DecisionContext(
            flight_length="long",
            trip_purpose="business",
            time_pressure="medium",
            recent_delays="minor"
        )

        results = []

        # Scenario 1: Comfort-seeker should accept legroom more than value-conscious
        logger.info("\nScenario 1: Comfort-seeker vs Value-conscious on legroom...")
        result = self.test_face_validity(
            scenario_name="comfort_vs_value_legroom",
            twin_a_id="twin_002",  # Comfort seeker
            twin_b_id="twin_006",  # Value conscious
            offer_factory=create_legroom_offer,
            discount=0.15,
            context=context,
            expected_ordering="a_higher"
        )
        results.append(result)
        logger.info(f"  {result.message}")

        # Scenario 2: Business-oriented should accept priority boarding more than leisure
        logger.info("\nScenario 2: Business vs Leisure on priority boarding...")
        result = self.test_face_validity(
            scenario_name="business_vs_leisure_boarding",
            twin_a_id="twin_009",  # Business-oriented
            twin_b_id="twin_003",  # Leisure
            offer_factory=create_priority_boarding_offer,
            discount=0.15,
            context=context,
            expected_ordering="a_higher"
        )
        results.append(result)
        logger.info(f"  {result.message}")

        logger.info(f"\n✅ Face Validity: {sum(r.passed for r in results)}/{len(results)} passed")
        return results

    def run_stability_tests(self, sample_twins: List[str] = None) -> List[TestResult]:
        """Run stability tests on sample twins."""
        logger.info("=" * 80)
        logger.info("STABILITY TESTS")
        logger.info("=" * 80)

        if sample_twins is None:
            sample_twins = ["twin_001", "twin_005"]

        context = DecisionContext(
            flight_length="medium",
            trip_purpose="business",
            time_pressure="medium",
            recent_delays="minor"
        )

        results = []

        for twin_id in sample_twins:
            logger.info(f"\nTesting {twin_id} stability...")
            result = self.test_stability(
                twin_id,
                create_wifi_offer,
                discount=0.25,
                context=context,
                num_trials=3
            )
            results.append(result)
            logger.info(f"  {result.message}")

        logger.info(f"\n✅ Stability: {sum(r.passed for r in results)}/{len(results)} passed")
        return results

    def run_all_tests(self) -> EvaluationReport:
        """Run complete evaluation suite."""
        logger.info("\n" + "=" * 80)
        logger.info("AIRLINE TWIN EVALUATION SUITE")
        logger.info("=" * 80)

        # Run all test categories
        monotonicity_results = self.run_monotonicity_tests()
        face_validity_results = self.run_face_validity_tests()
        stability_results = self.run_stability_tests()
        cohort_coherence_results = []  # TODO: Implement if needed

        # Create report
        report = EvaluationReport(
            monotonicity_results=monotonicity_results,
            face_validity_results=face_validity_results,
            stability_results=stability_results,
            cohort_coherence_results=cohort_coherence_results
        )

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("EVALUATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Monotonicity:     {report.passed_count('monotonicity')}/{report.total_count('monotonicity')} ({report.pass_rate('monotonicity')*100:.0f}%)")
        logger.info(f"Face Validity:    {report.passed_count('face_validity')}/{report.total_count('face_validity')} ({report.pass_rate('face_validity')*100:.0f}%)")
        logger.info(f"Stability:        {report.passed_count('stability')}/{report.total_count('stability')} ({report.pass_rate('stability')*100:.0f}%)")
        logger.info(f"\nOverall: {'✅ PASSED' if report.overall_passed() else '❌ FAILED'}")
        logger.info("=" * 80)

        return report


def main():
    """Run evaluation suite."""
    # Paths
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "CONFIGS" / "airline" / "twin_config.yaml"
    templates_dir = project_root / "PROMPTS" / "airline"
    twins_dir = project_root / "DATA" / "airline" / "twins"

    # Create evaluator
    evaluator = TwinEvaluator(config_path, templates_dir, twins_dir)

    # Run tests
    report = evaluator.run_all_tests()

    return 0 if report.overall_passed() else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

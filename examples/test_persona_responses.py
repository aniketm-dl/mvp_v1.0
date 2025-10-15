#!/usr/bin/env python3
"""
Test script to evaluate persona response quality with new core logic.

This script:
1. Loads all 18 trained personas
2. Tests them on sample scenarios
3. Evaluates response quality (natural language, no tags, decision-first)
4. Compares different personas' responses to the same scenario
5. Generates a quality report

Usage:
    python examples/test_persona_responses.py
"""

from __future__ import annotations
import numpy as np
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.encoder import encode_cta, project_psychographics, embed_demographics, fuse_joint
from src.models.mixture import load_twin_bank, TwinMixture
from src.models.policy_heads import TwinPolicyHeadSet
from src.reasoning.orchestrator import decide_then_verbalize
from src.reasoning.guardrails import apply_guardrails


class PersonaResponseTester:
    """Test harness for persona response quality."""

    def __init__(self):
        """Initialize tester with policy heads and twin bank."""
        self.policy = TwinPolicyHeadSet()
        self.policy.load()

        try:
            self.twin_bank = load_twin_bank()
            print(f"✅ Loaded {len(self.twin_bank)} twins from twin bank")
        except Exception as e:
            print(f"⚠️  Could not load twin bank: {e}")
            self.twin_bank = {}

        self.test_scenarios = self._create_test_scenarios()
        self.results = []

    def _create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create diverse test scenarios."""
        return [
            {
                "name": "Expensive Premium Product",
                "cta_seq": [{
                    "context": {
                        "price_mean": 150,
                        "promo_badge": False,
                        "delivery_eta_days": 2,
                    },
                    "task": "choose_product"
                }],
                "profile_vec": [0.2, 0.7, 0.9, 0.5, 0.8, 0.8, 0.5],  # Quality-focused, urban
                "offer_feats": np.array([150.0, 0.95, 0.9, 2.0, 0.0], dtype=np.float32),
                "expected_decision": "buy",  # Premium buyer should buy
            },
            {
                "name": "Budget Product with Big Discount",
                "cta_seq": [{
                    "context": {
                        "price_mean": 30,
                        "promo_badge": True,
                        "delivery_eta_days": 5,
                    },
                    "task": "choose_product"
                }],
                "profile_vec": [0.9, 0.2, 0.4, 0.3, 0.4, 0.5, 0.5],  # Budget-conscious
                "offer_feats": np.array([30.0, 0.6, 0.5, 5.0, 0.30], dtype=np.float32),
                "expected_decision": "buy",  # Budget buyer loves discounts
            },
            {
                "name": "Overpriced Average Product",
                "cta_seq": [{
                    "context": {
                        "price_mean": 100,
                        "promo_badge": False,
                        "delivery_eta_days": 7,
                    },
                    "task": "choose_product"
                }],
                "profile_vec": [0.7, 0.4, 0.5, 0.4, 0.5, 0.5, 0.5],  # Average user
                "offer_feats": np.array([100.0, 0.6, 0.5, 7.0, 0.0], dtype=np.float32),
                "expected_decision": "no_buy",  # Should pass
            },
            {
                "name": "Good Deal with Fast Delivery",
                "cta_seq": [{
                    "context": {
                        "price_mean": 60,
                        "promo_badge": True,
                        "delivery_eta_days": 1,
                    },
                    "task": "choose_product"
                }],
                "profile_vec": [0.6, 0.6, 0.7, 0.8, 0.7, 0.8, 0.5],  # Time-conscious
                "offer_feats": np.array([60.0, 0.75, 0.7, 1.0, 0.20], dtype=np.float32),
                "expected_decision": "buy",  # Fast delivery + discount
            },
        ]

    def build_twin_vec_from_scenario(self, scenario: Dict[str, Any]) -> np.ndarray:
        """Build twin embedding from scenario."""
        behavior = encode_cta(scenario["cta_seq"])
        psycho = project_psychographics(scenario["profile_vec"])
        demo = embed_demographics(scenario["profile_vec"])

        # Use legacy concatenation for now (learned fusion not trained yet)
        twin_vec = fuse_joint(behavior, psycho, demo, use_learned_fusion=False)
        return twin_vec

    def test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single scenario."""
        print(f"\n{'='*80}")
        print(f"Testing: {scenario['name']}")
        print('='*80)

        # Build twin vector
        twin_vec = self.build_twin_vec_from_scenario(scenario)

        # Get mixture weights
        if self.twin_bank:
            mixture = TwinMixture(self.twin_bank, tau=0.8)
            weights = mixture.weights(twin_vec)
            primary_twin = mixture.primary(twin_vec)
            print(f"Primary Twin: {primary_twin}")

            # Show top 3 twins
            sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
            print("Top 3 Twins:")
            for twin_id, weight in sorted_weights[:3]:
                print(f"  {twin_id}: {weight:.3f}")
        else:
            primary_twin = "unknown"

        # Decide and verbalize
        payload, text = decide_then_verbalize(
            twin_vec=twin_vec,
            offer_feats=scenario["offer_feats"],
            policy=self.policy,
            guardrails={
                "enabled": True,
                "context_keywords": ["price", "quality", "delivery", "discount"],
                "max_retries": 1,
            }
        )

        # Check guardrails
        cleaned_text, passed_guardrails = apply_guardrails(
            text,
            context_keywords=["price", "quality", "delivery"],
            require_decision_first=True,
        )

        # Print results
        print(f"\nDecision: {payload['decision']} (confidence: {payload['confidence']:.2f})")
        print(f"Expected: {scenario.get('expected_decision', 'N/A')}")
        print(f"Top Factors: {', '.join(payload['top_factors'])}")
        print(f"Response: \"{text}\"")
        print(f"Guardrails: {'✅ PASS' if passed_guardrails else '❌ FAIL'}")

        # Quality checks
        quality_score = self._assess_quality(text, payload)
        print(f"Quality Score: {quality_score}/5")

        result = {
            "scenario": scenario["name"],
            "primary_twin": primary_twin,
            "decision": payload["decision"],
            "expected": scenario.get("expected_decision", "N/A"),
            "confidence": payload["confidence"],
            "response": text,
            "guardrails_passed": passed_guardrails,
            "quality_score": quality_score,
            "top_factors": payload["top_factors"],
        }

        return result

    def _assess_quality(self, text: str, payload: Dict[str, Any]) -> int:
        """Assess response quality (0-5)."""
        score = 0

        # 1. Contains decision word in first sentence
        first_sentence = text.split(".")[0] if "." in text else text
        decision_words = ["yes", "no", "wait", "maybe", "buy", "pass", "consider"]
        if any(word in first_sentence.lower() for word in decision_words):
            score += 1

        # 2. No brackets or tags
        if "[" not in text and "]" not in text:
            score += 1

        # 3. Mentions at least one top factor
        text_lower = text.lower()
        if any(factor.lower() in text_lower for factor in payload["top_factors"]):
            score += 1

        # 4. Reasonable length (10-50 words)
        word_count = len(text.split())
        if 10 <= word_count <= 50:
            score += 1

        # 5. Natural language (not too technical)
        technical_words = ["embedding", "vector", "logit", "softmax", "calibration"]
        if not any(word in text_lower for word in technical_words):
            score += 1

        return score

    def run_all_tests(self):
        """Run all test scenarios."""
        print("\n" + "="*80)
        print("PERSONA RESPONSE QUALITY TEST")
        print("="*80)

        for scenario in self.test_scenarios:
            result = self.test_scenario(scenario)
            self.results.append(result)

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        total_tests = len(self.results)
        passed_guardrails = sum(1 for r in self.results if r["guardrails_passed"])
        avg_quality = sum(r["quality_score"] for r in self.results) / total_tests
        avg_confidence = sum(r["confidence"] for r in self.results) / total_tests

        correct_decisions = sum(
            1 for r in self.results
            if r["expected"] == "N/A" or r["decision"] == r["expected"]
        )

        print(f"\nTotal Tests: {total_tests}")
        print(f"Guardrails Passed: {passed_guardrails}/{total_tests} ({passed_guardrails/total_tests*100:.0f}%)")
        print(f"Average Quality Score: {avg_quality:.2f}/5")
        print(f"Average Confidence: {avg_confidence:.2f}")
        print(f"Decision Accuracy: {correct_decisions}/{total_tests} ({correct_decisions/total_tests*100:.0f}%)")

        print("\nQuality Breakdown:")
        for result in self.results:
            status = "✅" if result["guardrails_passed"] else "❌"
            print(f"  {status} {result['scenario']}: {result['quality_score']}/5")

        print("\n" + "="*80)

        # Save results to JSON
        output_file = Path("artifacts/persona_test_results.json")
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}")

    def test_persona_diversity(self):
        """Test how different personas respond to the same scenario."""
        print("\n" + "="*80)
        print("PERSONA DIVERSITY TEST")
        print("="*80)

        # Use first scenario
        scenario = self.test_scenarios[0]
        print(f"\nScenario: {scenario['name']}")
        print(f"Offer: ${scenario['offer_feats'][0]:.0f}, Quality: {scenario['offer_feats'][1]:.2f}")

        # Test with 3 different persona types
        persona_profiles = [
            {
                "name": "Budget Buyer",
                "profile": [0.9, 0.2, 0.4, 0.3, 0.4, 0.5, 0.5],  # High thrift
            },
            {
                "name": "Premium Buyer",
                "profile": [0.2, 0.7, 0.9, 0.5, 0.8, 0.8, 0.5],  # High quality focus
            },
            {
                "name": "Deal Seeker",
                "profile": [0.7, 0.8, 0.5, 0.6, 0.6, 0.6, 0.5],  # High novelty + thrift
            },
        ]

        print("\nResponses by Persona Type:")
        print("-" * 80)

        for persona in persona_profiles:
            # Modify scenario with this persona's profile
            test_scenario = scenario.copy()
            test_scenario["profile_vec"] = persona["profile"]

            twin_vec = self.build_twin_vec_from_scenario(test_scenario)
            payload, text = decide_then_verbalize(
                twin_vec=twin_vec,
                offer_feats=scenario["offer_feats"],
                policy=self.policy,
            )

            print(f"\n{persona['name']}:")
            print(f"  Decision: {payload['decision']} (confidence: {payload['confidence']:.2f})")
            print(f"  Response: \"{text}\"")


def main():
    """Run persona response tests."""
    tester = PersonaResponseTester()

    # Run main tests
    tester.run_all_tests()

    # Test persona diversity
    tester.test_persona_diversity()

    print("\n✅ Testing complete!")


if __name__ == "__main__":
    main()

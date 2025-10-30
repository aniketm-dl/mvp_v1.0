#!/usr/bin/env python3
"""
Interactive twin comparison tool.
Phase 6: Compare how different twins respond to the same offer.

Usage:
    python scripts/compare_twins.py --twins twin_001,twin_002,twin_006 --offer legroom --discount 0.20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.airline.twin_card import load_twin_card
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

import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


OFFER_FACTORIES = {
    "legroom": create_legroom_offer,
    "wifi": create_wifi_offer,
    "lounge": create_lounge_offer,
    "boarding": create_priority_boarding_offer,
    "baggage": create_baggage_offer
}


def compare_twins(
    twin_ids: list[str],
    offer_factory,
    discount_pct: float,
    context: DecisionContext,
    gateway: LLMGateway,
    templates_dir: Path,
    twins_dir: Path,
    seed: int = 42
):
    """Compare how different twins respond to the same offer."""

    results = []

    for twin_id in twin_ids:
        # Load twin
        twin_path = twins_dir / f"{twin_id}.json"
        twin = load_twin_card(twin_path)

        # Create task
        offer = offer_factory(discount_pct=discount_pct)
        task = OfferAcceptanceTask(offer=offer, context=context)

        # Compose prompts
        system_prompt, user_prompt = compose_prompts(twin, task, templates_dir)

        # Get decision
        try:
            decision, metadata = gateway.get_decision(system_prompt, user_prompt, seed=seed)

            results.append({
                "twin_id": twin.id,
                "twin_label": twin.label,
                "psychographics": twin.psychographics,
                "cohort": twin.cohort_key,
                "decision": decision["decision"],
                "probability": decision["probability"],
                "rationale": decision["rationale"],
                "cohort_satisfaction": twin.cohort_priors.get("satisfaction_rate", "N/A"),
                "price_sensitivity": twin.cohort_priors.get("price_sensitivity", "N/A")
            })

        except Exception as e:
            logger.error(f"Error processing {twin_id}: {e}")

    return results


def display_comparison(results: list[dict], offer_name: str, discount_pct: float):
    """Display comparison in a nice format."""

    logger.info("=" * 100)
    logger.info(f"TWIN COMPARISON: {offer_name.upper()} @ {discount_pct*100:.0f}% OFF")
    logger.info("=" * 100)
    logger.info("")

    # Sort by probability (highest first)
    results_sorted = sorted(results, key=lambda x: x["probability"], reverse=True)

    for i, r in enumerate(results_sorted, 1):
        logger.info(f"#{i}. {r['twin_id']} - {r['twin_label']}")
        logger.info(f"    Decision: {r['decision'].upper()}")
        logger.info(f"    Probability: {r['probability']:.3f}")
        logger.info(f"    Rationale: {r['rationale']}")
        logger.info(f"    Psychographics: {', '.join(r['psychographics']) if r['psychographics'] else 'none'}")
        logger.info(f"    Cohort Satisfaction: {r['cohort_satisfaction']}")
        logger.info(f"    Price Sensitivity: {r['price_sensitivity']}")
        logger.info("")

    # Summary stats
    yes_count = sum(1 for r in results if r["decision"] == "yes")
    avg_prob = sum(r["probability"] for r in results) / len(results)

    logger.info("=" * 100)
    logger.info("SUMMARY")
    logger.info("=" * 100)
    logger.info(f"Acceptance Rate: {yes_count}/{len(results)} ({yes_count/len(results)*100:.0f}%)")
    logger.info(f"Average Probability: {avg_prob:.3f}")
    logger.info("")

    # Insights
    logger.info("INSIGHTS:")

    # Most likely to accept
    most_likely = results_sorted[0]
    logger.info(f"✅ Most likely to accept: {most_likely['twin_label']} ({most_likely['probability']:.3f})")

    # Least likely
    least_likely = results_sorted[-1]
    logger.info(f"❌ Least likely to accept: {least_likely['twin_label']} ({least_likely['probability']:.3f})")

    # Probability spread
    prob_range = results_sorted[0]["probability"] - results_sorted[-1]["probability"]
    logger.info(f"📊 Probability spread: {prob_range:.3f}")

    logger.info("=" * 100)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare twins on same offer")

    parser.add_argument(
        "--twins",
        type=str,
        required=True,
        help="Comma-separated twin IDs (e.g., twin_001,twin_002,twin_006)"
    )

    parser.add_argument(
        "--offer",
        type=str,
        choices=list(OFFER_FACTORIES.keys()),
        required=True,
        help="Offer type"
    )

    parser.add_argument(
        "--discount",
        type=float,
        required=True,
        help="Discount percentage as decimal (e.g., 0.20 for 20%%)"
    )

    parser.add_argument(
        "--flight-length",
        type=str,
        choices=["short", "medium", "long"],
        default="medium"
    )

    parser.add_argument(
        "--trip-purpose",
        type=str,
        choices=["business", "leisure"],
        default="business"
    )

    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    # Parse twin IDs
    twin_ids = [t.strip() for t in args.twins.split(",")]

    # Context
    context = DecisionContext(
        flight_length=args.flight_length,
        trip_purpose=args.trip_purpose,
        time_pressure="medium",
        recent_delays="minor"
    )

    # Paths
    project_root = Path(__file__).parent.parent
    config_path = project_root / "CONFIGS" / "airline" / "twin_config.yaml"
    templates_dir = project_root / "PROMPTS" / "airline"
    twins_dir = project_root / "DATA" / "airline" / "twins"

    # Initialize gateway
    gateway = LLMGateway(config_path)

    # Get offer factory
    offer_factory = OFFER_FACTORIES[args.offer]

    # Run comparison
    logger.info("Running comparison...")
    logger.info("")

    results = compare_twins(
        twin_ids,
        offer_factory,
        args.discount,
        context,
        gateway,
        templates_dir,
        twins_dir,
        args.seed
    )

    # Display
    display_comparison(results, args.offer, args.discount)

    return 0


if __name__ == "__main__":
    sys.exit(main())

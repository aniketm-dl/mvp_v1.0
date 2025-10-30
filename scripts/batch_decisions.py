#!/usr/bin/env python3
"""
Batch decision processing for multiple twins and offers.
Phase 6: Process many decisions at once and compare results.

Usage:
    # Test all twins on single offer
    python scripts/batch_decisions.py --offer legroom --discount 0.20

    # Test single twin on all offers
    python scripts/batch_decisions.py --twin twin_001 --all-offers

    # Full matrix: all twins × all offers
    python scripts/batch_decisions.py --full-matrix --discounts 0.10,0.20,0.30
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.airline.twin_card import list_twin_cards
from src.airline.schemas import (
    OfferAcceptanceTask,
    DecisionContext,
    DecisionResponse,
    TwinDecision,
    create_legroom_offer,
    create_wifi_offer,
    create_lounge_offer,
    create_priority_boarding_offer,
    create_baggage_offer
)
from src.airline.prompt_composer import compose_prompts
from src.airline.llm_gateway import LLMGateway
from src.airline.ledger import DecisionLedger

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


def make_decision(
    gateway: LLMGateway,
    ledger: DecisionLedger,
    twin,
    offer_factory,
    discount_pct: float,
    context: DecisionContext,
    templates_dir: Path,
    seed: int = 42
) -> TwinDecision:
    """Make a single decision and log to ledger."""

    # Create task
    offer = offer_factory(discount_pct=discount_pct)
    task = OfferAcceptanceTask(offer=offer, context=context)

    # Compose prompts
    system_prompt, user_prompt = compose_prompts(twin, task, templates_dir)

    # Get decision
    decision_dict, llm_metadata = gateway.get_decision(
        system_prompt,
        user_prompt,
        seed=seed
    )

    response = DecisionResponse.from_dict(decision_dict)

    # Create full decision record
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "seed": seed,
        "llm_metadata": llm_metadata
    }

    twin_decision = TwinDecision(
        twin_id=twin.id,
        twin_label=twin.label,
        task=task,
        response=response,
        metadata=metadata
    )

    # Log to ledger
    ledger.log_decision(twin_decision.to_dict(), system_prompt, user_prompt)

    return twin_decision


def batch_process(
    twin_ids: list[str],
    offer_names: list[str],
    discounts: list[float],
    context: DecisionContext,
    config_path: Path,
    templates_dir: Path,
    twins_dir: Path,
    ledger_path: Path,
    seed: int = 42
):
    """Process batch of decisions."""

    # Initialize
    gateway = LLMGateway(config_path)
    ledger = DecisionLedger(ledger_path)

    # Count total
    total = len(twin_ids) * len(offer_names) * len(discounts)
    logger.info(f"Processing {total} decisions:")
    logger.info(f"  {len(twin_ids)} twins × {len(offer_names)} offers × {len(discounts)} discounts")
    logger.info("")

    results = []
    count = 0

    for twin_id in twin_ids:
        # Load twin
        twin_path = twins_dir / f"{twin_id}.json"
        from src.airline.twin_card import load_twin_card
        twin = load_twin_card(twin_path)

        logger.info(f"Twin: {twin.label}")

        for offer_name in offer_names:
            offer_factory = OFFER_FACTORIES[offer_name]

            for discount in discounts:
                count += 1

                # Make decision
                try:
                    decision = make_decision(
                        gateway,
                        ledger,
                        twin,
                        offer_factory,
                        discount,
                        context,
                        templates_dir,
                        seed
                    )

                    # Store result
                    results.append({
                        "twin_id": twin.id,
                        "twin_label": twin.label,
                        "offer": offer_name,
                        "discount": discount,
                        "decision": decision.response.decision,
                        "probability": decision.response.probability,
                        "rationale": decision.response.rationale
                    })

                    # Log progress
                    logger.info(f"  [{count}/{total}] {offer_name} @ {discount*100:.0f}% → {decision.response.decision.upper()} ({decision.response.probability:.2f})")

                except Exception as e:
                    logger.error(f"  [{count}/{total}] {offer_name} @ {discount*100:.0f}% → ERROR: {e}")

        logger.info("")

    return results


def display_comparison_table(results: list[dict]):
    """Display results in a comparison table."""

    # Group by offer and discount
    by_offer_discount = {}

    for r in results:
        key = (r["offer"], r["discount"])
        if key not in by_offer_discount:
            by_offer_discount[key] = []
        by_offer_discount[key].append(r)

    # Display each offer/discount combo
    for (offer, discount), items in sorted(by_offer_discount.items()):
        logger.info("=" * 80)
        logger.info(f"{offer.upper()} @ {discount*100:.0f}% OFF")
        logger.info("=" * 80)
        logger.info(f"{'Twin ID':<12} {'Decision':<10} {'Probability':<12} {'Label'}")
        logger.info("-" * 80)

        # Sort by probability descending
        items_sorted = sorted(items, key=lambda x: x["probability"], reverse=True)

        for item in items_sorted:
            logger.info(f"{item['twin_id']:<12} {item['decision']:<10} {item['probability']:<12.2f} {item['twin_label'][:50]}")

        logger.info("")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Batch decision processing")

    parser.add_argument("--twin", type=str, help="Single twin ID")
    parser.add_argument("--all-twins", action="store_true", help="Test all twins")
    parser.add_argument("--offer", type=str, choices=list(OFFER_FACTORIES.keys()), help="Single offer type")
    parser.add_argument("--all-offers", action="store_true", help="Test all offers")
    parser.add_argument("--discounts", type=str, default="0.20", help="Comma-separated discount levels (e.g., 0.10,0.20,0.30)")
    parser.add_argument("--full-matrix", action="store_true", help="All twins × all offers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--flight-length", type=str, choices=["short", "medium", "long"], default="medium")
    parser.add_argument("--trip-purpose", type=str, choices=["business", "leisure"], default="business")

    args = parser.parse_args()

    # Parse discounts
    discounts = [float(d) for d in args.discounts.split(",")]

    # Determine twin IDs
    if args.full_matrix or args.all_twins:
        twin_ids = [f"twin_{i:03d}" for i in range(1, 13)]
    elif args.twin:
        twin_ids = [args.twin]
    else:
        logger.error("Specify --twin, --all-twins, or --full-matrix")
        return 1

    # Determine offers
    if args.full_matrix or args.all_offers:
        offer_names = list(OFFER_FACTORIES.keys())
    elif args.offer:
        offer_names = [args.offer]
    else:
        logger.error("Specify --offer, --all-offers, or --full-matrix")
        return 1

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
    ledger_path = project_root / "DATA" / "airline" / "decisions" / "ledger.csv"

    # Run batch
    logger.info("=" * 80)
    logger.info("BATCH DECISION PROCESSING")
    logger.info("=" * 80)
    logger.info("")

    results = batch_process(
        twin_ids,
        offer_names,
        discounts,
        context,
        config_path,
        templates_dir,
        twins_dir,
        ledger_path,
        args.seed
    )

    # Display comparison
    logger.info("")
    logger.info("=" * 80)
    logger.info("COMPARISON TABLE")
    logger.info("=" * 80)
    logger.info("")

    display_comparison_table(results)

    logger.info(f"✅ Completed {len(results)} decisions")
    logger.info(f"📋 Logged to: {ledger_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

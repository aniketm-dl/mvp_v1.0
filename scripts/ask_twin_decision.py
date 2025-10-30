#!/usr/bin/env python3
"""
Ask a twin to make an offer acceptance decision.
Phase 4: Complete end-to-end twin decision flow.

Usage:
    python scripts/ask_twin_decision.py --twin twin_001 --offer legroom --discount 0.20

"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.airline.twin_card import load_twin_card
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


OFFER_FACTORIES = {
    "legroom": create_legroom_offer,
    "wifi": create_wifi_offer,
    "lounge": create_lounge_offer,
    "boarding": create_priority_boarding_offer,
    "baggage": create_baggage_offer
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Ask an airline twin to make an offer acceptance decision"
    )

    parser.add_argument(
        "--twin",
        type=str,
        required=True,
        help="Twin ID (e.g., twin_001)"
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
        help="Discount percentage as decimal (e.g., 0.20 for 20%% off)"
    )

    parser.add_argument(
        "--flight-length",
        type=str,
        choices=["short", "medium", "long"],
        default="medium",
        help="Flight length context"
    )

    parser.add_argument(
        "--trip-purpose",
        type=str,
        choices=["business", "leisure"],
        default="business",
        help="Trip purpose context"
    )

    parser.add_argument(
        "--time-pressure",
        type=str,
        choices=["low", "medium", "high"],
        default="medium",
        help="Time pressure context"
    )

    parser.add_argument(
        "--recent-delays",
        type=str,
        choices=["none", "minor", "major"],
        default="minor",
        help="Recent delays context"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for determinism"
    )

    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save decision to JSON file"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full prompts"
    )

    return parser.parse_args()


def make_decision(
    twin_id: str,
    offer_type: str,
    discount_pct: float,
    flight_length: str,
    trip_purpose: str,
    time_pressure: str,
    recent_delays: str,
    seed: int = None,
    verbose: bool = False
) -> TwinDecision:
    """
    Make a decision for a twin given an offer and context.

    Args:
        twin_id: Twin identifier
        offer_type: Type of offer
        discount_pct: Discount percentage (0.0 to 1.0)
        flight_length: Flight length context
        trip_purpose: Trip purpose context
        time_pressure: Time pressure context
        recent_delays: Recent delays context
        seed: Optional random seed
        verbose: Show full prompts

    Returns:
        TwinDecision object
    """
    # Paths
    project_root = Path(__file__).parent.parent
    twins_dir = project_root / "DATA" / "airline" / "twins"
    templates_dir = project_root / "PROMPTS" / "airline"
    config_path = project_root / "CONFIGS" / "airline" / "twin_config.yaml"

    # Load twin
    logger.info(f"Loading twin: {twin_id}")
    twin_path = twins_dir / f"{twin_id}.json"

    if not twin_path.exists():
        raise FileNotFoundError(f"Twin not found: {twin_path}")

    twin = load_twin_card(twin_path)
    logger.info(f"  Label: {twin.label}")
    logger.info(f"  Cohort: {twin.cohort_key}")

    # Create offer
    logger.info(f"\nCreating offer: {offer_type} at {discount_pct * 100:.0f}% discount")
    offer_factory = OFFER_FACTORIES[offer_type]
    offer = offer_factory(discount_pct=discount_pct)

    # Create context
    context = DecisionContext(
        flight_length=flight_length,
        trip_purpose=trip_purpose,
        time_pressure=time_pressure,
        recent_delays=recent_delays
    )

    # Create task
    task = OfferAcceptanceTask(offer=offer, context=context)

    # Compose prompts
    logger.info("\nComposing prompts...")
    system_prompt, user_prompt = compose_prompts(twin, task, templates_dir)

    if verbose:
        print("\n" + "=" * 80)
        print("SYSTEM PROMPT")
        print("=" * 80)
        print(system_prompt)
        print("\n" + "=" * 80)
        print("USER PROMPT")
        print("=" * 80)
        print(user_prompt)
        print("=" * 80 + "\n")

    # Initialize LLM gateway
    logger.info("\nInitializing LLM gateway...")
    gateway = LLMGateway(config_path)

    # Get decision
    logger.info("\nCalling LLM...")
    try:
        decision_dict, llm_metadata = gateway.get_decision(
            system_prompt,
            user_prompt,
            seed=seed
        )

        logger.info("✅ Decision received!")

        # Create response object
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

        return twin_decision

    except Exception as e:
        logger.error(f"❌ Decision failed: {e}")
        raise


def main():
    """Main entry point."""
    args = parse_args()

    logger.info("=" * 80)
    logger.info("AIRLINE TWIN DECISION")
    logger.info("=" * 80)

    try:
        # Make decision
        decision = make_decision(
            twin_id=args.twin,
            offer_type=args.offer,
            discount_pct=args.discount,
            flight_length=args.flight_length,
            trip_purpose=args.trip_purpose,
            time_pressure=args.time_pressure,
            recent_delays=args.recent_delays,
            seed=args.seed,
            verbose=args.verbose
        )

        # Display result
        print("\n" + "=" * 80)
        print("DECISION RESULT")
        print("=" * 80)
        print(f"Twin: {decision.twin_label}")
        print(f"Offer: {decision.task.offer.name}")
        print(f"Discount: {decision.task.offer.discount_pct * 100:.0f}% off")
        print(f"Final Price: ${decision.task.offer.absolute_price_delta:.2f}")
        print()
        print(f"Decision: {decision.response.decision.upper()}")
        print(f"Probability: {decision.response.probability:.2f}")
        print(f"Rationale: {decision.response.rationale}")
        print()
        print(f"Context: {decision.task.context.flight_length} {decision.task.context.trip_purpose} flight")
        print(f"Time Pressure: {decision.task.context.time_pressure}")
        print(f"Recent Delays: {decision.task.context.recent_delays}")
        print("=" * 80)

        # Save if requested
        if args.save:
            output_path = Path(args.save)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(decision.to_dict(), f, indent=2)

            logger.info(f"\n💾 Decision saved to: {output_path}")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
Prompt composer for airline twin decisions.
Phase 3: Assemble system and user prompts from templates and data.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.airline.twin_card import TwinCard
    from src.airline.schemas import OfferAcceptanceTask, OfferDetails, DecisionContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_prompt_template(template_path: Path) -> str:
    """Load prompt template from file."""
    with open(template_path, "r") as f:
        return f.read()


def format_twin_profile(twin) -> str:
    """
    Format twin card into human-readable profile text.

    Args:
        twin: TwinCard object

    Returns:
        Formatted profile string
    """
    demo = twin.demographics
    travel = twin.travel_profile
    exp = twin.recent_experience

    profile_lines = [
        f"Passenger ID: {twin.id}",
        f"Description: {twin.label}",
        "",
        "DEMOGRAPHICS:",
        f"  • Gender: {demo.gender}",
        f"  • Age: {demo.age} years old ({demo.age_band})",
        "",
        "TRAVEL PROFILE:",
        f"  • Customer Type: {travel.customer_type}",
        f"  • Typical Travel Purpose: {travel.type_of_travel}",
        f"  • Preferred Class: {travel.flight_class}",
        f"  • Recent Flight Distance: {travel.flight_distance} miles ({travel.distance_band})",
        f"  • Recent Delays: {travel.delay_band}",
        "",
        "BEHAVIORAL PROFILE:",
    ]

    if twin.psychographics:
        for tag in twin.psychographics:
            readable_tag = tag.replace("_", " ").title()
            profile_lines.append(f"  • {readable_tag}")
    else:
        profile_lines.append("  • No specific behavioral tags")

    profile_lines.extend([
        "",
        "RECENT EXPERIENCE (Service Ratings, 1-5 scale):",
        f"  • Inflight WiFi: {exp.inflight_wifi_service}/5",
        f"  • Time Convenience: {exp.departure_arrival_time_convenient}/5",
        f"  • Online Booking: {exp.ease_of_online_booking}/5",
        f"  • Gate Location: {exp.gate_location}/5",
        f"  • Food & Drink: {exp.food_and_drink}/5",
        f"  • Online Boarding: {exp.online_boarding}/5",
        f"  • Seat Comfort: {exp.seat_comfort}/5",
        f"  • Entertainment: {exp.inflight_entertainment}/5",
        f"  • Onboard Service: {exp.on_board_service}/5",
        f"  • Leg Room: {exp.leg_room_service}/5",
        f"  • Baggage Handling: {exp.baggage_handling}/5",
        f"  • Check-in Service: {exp.checkin_service}/5",
        f"  • Inflight Service: {exp.inflight_service}/5",
        f"  • Cleanliness: {exp.cleanliness}/5",
    ])

    return "\n".join(profile_lines)


def format_cohort_insights(twin) -> str:
    """
    Format cohort priors into human-readable insights.

    Args:
        twin: TwinCard with cohort_priors

    Returns:
        Formatted insights string
    """
    priors = twin.cohort_priors

    if not priors:
        return "No cohort insights available."

    insights_lines = [
        f"Based on {priors.get('n', 0)} similar passengers:",
        "",
        f"SATISFACTION PATTERN:",
        f"  • {priors.get('satisfaction_rate', 0) * 100:.0f}% of similar passengers were satisfied",
        "",
    ]

    # Top positive drivers
    if priors.get("top_positive_drivers"):
        insights_lines.append("WHAT DRIVES SATISFACTION (for similar passengers):")
        for driver in priors["top_positive_drivers"][:3]:
            service = driver["service"].replace("_", " ").title()
            insights_lines.append(f"  • {service} (strong positive impact)")
        insights_lines.append("")

    # Top negative drivers
    if priors.get("top_negative_drivers"):
        insights_lines.append("WHAT HURTS SATISFACTION (for similar passengers):")
        for driver in priors["top_negative_drivers"][:3]:
            service = driver["service"].replace("_", " ").title()
            insights_lines.append(f"  • {service} (strong negative impact)")
        insights_lines.append("")

    # Price sensitivity
    price_sensitivity = priors.get("price_sensitivity", "medium")
    insights_lines.extend([
        "PRICE SENSITIVITY:",
        f"  • Similar passengers are: {price_sensitivity.upper()}",
        "",
    ])

    # Discount hints
    if priors.get("discount_ladder_hints"):
        insights_lines.append("TYPICAL ACCEPTANCE THRESHOLDS:")
        for offer_type, threshold in priors["discount_ladder_hints"].items():
            offer_name = offer_type.replace("_", " ").title()
            insights_lines.append(f"  • {offer_name}: typically accept at {threshold * 100:.0f}% discount")
        insights_lines.append("")

    return "\n".join(insights_lines)


def format_offer_details(offer) -> Dict[str, str]:
    """
    Format offer details for template substitution.

    Args:
        offer: OfferDetails object

    Returns:
        Dictionary with formatted offer fields
    """
    original_price = offer.absolute_price_delta / (1 - offer.discount_pct) if offer.discount_pct < 1.0 else offer.absolute_price_delta

    constraints_text = ""
    if offer.constraints:
        constraints_text = "Constraints:\n" + "\n".join([f"  • {c}" for c in offer.constraints])

    return {
        "offer_name": offer.name,
        "offer_type": offer.offer_kind.replace("_", " ").title(),
        "original_price": original_price,
        "discount_pct": offer.discount_pct * 100,
        "final_price": offer.absolute_price_delta,
        "constraints_text": constraints_text,
    }


def format_context_details(context) -> Dict[str, str]:
    """
    Format context details for template substitution.

    Args:
        context: DecisionContext object

    Returns:
        Dictionary with formatted context fields
    """
    return {
        "flight_length": context.flight_length.title(),
        "trip_purpose": context.trip_purpose.title(),
        "time_pressure": context.time_pressure.title(),
        "recent_delays": context.recent_delays.title(),
    }


def compose_prompts(
    twin,
    task,
    templates_dir: Path
) -> Tuple[str, str]:
    """
    Compose system and user prompts for a twin decision.

    Args:
        twin: TwinCard with passenger profile
        task: OfferAcceptanceTask with offer and context
        templates_dir: Directory containing prompt templates

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Load templates
    system_template = load_prompt_template(templates_dir / "system_prompt.txt")
    user_template = load_prompt_template(templates_dir / "user_offer_prompt.txt")

    # Format twin profile and cohort insights
    twin_profile = format_twin_profile(twin)
    cohort_insights = format_cohort_insights(twin)

    # Compose system prompt
    system_prompt = system_template.format(
        twin_profile=twin_profile,
        cohort_insights=cohort_insights
    )

    # Format offer and context
    offer_vars = format_offer_details(task.offer)
    context_vars = format_context_details(task.context)

    # Merge all template variables
    template_vars = {**offer_vars, **context_vars}

    # Compose user prompt
    user_prompt = user_template.format(**template_vars)

    return system_prompt, user_prompt


def main():
    """Test prompt composition with sample twin and task."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from src.airline.twin_card import load_twin_card
    from src.airline.schemas import (
        create_legroom_offer,
        DecisionContext,
        OfferAcceptanceTask
    )

    # Paths
    project_root = Path(__file__).parent.parent.parent
    twins_dir = project_root / "DATA" / "airline" / "twins"
    templates_dir = project_root / "PROMPTS" / "airline"

    # Load first twin
    twin_path = twins_dir / "twin_001.json"
    twin = load_twin_card(twin_path)

    print(f"Loaded twin: {twin.label}")

    # Create sample task
    offer = create_legroom_offer(discount_pct=0.20)
    context = DecisionContext(
        flight_length="long",
        trip_purpose="business",
        time_pressure="medium",
        recent_delays="minor"
    )
    task = OfferAcceptanceTask(offer=offer, context=context)

    # Compose prompts
    system_prompt, user_prompt = compose_prompts(twin, task, templates_dir)

    # Display
    print("\n" + "=" * 80)
    print("SYSTEM PROMPT")
    print("=" * 80)
    print(system_prompt)

    print("\n" + "=" * 80)
    print("USER PROMPT")
    print("=" * 80)
    print(user_prompt)

    print("\n" + "=" * 80)
    print("✅ Prompt composition successful!")
    print("=" * 80)


if __name__ == "__main__":
    main()

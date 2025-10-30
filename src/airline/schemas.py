"""
Schemas for airline twin decision tasks.
Phase 3: Define offer acceptance and decision task structures.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional, Literal


@dataclass
class OfferDetails:
    """Details of an offer being presented to the passenger."""
    name: str  # e.g., "Extra Legroom Seat"
    offer_kind: Literal["upgrade_addon", "service_addon", "priority"]
    discount_pct: float  # 0.0 to 1.0 (e.g., 0.20 = 20% off)
    absolute_price_delta: float  # Price in USD (e.g., 25.00)
    constraints: List[str] = None  # e.g., ["same flight", "subject to availability"]

    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []


@dataclass
class DecisionContext:
    """Context information for the decision."""
    flight_length: Literal["short", "medium", "long"]
    trip_purpose: Literal["business", "leisure"]
    time_pressure: Literal["low", "medium", "high"]
    recent_delays: Literal["none", "minor", "major"]


@dataclass
class OfferAcceptanceTask:
    """
    Complete offer acceptance decision task.

    Represents a question to ask a twin: "Would you accept this offer?"
    """
    task_type: str = "offer_acceptance"
    offer: OfferDetails = None
    context: DecisionContext = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DecisionResponse:
    """
    Response from twin after making a decision.

    This is what we expect the LLM to return.
    """
    decision: Literal["yes", "no"]
    probability: float  # 0.0 to 1.0
    rationale: str  # One-sentence explanation

    @classmethod
    def from_dict(cls, data: dict) -> DecisionResponse:
        """Create from dictionary."""
        return cls(
            decision=data["decision"],
            probability=float(data["probability"]),
            rationale=data["rationale"]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TwinDecision:
    """
    Complete decision record including task, twin info, and response.
    """
    twin_id: str
    twin_label: str
    task: OfferAcceptanceTask
    response: DecisionResponse
    metadata: dict  # timestamps, model used, etc.

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "twin_id": self.twin_id,
            "twin_label": self.twin_label,
            "task": self.task.to_dict(),
            "response": self.response.to_dict(),
            "metadata": self.metadata
        }


# Helper functions for creating common tasks

def create_legroom_offer(discount_pct: float, price: float = 25.0) -> OfferDetails:
    """Create extra legroom offer."""
    return OfferDetails(
        name="Extra Legroom Seat",
        offer_kind="upgrade_addon",
        discount_pct=discount_pct,
        absolute_price_delta=price * (1 - discount_pct),
        constraints=["same flight", "subject to availability"]
    )


def create_wifi_offer(discount_pct: float, price: float = 15.0) -> OfferDetails:
    """Create WiFi access offer."""
    return OfferDetails(
        name="Inflight WiFi Access",
        offer_kind="service_addon",
        discount_pct=discount_pct,
        absolute_price_delta=price * (1 - discount_pct),
        constraints=["full flight duration"]
    )


def create_lounge_offer(discount_pct: float, price: float = 40.0) -> OfferDetails:
    """Create lounge access offer."""
    return OfferDetails(
        name="Airport Lounge Access",
        offer_kind="service_addon",
        discount_pct=discount_pct,
        absolute_price_delta=price * (1 - discount_pct),
        constraints=["3 hours before flight", "subject to availability"]
    )


def create_priority_boarding_offer(discount_pct: float, price: float = 20.0) -> OfferDetails:
    """Create priority boarding offer."""
    return OfferDetails(
        name="Priority Boarding",
        offer_kind="priority",
        discount_pct=discount_pct,
        absolute_price_delta=price * (1 - discount_pct),
        constraints=["board before general passengers"]
    )


def create_baggage_offer(discount_pct: float, price: float = 30.0) -> OfferDetails:
    """Create extra baggage offer."""
    return OfferDetails(
        name="Extra Checked Baggage",
        offer_kind="service_addon",
        discount_pct=discount_pct,
        absolute_price_delta=price * (1 - discount_pct),
        constraints=["one additional checked bag", "up to 50 lbs"]
    )

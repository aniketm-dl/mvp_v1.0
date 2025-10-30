"""
Twin Card data structure for airline passengers.
Phase 2: Define and generate twin persona cards.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class TwinCardDemographics:
    """Demographics section of twin card."""
    gender: str
    age: int
    age_band: str


@dataclass
class TwinCardTravelProfile:
    """Travel profile section of twin card."""
    customer_type: str
    type_of_travel: str
    flight_class: str
    flight_distance: int
    distance_band: str
    delay_band: str


@dataclass
class TwinCardServiceRatings:
    """Service ratings (recent experience) section of twin card."""
    inflight_wifi_service: int
    departure_arrival_time_convenient: int
    ease_of_online_booking: int
    gate_location: int
    food_and_drink: int
    online_boarding: int
    seat_comfort: int
    inflight_entertainment: int
    on_board_service: int
    leg_room_service: int
    baggage_handling: int
    checkin_service: int
    inflight_service: int
    cleanliness: int


@dataclass
class TwinCard:
    """
    Complete twin card for an airline passenger persona.

    Represents a rich, grounded persona with demographics, travel profile,
    psychographic tags, recent experience, and cohort-based priors.
    """
    # Identity
    id: str  # Unique twin ID (e.g., "twin_001")
    label: str  # Human-readable label (e.g., "Budget-conscious young female traveler")

    # Core profile
    demographics: TwinCardDemographics
    travel_profile: TwinCardTravelProfile
    psychographics: List[str]  # List of tag names

    # Experience
    recent_experience: TwinCardServiceRatings

    # Cohort grounding
    cohort_key: str
    cohort_priors: Dict  # Full cohort prior object

    # Metadata
    metadata: Dict

    def to_dict(self) -> Dict:
        """Convert to dictionary (for JSON serialization)."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict) -> TwinCard:
        """Create TwinCard from dictionary."""
        return cls(
            id=data["id"],
            label=data["label"],
            demographics=TwinCardDemographics(**data["demographics"]),
            travel_profile=TwinCardTravelProfile(**data["travel_profile"]),
            psychographics=data["psychographics"],
            recent_experience=TwinCardServiceRatings(**data["recent_experience"]),
            cohort_key=data["cohort_key"],
            cohort_priors=data["cohort_priors"],
            metadata=data["metadata"]
        )

    @classmethod
    def from_passenger_row(
        cls,
        row: pd.Series,
        twin_id: str,
        cohort_priors_map: Dict[str, Dict]
    ) -> TwinCard:
        """
        Create TwinCard from a passenger data row.

        Args:
            row: DataFrame row with passenger data
            twin_id: Unique ID for this twin
            cohort_priors_map: Map of cohort_key -> cohort_prior

        Returns:
            TwinCard instance
        """
        # Demographics
        demographics = TwinCardDemographics(
            gender=str(row["gender"]),
            age=int(row["age"]),
            age_band=str(row["age_band"])
        )

        # Travel profile
        travel_profile = TwinCardTravelProfile(
            customer_type=str(row["customer_type"]),
            type_of_travel=str(row["type_of_travel"]),
            flight_class=str(row["flight_class"]),
            flight_distance=int(row["flight_distance"]),
            distance_band=str(row["distance_band"]),
            delay_band=str(row["delay_band"])
        )

        # Psychographics
        psycho_tags_str = row.get("psychographic_tags", "")
        psychographics = [tag.strip() for tag in psycho_tags_str.split(",") if tag.strip()]

        # Service ratings
        service_rating_cols = [
            "inflight_wifi_service",
            "departure_arrival_time_convenient",
            "ease_of_online_booking",
            "gate_location",
            "food_and_drink",
            "online_boarding",
            "seat_comfort",
            "inflight_entertainment",
            "on_board_service",
            "leg_room_service",
            "baggage_handling",
            "checkin_service",
            "inflight_service",
            "cleanliness"
        ]

        ratings_dict = {}
        for col in service_rating_cols:
            ratings_dict[col] = int(row[col]) if pd.notna(row[col]) else 3  # Default to 3 if missing

        recent_experience = TwinCardServiceRatings(**ratings_dict)

        # Cohort - rebuild key if not present
        if "cohort_key" in row.index:
            cohort_key = str(row["cohort_key"])
        else:
            # Rebuild cohort key from components
            cohort_key = f"{row['age_band']}_{row['gender']}_{row['type_of_travel']}_{row['flight_class']}_{row['distance_band']}"
            cohort_key = cohort_key.replace(" ", "_").replace("/", "_")

        cohort_priors = cohort_priors_map.get(cohort_key, {})

        # Generate label
        label = generate_label(demographics, travel_profile, psychographics)

        # Metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "data_source": "airline_satisfaction_survey",
            "row_id": int(row["row_id"]) if "row_id" in row.index else None,
            "satisfaction_label": str(row.get("satisfaction_label", "unknown"))
        }

        return cls(
            id=twin_id,
            label=label,
            demographics=demographics,
            travel_profile=travel_profile,
            psychographics=psychographics,
            recent_experience=recent_experience,
            cohort_key=cohort_key,
            cohort_priors=cohort_priors,
            metadata=metadata
        )

    def save(self, output_path: Path) -> None:
        """Save twin card to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(self.to_json())


def generate_label(
    demographics: TwinCardDemographics,
    travel_profile: TwinCardTravelProfile,
    psychographics: List[str]
) -> str:
    """
    Generate a human-readable label for the twin.

    Args:
        demographics: Demographics info
        travel_profile: Travel profile info
        psychographics: List of psychographic tags

    Returns:
        Descriptive label string
    """
    # Age descriptor
    age_desc = demographics.age_band.lower().replace("+", "plus")

    # Gender
    gender_desc = demographics.gender.lower()

    # Travel type
    if "business" in travel_profile.type_of_travel.lower():
        travel_desc = "business traveler"
    else:
        travel_desc = "leisure traveler"

    # Class
    class_desc = travel_profile.flight_class.lower().replace(" ", "-")

    # Primary psychographic
    if psychographics:
        # Use first (or most distinctive) tag
        primary_tag = psychographics[0]
        # Make it readable
        tag_desc = primary_tag.replace("_", " ")
    else:
        tag_desc = "typical"

    # Construct label
    label = f"{tag_desc.capitalize()} {age_desc} {gender_desc} {travel_desc} ({class_desc})"

    return label


def load_twin_card(file_path: Path) -> TwinCard:
    """Load twin card from JSON file."""
    with open(file_path, "r") as f:
        data = json.load(f)
    return TwinCard.from_dict(data)


def list_twin_cards(twins_dir: Path) -> List[TwinCard]:
    """Load all twin cards from directory."""
    twin_cards = []
    for file_path in sorted(twins_dir.glob("*.json")):
        twin_card = load_twin_card(file_path)
        twin_cards.append(twin_card)
    return twin_cards

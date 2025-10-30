"""
Decision ledger for audit trail and analysis.
Phase 6: Track all twin decisions with full context.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionLedger:
    """
    Ledger for tracking all twin decisions with full audit trail.

    Each decision is logged with:
    - Timestamp
    - Twin ID and label
    - Offer details
    - Context (flight, purpose, pressure)
    - Decision outcome (yes/no, probability, rationale)
    - LLM metadata (model, tokens, seed)
    - Prompt hash (for reproducibility)
    """

    def __init__(self, ledger_path: Path):
        """
        Initialize decision ledger.

        Args:
            ledger_path: Path to CSV ledger file
        """
        self.ledger_path = ledger_path
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        # CSV columns
        self.columns = [
            "timestamp",
            "twin_id",
            "twin_label",
            "offer_name",
            "offer_type",
            "discount_pct",
            "original_price",
            "final_price",
            "flight_length",
            "trip_purpose",
            "time_pressure",
            "recent_delays",
            "decision",
            "probability",
            "rationale",
            "llm_provider",
            "llm_model",
            "seed",
            "prompt_hash",
            "total_tokens",
            "attempt",
        ]

        # Initialize file if it doesn't exist
        if not self.ledger_path.exists():
            self._initialize_ledger()

    def _initialize_ledger(self):
        """Create ledger file with headers."""
        with open(self.ledger_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
        logger.info(f"Initialized decision ledger: {self.ledger_path}")

    def _hash_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Create hash of prompts for reproducibility tracking."""
        combined = f"{system_prompt}\n{user_prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def log_decision(
        self,
        twin_decision: Dict,
        system_prompt: str = "",
        user_prompt: str = ""
    ):
        """
        Log a twin decision to the ledger.

        Args:
            twin_decision: TwinDecision.to_dict() output
            system_prompt: System prompt used (for hashing)
            user_prompt: User prompt used (for hashing)
        """
        task = twin_decision["task"]
        response = twin_decision["response"]
        metadata = twin_decision["metadata"]
        llm_metadata = metadata.get("llm_metadata", {})

        # Extract offer details
        offer = task["offer"]
        original_price = offer["absolute_price_delta"] / (1 - offer["discount_pct"]) if offer["discount_pct"] < 1.0 else offer["absolute_price_delta"]

        # Extract context
        context = task["context"]

        # Compute prompt hash
        prompt_hash = self._hash_prompt(system_prompt, user_prompt) if system_prompt else "N/A"

        # Build row
        row = {
            "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
            "twin_id": twin_decision["twin_id"],
            "twin_label": twin_decision["twin_label"],
            "offer_name": offer["name"],
            "offer_type": offer["offer_kind"],
            "discount_pct": offer["discount_pct"],
            "original_price": original_price,
            "final_price": offer["absolute_price_delta"],
            "flight_length": context["flight_length"],
            "trip_purpose": context["trip_purpose"],
            "time_pressure": context["time_pressure"],
            "recent_delays": context["recent_delays"],
            "decision": response["decision"],
            "probability": response["probability"],
            "rationale": response["rationale"],
            "llm_provider": llm_metadata.get("provider", "N/A"),
            "llm_model": llm_metadata.get("model", "N/A"),
            "seed": metadata.get("seed", "N/A"),
            "prompt_hash": prompt_hash,
            "total_tokens": llm_metadata.get("usage", {}).get("total_tokens", "N/A"),
            "attempt": llm_metadata.get("attempt", 1),
        }

        # Append to CSV
        with open(self.ledger_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writerow(row)

        logger.debug(f"Logged decision: {row['twin_id']} -> {row['decision']}")

    def load_all_decisions(self) -> List[Dict]:
        """Load all decisions from ledger."""
        decisions = []

        if not self.ledger_path.exists():
            return decisions

        with open(self.ledger_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                row["discount_pct"] = float(row["discount_pct"])
                row["original_price"] = float(row["original_price"])
                row["final_price"] = float(row["final_price"])
                row["probability"] = float(row["probability"])
                decisions.append(row)

        return decisions

    def get_twin_history(self, twin_id: str) -> List[Dict]:
        """Get all decisions for a specific twin."""
        all_decisions = self.load_all_decisions()
        return [d for d in all_decisions if d["twin_id"] == twin_id]

    def get_offer_history(self, offer_name: str) -> List[Dict]:
        """Get all decisions for a specific offer."""
        all_decisions = self.load_all_decisions()
        return [d for d in all_decisions if d["offer_name"] == offer_name]

    def get_summary_stats(self) -> Dict:
        """Get summary statistics from ledger."""
        decisions = self.load_all_decisions()

        if not decisions:
            return {"total_decisions": 0}

        # Basic stats
        total = len(decisions)
        yes_count = sum(1 for d in decisions if d["decision"] == "yes")
        no_count = total - yes_count

        # By twin
        twins = {}
        for d in decisions:
            tid = d["twin_id"]
            if tid not in twins:
                twins[tid] = {"total": 0, "yes": 0, "avg_prob": []}
            twins[tid]["total"] += 1
            if d["decision"] == "yes":
                twins[tid]["yes"] += 1
            twins[tid]["avg_prob"].append(d["probability"])

        # Compute averages
        for tid in twins:
            twins[tid]["acceptance_rate"] = twins[tid]["yes"] / twins[tid]["total"]
            twins[tid]["avg_probability"] = sum(twins[tid]["avg_prob"]) / len(twins[tid]["avg_prob"])
            del twins[tid]["avg_prob"]  # Remove raw list

        # By offer
        offers = {}
        for d in decisions:
            offer = d["offer_name"]
            if offer not in offers:
                offers[offer] = {"total": 0, "yes": 0, "avg_prob": []}
            offers[offer]["total"] += 1
            if d["decision"] == "yes":
                offers[offer]["yes"] += 1
            offers[offer]["avg_prob"].append(d["probability"])

        for offer in offers:
            offers[offer]["acceptance_rate"] = offers[offer]["yes"] / offers[offer]["total"]
            offers[offer]["avg_probability"] = sum(offers[offer]["avg_prob"]) / len(offers[offer]["avg_prob"])
            del offers[offer]["avg_prob"]

        return {
            "total_decisions": total,
            "yes_decisions": yes_count,
            "no_decisions": no_count,
            "overall_acceptance_rate": yes_count / total,
            "by_twin": twins,
            "by_offer": offers,
            "unique_twins": len(twins),
            "unique_offers": len(offers)
        }

    def export_to_json(self, output_path: Path):
        """Export ledger to JSON format."""
        decisions = self.load_all_decisions()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(decisions, f, indent=2)

        logger.info(f"Exported {len(decisions)} decisions to: {output_path}")


def main():
    """Test decision ledger."""
    # Create test ledger
    ledger_path = Path("DATA/airline/decisions/test_ledger.csv")
    ledger = DecisionLedger(ledger_path)

    # Mock decision
    mock_decision = {
        "twin_id": "twin_001",
        "twin_label": "Test twin",
        "task": {
            "offer": {
                "name": "Extra Legroom",
                "offer_kind": "upgrade_addon",
                "discount_pct": 0.20,
                "absolute_price_delta": 20.0
            },
            "context": {
                "flight_length": "long",
                "trip_purpose": "business",
                "time_pressure": "medium",
                "recent_delays": "minor"
            }
        },
        "response": {
            "decision": "yes",
            "probability": 0.75,
            "rationale": "Good value for long flight"
        },
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "seed": 42,
            "llm_metadata": {
                "provider": "openai",
                "model": "gpt-4",
                "usage": {"total_tokens": 350},
                "attempt": 1
            }
        }
    }

    # Log it
    ledger.log_decision(mock_decision)
    logger.info("✅ Logged test decision")

    # Get stats
    stats = ledger.get_summary_stats()
    logger.info(f"Summary: {stats}")


if __name__ == "__main__":
    main()

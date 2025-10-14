#!/usr/bin/env python3
"""
Interactive Twin Playground - Darpan Labs What-If Simulator

This script demonstrates how to interact with digital twins to:
1. Chat with individual twins
2. Get purchase decisions from twins
3. Run what-if scenarios
4. Match users to twin profiles
"""

import requests
import json
from typing import Dict, List, Any

# API Configuration
BASE_URL = "http://localhost:8000"

def chat_with_twin(twin_id: str, prompt: str) -> str:
    """
    Chat with a specific twin personality.

    Args:
        twin_id: One of k0 (Budget-Conscious), k1 (Premium Quality), k2 (Deal-Hunting)
        prompt: Your question or conversation prompt

    Returns:
        The twin's response
    """
    response = requests.post(
        f"{BASE_URL}/twin/chat",
        json={
            "twin_id": twin_id,
            "history": [],
            "prompt": prompt
        }
    )
    return response.json()["reply"]


def get_twin_decision(twin_id: str, context: Dict[str, Any], candidates: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Ask a twin to make a purchase decision.

    Args:
        twin_id: The twin to consult
        context: Shopping context (price_mean, promo_badge, delivery_eta_days, etc.)
        candidates: List of products to choose from, e.g. [{"id": "A1"}, {"id": "A2"}]

    Returns:
        Decision with 'pick' (chosen product) and 'why' (short reason)
    """
    response = requests.post(
        f"{BASE_URL}/twin/decide",
        json={
            "twin_id": twin_id,
            "context": context,
            "candidates": candidates,
            "max_tokens": 20
        }
    )
    return response.json()["decision"]


def match_user_to_twins(user_id: str) -> tuple:
    """
    Match a user to their twin mixture.

    Args:
        user_id: User identifier (e.g., "u1", "u2")

    Returns:
        Tuple of (twin_weights dict, primary_twin dict)
    """
    response = requests.post(
        f"{BASE_URL}/match",
        json={"z_or_user_id": user_id}
    )
    data = response.json()
    return data["twin_weights"], data["primary_twin"]


def run_what_if_simulation(cta_seq: List[Dict], scenarios: List[Dict], explain: str = "blend") -> Dict:
    """
    Run what-if scenarios to see how twins respond to changes.

    Args:
        cta_seq: User's click-through-action history
        scenarios: List of scenario patches (base, price_drop, promo, etc.)
        explain: "none", "blend", or "per_twin"

    Returns:
        Simulation results with per-scenario predictions and deltas
    """
    response = requests.post(
        f"{BASE_URL}/simulate",
        json={
            "cta_seq": cta_seq,
            "task": "choose_product",
            "scenarios": scenarios,
            "topk": 5,
            "explain": explain,
            "deterministic": True,
            "seed": 17
        }
    )
    return response.json()


def get_all_personas() -> List[Dict]:
    """Get list of all available twin personas."""
    response = requests.get(f"{BASE_URL}/twin/personas")
    return response.json()["personas"]


# ========== EXAMPLE USE CASES ==========

def example_1_chat_with_all_twins():
    """Example 1: Chat with each twin to understand their personality."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Chat with All Twins")
    print("="*60 + "\n")

    prompt = "What do you look for when shopping?"
    twins = ["k0", "k1", "k2"]
    labels = {
        "k0": "Budget-Conscious Searcher",
        "k1": "Premium Quality Seeker",
        "k2": "Deal-Hunting Explorer"
    }

    for twin_id in twins:
        reply = chat_with_twin(twin_id, prompt)
        print(f"🧑 {labels[twin_id]} ({twin_id}):")
        print(f"   \"{reply}\"\n")


def example_2_compare_twin_decisions():
    """Example 2: See how different twins choose among products."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Compare Twin Product Decisions")
    print("="*60 + "\n")

    context = {
        "price_mean": 500,
        "promo_badge": False,
        "delivery_eta_days": 3
    }

    candidates = [
        {"id": "Premium_A"},
        {"id": "Budget_B"},
        {"id": "Feature_C"}
    ]

    print("Context:", json.dumps(context, indent=2))
    print("\nCandidates:", [c["id"] for c in candidates])
    print("\nTwin Decisions:\n")

    for twin_id in ["k0", "k1", "k2"]:
        decision = get_twin_decision(twin_id, context, candidates)
        print(f"  {twin_id}: Chose '{decision['pick']}' — {decision['why']}")


def example_3_what_if_price_drop():
    """Example 3: What if we drop prices? Run a price sensitivity test."""
    print("\n" + "="*60)
    print("EXAMPLE 3: What-If Price Drop Simulation")
    print("="*60 + "\n")

    cta_seq = [{
        "user_id": "u1",
        "session_id": "s1",
        "ts": "2025-06-01T12:00:00",
        "context": {
            "page_type": "search",
            "price_mean": 820,
            "visible_products": ["Product_A", "Product_B", "Product_C"]
        },
        "task": "choose_product",
        "action_id": "Product_B"
    }]

    scenarios = [
        {"variant_id": "base", "context_overrides": {}},
        {"variant_id": "10%_off", "context_overrides": {"price_mean": 738}},
        {"variant_id": "20%_off", "context_overrides": {"price_mean": 656}},
    ]

    result = run_what_if_simulation(cta_seq, scenarios, explain="blend")

    print("Primary Twin:", result["primary_twin"]["label"])
    print("\nScenario Results:\n")

    for scenario in result["by_scenario"]:
        print(f"  📊 {scenario['variant_id']}:")
        print(f"     Top Pick: {scenario['topN'][0]['id']} (prob: {scenario['topN'][0]['p']:.3f})")
        if scenario['why']:
            print(f"     Reason: \"{scenario['why']}\"")
        print()


def example_4_user_matching():
    """Example 4: Match a user to their primary twin."""
    print("\n" + "="*60)
    print("EXAMPLE 4: User-to-Twin Matching")
    print("="*60 + "\n")

    for user_id in ["u1", "u2"]:
        weights, primary = match_user_to_twins(user_id)
        print(f"User: {user_id}")
        print(f"  Primary Twin: {primary['label']} ({primary['id']})")
        print(f"  Twin Weights: {json.dumps(weights, indent=4)}\n")


def example_5_promo_impact():
    """Example 5: What's the impact of adding a promo badge?"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Promo Badge Impact Analysis")
    print("="*60 + "\n")

    cta_seq = [{
        "user_id": "u1",
        "session_id": "s1",
        "ts": "2025-06-01T12:00:00",
        "context": {
            "page_type": "product_page",
            "price_mean": 599,
            "visible_products": ["Laptop_Pro", "Laptop_Budget"]
        },
        "task": "choose_product",
        "action_id": "Laptop_Pro"
    }]

    scenarios = [
        {"variant_id": "no_promo", "context_overrides": {"promo_badge": False}},
        {"variant_id": "with_promo", "context_overrides": {"promo_badge": True}},
    ]

    result = run_what_if_simulation(cta_seq, scenarios, explain="per_twin")

    print("Scenario Comparison:\n")

    for scenario in result["by_scenario"]:
        print(f"  {scenario['variant_id']}:")
        print(f"    Blended Top Pick: {scenario['topN'][0]['id']}")

        if scenario.get("by_twin"):
            print(f"    Per-Twin Decisions:")
            for twin_pick in scenario["by_twin"]:
                pick_id = twin_pick["picks"][0]["id"]
                print(f"      - {twin_pick['twin_id']}: {pick_id} — {twin_pick.get('why', 'N/A')}")
        print()


def main():
    """Run all examples."""
    print("\n" + "🎯" * 30)
    print("   DARPAN LABS - TWIN INTERACTION PLAYGROUND")
    print("🎯" * 30)

    # List available twins
    personas = get_all_personas()
    print(f"\n📋 Available Twins: {len(personas)}")
    for p in personas:
        print(f"   • {p['id']}: {p['label']}")

    # Run examples
    example_1_chat_with_all_twins()
    example_2_compare_twin_decisions()
    example_3_what_if_price_drop()
    example_4_user_matching()
    example_5_promo_impact()

    print("\n" + "✅" * 30)
    print("   All examples completed!")
    print("✅" * 30 + "\n")


if __name__ == "__main__":
    # Make sure API is running first
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.json()["status"] != "ok":
            raise Exception("API not healthy")
    except:
        print("❌ Error: API server not running!")
        print("   Please start the server with: make serve")
        print("   Or: uvicorn src.api.service:app --host 0.0.0.0 --port 8000")
        exit(1)

    main()

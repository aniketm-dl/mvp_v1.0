#!/usr/bin/env python3
"""
Example script demonstrating the decide_then_verbalize workflow.

This script shows the complete pipeline:
1. Build twin embedding from behavioral/psychographic/demographic features
2. Compute mixture weights (optional)
3. Use policy heads to get decision probabilities
4. Verbalize the decision with guardrails
5. Print clean JSON payload + natural language output

Usage:
    python examples/run_decide_then_verbalize.py
"""

from __future__ import annotations
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.encoder import build_twin_embedding
from src.models.mixture import TwinMixture, load_twin_bank
from src.models.policy_heads import TwinPolicyHeadSet
from src.reasoning.orchestrator import decide_then_verbalize, DecisionOrchestrator


def main():
    print("=" * 80)
    print("DECIDE THEN VERBALIZE - EXAMPLE")
    print("=" * 80)
    print()

    # ==================================================================
    # Step 1: Build twin embedding from features
    # ==================================================================
    print("Step 1: Building twin embedding...")
    print("-" * 80)

    # Mock behavioral features (8-D)
    # [price_sensitivity, promo_response, delivery_sensitivity, brand_loyalty,
    #  impulse_score, research_depth, frequency, recency]
    behavior_8d = np.array([
        0.8,  # High price sensitivity
        0.6,  # Moderate promo response
        0.4,  # Low delivery sensitivity
        0.5,  # Moderate brand loyalty
        0.3,  # Low impulse
        0.7,  # High research depth
        0.6,  # Moderate frequency
        0.9,  # Recent
    ], dtype=np.float32)

    # Mock psychographic features (4-D)
    # [thrift, novelty, quality_focus, speed_focus]
    psycho_4d = np.array([
        0.9,  # High thrift
        0.3,  # Low novelty seeking
        0.7,  # High quality focus
        0.4,  # Low speed focus
    ], dtype=np.float32)

    # Mock demographic features (3-D)
    # [age_25_34, urban, female]
    demo_3d = np.array([
        0.8,  # Likely 25-34
        0.7,  # Urban
        0.5,  # Neutral
    ], dtype=np.float32)

    # Build twin embedding (15-D)
    # use_learned_fusion=False for simple concatenation (legacy mode)
    # use_learned_fusion=True for learned MLP fusion (requires trained weights)
    twin_vec = build_twin_embedding(
        behavior_8d,
        psycho_4d,
        demo_3d,
        use_learned_fusion=False  # Change to True if you have trained fusion MLP
    )

    print(f"Twin embedding shape: {twin_vec.shape}")
    print(f"Twin embedding (first 5): {twin_vec[:5]}")
    print()

    # ==================================================================
    # Step 2: Compute mixture weights (optional - for debugging)
    # ==================================================================
    print("Step 2: Computing mixture weights...")
    print("-" * 80)

    try:
        twin_bank = load_twin_bank()
        print(f"Loaded twin bank with {len(twin_bank)} twins")

        mixture = TwinMixture(twin_bank, tau=0.8)
        weights = mixture.weights(twin_vec)
        primary_twin = mixture.primary(twin_vec)

        print(f"Primary twin: {primary_twin}")
        print("Top 3 mixture weights:")
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        for twin_id, weight in sorted_weights[:3]:
            print(f"  {twin_id}: {weight:.3f}")
        print()
    except Exception as e:
        print(f"Mixture computation skipped (twin bank not available): {e}")
        print()

    # ==================================================================
    # Step 3: Setup policy heads
    # ==================================================================
    print("Step 3: Setting up policy heads...")
    print("-" * 80)

    policy = TwinPolicyHeadSet()
    loaded = policy.load()

    if loaded:
        print(f"Loaded policy heads for {len(policy.available_twins())} twins")
    else:
        print("No pre-trained policy heads found - using mock policy")
    print()

    # ==================================================================
    # Step 4: Define offer features
    # ==================================================================
    print("Step 4: Defining offer features...")
    print("-" * 80)

    # Mock offer/product features
    # [price, quality_score, brand_score, delivery_days, promo_discount, ...]
    offer_feats = np.array([
        75.0,  # Price: $75
        0.8,   # Quality: 0.8/1.0
        0.7,   # Brand: 0.7/1.0
        3.0,   # Delivery: 3 days
        0.15,  # Promo: 15% off
        450,   # Reviews count
        4.2,   # Rating: 4.2/5.0
        0.6,   # Popularity: 0.6/1.0
    ], dtype=np.float32)

    print(f"Offer features: price=${offer_feats[0]}, quality={offer_feats[1]:.2f}, delivery={offer_feats[3]:.0f} days")
    print()

    # ==================================================================
    # Step 5: Run decide_then_verbalize
    # ==================================================================
    print("Step 5: Running decide_then_verbalize...")
    print("-" * 80)

    # Method A: Direct function call
    payload, text = decide_then_verbalize(
        twin_vec=twin_vec,
        offer_feats=offer_feats,
        policy=policy,
        guardrails={
            "enabled": True,
            "context_keywords": ["price", "quality", "delivery", "brand"],
            "max_retries": 1,
        }
    )

    print("Decision Payload (JSON):")
    print("-" * 40)
    print(f"  Decision: {payload['decision']}")
    print(f"  Confidence: {payload['confidence']:.2f}")
    print(f"  Probabilities:")
    for decision, prob in payload['probs'].items():
        print(f"    {decision}: {prob:.3f}")
    print(f"  Top Factors: {', '.join(payload['top_factors'])}")
    print()

    print("Natural Language Output:")
    print("-" * 40)
    print(f"  \"{text}\"")
    print()

    # ==================================================================
    # Step 6: Using DecisionOrchestrator (stateful API)
    # ==================================================================
    print("Step 6: Using DecisionOrchestrator (stateful API)...")
    print("-" * 80)

    orchestrator = DecisionOrchestrator(
        policy=policy,
        guardrails_config={
            "enabled": True,
            "context_keywords": ["price", "quality", "delivery"],
        }
    )

    # Make a decision
    payload2, text2 = orchestrator.decide(twin_vec, offer_feats)

    print("Orchestrator Output:")
    print(f"  Decision: {payload2['decision']}")
    print(f"  Text: \"{text2}\"")
    print()

    # ==================================================================
    # Step 7: Batch processing example
    # ==================================================================
    print("Step 7: Batch processing multiple queries...")
    print("-" * 80)

    # Create 3 different twin vectors (e.g., budget, premium, deal-seeker)
    twin_vecs = [
        build_twin_embedding(
            np.array([0.9, 0.8, 0.3, 0.4, 0.2, 0.6, 0.5, 0.9], dtype=np.float32),  # Budget-conscious
            np.array([0.9, 0.2, 0.6, 0.3], dtype=np.float32),
            np.array([0.5, 0.6, 0.5], dtype=np.float32),
        ),
        build_twin_embedding(
            np.array([0.2, 0.3, 0.8, 0.7, 0.6, 0.8, 0.7, 0.9], dtype=np.float32),  # Premium
            np.array([0.2, 0.7, 0.9, 0.6], dtype=np.float32),
            np.array([0.8, 0.8, 0.5], dtype=np.float32),
        ),
        build_twin_embedding(
            np.array([0.7, 0.9, 0.5, 0.5, 0.7, 0.5, 0.8, 0.9], dtype=np.float32),  # Deal-seeker
            np.array([0.8, 0.5, 0.5, 0.5], dtype=np.float32),
            np.array([0.6, 0.5, 0.5], dtype=np.float32),
        ),
    ]

    # Same offer for all
    offer_feats_list = [offer_feats, offer_feats, offer_feats]

    # Batch decide
    results = orchestrator.batch_decide(twin_vecs, offer_feats_list)

    persona_labels = ["Budget-Conscious", "Premium", "Deal-Seeker"]
    for i, ((payload, text), label) in enumerate(zip(results, persona_labels)):
        print(f"Persona {i+1} ({label}):")
        print(f"  Decision: {payload['decision']} (confidence: {payload['confidence']:.2f})")
        print(f"  Response: \"{text}\"")
        print()

    # ==================================================================
    # Summary
    # ==================================================================
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✅ Successfully demonstrated decide_then_verbalize workflow:")
    print("  1. Built twin embeddings from behavioral/psychographic/demographic features")
    print("  2. Computed mixture weights over twin bank")
    print("  3. Used policy heads to predict decision probabilities")
    print("  4. Generated natural language with guardrails")
    print("  5. Produced clean JSON payloads + natural text (no brackets/tags)")
    print()
    print("Key features:")
    print("  - Policy-first routing (fast decisions without LLM)")
    print("  - Temperature-calibrated probabilities")
    print("  - Top-K factor extraction for explainability")
    print("  - Guardrails for natural, tag-free output")
    print("  - Batch processing support")
    print()
    print("Done!")


if __name__ == "__main__":
    main()

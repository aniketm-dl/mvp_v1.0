#!/usr/bin/env python3
"""
Generate comprehensive training data for all 18 MVP personas.
Creates diverse, persona-specific conversational examples for SFT.
"""

from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import json
import random

# Seed for reproducibility
random.seed(42)

# Conversation templates for different scenarios
PRICE_QUESTIONS = [
    "What do you think about this price?",
    "Is this product worth the cost?",
    "Would you buy this at this price point?",
    "How important is price to you?",
    "What's your budget for this purchase?"
]

QUALITY_QUESTIONS = [
    "What matters most to you when shopping?",
    "How do you evaluate product quality?",
    "Would you pay more for better quality?",
    "What makes a product worth buying?",
    "How do you judge if something is high quality?"
]

BRAND_QUESTIONS = [
    "Do you prefer certain brands?",
    "How important is brand reputation?",
    "Would you try a new brand?",
    "What do you think about brand loyalty?",
    "How do brand names influence your decisions?"
]

DELIVERY_QUESTIONS = [
    "How important is fast shipping?",
    "What delivery time is acceptable?",
    "Would you pay for faster delivery?",
    "How do you feel about delivery options?",
    "What's your preferred shipping method?"
]

DECISION_QUESTIONS = [
    "How do you make purchase decisions?",
    "What influences your buying choices?",
    "How long do you research before buying?",
    "What factors matter most to you?",
    "How do you choose between similar products?"
]

REVIEW_QUESTIONS = [
    "Do you read product reviews?",
    "How important are customer ratings?",
    "What do you look for in reviews?",
    "Would you buy something with few reviews?",
    "How do reviews influence your decisions?"
]

def generate_responses_for_persona(persona: Dict[str, Any]) -> Dict[str, List[str]]:
    """Generate persona-specific response templates."""

    pid = persona["id"]
    tags = persona.get("psychographic_tags", [])
    values = persona.get("shopping_values", [])
    constraints = persona.get("decision_constraints", "")
    behavior = persona.get("typical_behavior", "")

    responses = {
        "price": [],
        "quality": [],
        "brand": [],
        "delivery": [],
        "decision": [],
        "review": []
    }

    # Price-sensitive personas
    if "price_sensitive" in tags or "deal_seeker" in tags or "budget_conscious" in tags:
        responses["price"].extend([
            "Price is my top priority. I always look for the best deal.",
            "I won't buy unless the price is right. I'm patient and wait for sales.",
            "I compare prices across sites to find the lowest cost.",
            "A good price matters more than anything else to me.",
            "I use price trackers and wait for discounts before buying."
        ])
        responses["decision"].extend([
            "I decide based on price first, then features.",
            "If it's not the cheapest option, I keep looking.",
            "I calculate value per dollar before every purchase."
        ])

    # Quality-focused personas
    if "quality_focused" in tags or "premium_buyer" in tags or "selective" in tags:
        responses["quality"].extend([
            "Quality is non-negotiable for me. I'm willing to pay more.",
            "I invest in products that last and perform well.",
            "I research quality indicators and materials carefully.",
            "Cheap products often cost more in the long run.",
            "I'd rather buy less but buy better quality."
        ])
        responses["brand"].extend([
            "I trust established brands with proven quality.",
            "Brand reputation tells me a lot about reliability.",
            "I stick with brands that have never disappointed me."
        ])

    # Impulse/spontaneous buyers
    if "spontaneous" in tags or "fomo_prone" in tags or "visually_driven" in tags:
        responses["decision"].extend([
            "I buy what catches my eye in the moment.",
            "If I like it, I add it to cart right away.",
            "I don't overthink purchases - life's too short!",
            "Attractive products and good images sell me instantly.",
            "Limited time offers make me act fast."
        ])
        responses["price"].extend([
            "Price doesn't matter if I really want it.",
            "I see something I like, I buy it - simple as that."
        ])

    # Analytical/research-oriented personas
    if "analytical" in tags or "review_focused" in tags or "detail_oriented" in tags:
        responses["review"].extend([
            "I read every review before making a decision.",
            "I create comparison spreadsheets for major purchases.",
            "I need comprehensive information to feel confident.",
            "I look for detailed specs and verified reviews.",
            "I research for days or weeks before committing."
        ])
        responses["decision"].extend([
            "I methodically compare all options before deciding.",
            "Data and reviews guide my choices, not emotions.",
            "I won't buy until I've done thorough research."
        ])

    # Convenience-focused personas
    if "efficiency_focused" in tags or "time_conscious" in tags or "convenience_focused" in tags:
        responses["delivery"].extend([
            "Fast delivery is essential - I value my time.",
            "I filter by fastest shipping available.",
            "Same-day or next-day delivery is worth paying for.",
            "Convenience trumps small price differences."
        ])
        responses["decision"].extend([
            "I choose the most convenient option available.",
            "Easy checkout and fast delivery win me over.",
            "I don't want to waste time - show me quick solutions."
        ])

    # Values-driven personas
    if "values_driven" in tags or "eco_friendly" in tags or "ethical_consumer" in tags:
        responses["quality"].extend([
            "I look for sustainable and ethical products.",
            "Environmental impact matters more than price.",
            "I research company values and practices.",
            "I'm willing to pay premium for ethical production."
        ])
        responses["brand"].extend([
            "I support brands that align with my values.",
            "Company ethics and sustainability are deal-makers.",
            "I choose brands that give back to communities."
        ])

    # Social validators
    if "socially_influenced" in tags or "validation_seeker" in tags or "review_dependent" in tags:
        responses["review"].extend([
            "I only buy products with high ratings and lots of reviews.",
            "Social proof is everything - I trust the crowd.",
            "I check what influencers and friends recommend.",
            "If it's popular and well-reviewed, it's probably good.",
            "Low ratings are an instant deal-breaker for me."
        ])
        responses["decision"].extend([
            "I follow what others recommend and trust.",
            "Popularity and ratings guide my choices.",
            "I look for social validation before buying."
        ])

    # Brand-loyal personas
    if "brand_loyal" in tags:
        responses["brand"].extend([
            "I stick with brands I trust - why risk it?",
            "Once a brand earns my loyalty, I'm a customer for life.",
            "I rarely switch brands unless something goes wrong.",
            "Familiar brands give me peace of mind."
        ])

    # Brand-agnostic personas
    if "brand_agnostic" in tags or "opportunistic" in tags:
        responses["brand"].extend([
            "I have zero brand loyalty - I go where value is.",
            "Brands don't matter - I judge each product individually.",
            "I'll switch brands for any better deal or feature.",
            "Why stick to one brand when there are better options?"
        ])

    # Innovation seekers
    if "innovation_seeker" in tags or "early_adopter" in tags or "trend_conscious" in tags:
        responses["decision"].extend([
            "I want the latest and most innovative products.",
            "I'm always first to try new releases and trends.",
            "Cutting-edge features excite me more than anything.",
            "I pre-order new products before they're even out."
        ])
        responses["quality"].extend([
            "Innovation and novelty are my top priorities.",
            "I love being ahead of trends and trying new things."
        ])

    # Gift buyers
    if "gift_oriented" in tags or "thoughtful" in tags or "experience_focused" in tags:
        responses["decision"].extend([
            "I think about how the recipient will feel.",
            "Presentation and uniqueness matter for gifts.",
            "I look for items that create memorable experiences.",
            "Emotional significance outweighs price for me."
        ])
        responses["quality"].extend([
            "For gifts, quality and thoughtfulness are everything.",
            "I choose items that show I care and understand the person."
        ])

    # Fill in any empty categories with generic responses based on persona
    if not responses["price"]:
        responses["price"].append(f"I consider price along with other factors.")
    if not responses["quality"]:
        responses["quality"].append(f"Quality matters to me like it does to most shoppers.")
    if not responses["brand"]:
        responses["brand"].append(f"Brands are one factor I consider.")
    if not responses["delivery"]:
        responses["delivery"].append(f"I appreciate reasonable delivery times.")
    if not responses["decision"]:
        responses["decision"].append(f"I weigh multiple factors when deciding.")
    if not responses["review"]:
        responses["review"].append(f"I glance at reviews when available.")

    return responses

def generate_training_examples(persona: Dict[str, Any], n_examples: int = 150) -> List[Dict[str, Any]]:
    """Generate diverse training examples for a persona."""

    examples = []
    responses = generate_responses_for_persona(persona)

    # Question pools
    all_questions = {
        "price": PRICE_QUESTIONS,
        "quality": QUALITY_QUESTIONS,
        "brand": BRAND_QUESTIONS,
        "delivery": DELIVERY_QUESTIONS,
        "decision": DECISION_QUESTIONS,
        "review": REVIEW_QUESTIONS
    }

    # Generate examples across all categories
    categories = list(all_questions.keys())

    for i in range(n_examples):
        # Cycle through categories to ensure diversity
        category = categories[i % len(categories)]

        # Pick random question and response from category
        question = random.choice(all_questions[category])
        response = random.choice(responses[category])

        # Create training example
        example = {
            "twin_id": persona["id"],
            "input": f"User: {question}\nAssistant:",
            "output": response,
            "meta": {
                "psychographic_tags": persona.get("psychographic_tags", []),
                "category": category,
                "shopping_values": persona.get("shopping_values", [])
            }
        }

        examples.append(example)

    return examples

def main():
    """Generate training data for all personas."""

    print("🎯 Generating MVP Training Data for All 18 Personas...\n")

    # Load personas
    personas_file = Path("DATA/personas.json")
    if not personas_file.exists():
        print(f"❌ Error: {personas_file} not found!")
        print("   Run: python scripts/generate_mvp_personas.py first")
        return

    personas_data = json.loads(personas_file.read_text())
    personas = personas_data["personas"]

    print(f"📚 Loaded {len(personas)} personas\n")

    # Create output directory
    outdir = Path("DATA/sft")
    outdir.mkdir(parents=True, exist_ok=True)

    # Generate training data for each persona
    total_examples = 0

    for persona in personas:
        pid = persona["id"]
        label = persona["label"]

        # Generate 150 examples per persona (up from 50)
        examples = generate_training_examples(persona, n_examples=150)

        # Save to JSONL file
        output_file = outdir / f"{pid}.jsonl"
        output_file.write_text(
            "\n".join(json.dumps(ex) for ex in examples),
            encoding="utf-8"
        )

        total_examples += len(examples)
        print(f"✅ {label:40s} → {len(examples):3d} examples → {output_file}")

    print(f"\n🎉 Generated {total_examples:,} total training examples!")
    print(f"   📁 Saved to: {outdir.absolute()}")
    print(f"\n📊 Stats:")
    print(f"   • Personas: {len(personas)}")
    print(f"   • Examples per persona: ~150")
    print(f"   • Total examples: {total_examples:,}")
    print(f"\n⏭️  Next step: Train adapters with `python scripts/train_all_adapters.py`")

if __name__ == "__main__":
    main()

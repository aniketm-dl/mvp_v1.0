#!/usr/bin/env python3
"""
Prepare Multi-Turn SFT Training Data for Existing Personas

This script creates multi-turn conversation training data for the 18 existing personas
defined in DATA/personas.json. It generates realistic shopping conversations based on
each persona's characteristics and shopping style.

Usage:
    python scripts/prepare_persona_sft_data.py
    python scripts/prepare_persona_sft_data.py --max_examples_per_persona 1000
    python scripts/prepare_persona_sft_data.py --output_dir DATA/sft
"""

from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

# Shopping conversation scenarios
SHOPPING_SCENARIOS = [
    {
        "context": "product_recommendation",
        "user_questions": [
            "I'm looking for {product_type}. What would you recommend?",
            "What's the best {product_type} for my needs?",
            "Can you help me find a good {product_type}?",
            "I need advice on choosing a {product_type}."
        ],
        "follow_ups": [
            "What about the warranty?",
            "How does the return policy work?",
            "Are there any accessories I should consider?",
            "What's the delivery time?",
            "Is there a better deal elsewhere?"
        ]
    },
    {
        "context": "product_evaluation",
        "user_questions": [
            "What do you think about this {product_name}?",
            "Is this {product_name} worth the price?",
            "Should I buy this {product_name}?",
            "How does this {product_name} compare to others?"
        ],
        "follow_ups": [
            "What are the main pros and cons?",
            "Are there any known issues?",
            "How long will it last?",
            "Is it worth the extra cost?"
        ]
    },
    {
        "context": "timing_advice",
        "user_questions": [
            "Should I buy this now or wait?",
            "Is this a good time to buy {product_type}?",
            "Do you think the price will go down?",
            "Should I wait for a sale?"
        ],
        "follow_ups": [
            "When do you think it will be cheaper?",
            "Are there any upcoming sales?",
            "What's the typical price range?",
            "Is it worth waiting?"
        ]
    },
    {
        "context": "product_comparison",
        "user_questions": [
            "I'm comparing {product1} and {product2}. Which is better?",
            "Should I get {product1} or {product2}?",
            "What's the difference between {product1} and {product2}?",
            "Which would you choose: {product1} or {product2}?"
        ],
        "follow_ups": [
            "What are the key differences?",
            "Which offers better value?",
            "Which has better reviews?",
            "Which would last longer?"
        ]
    },
    {
        "context": "deal_seeking",
        "user_questions": [
            "What's the best deal on {product_type} right now?",
            "Where can I find the cheapest {product_type}?",
            "Are there any discounts on {product_type}?",
            "What's the lowest price you've seen for {product_type}?"
        ],
        "follow_ups": [
            "Are there any coupon codes?",
            "What about refurbished options?",
            "Should I check other stores?",
            "Is there a price match guarantee?"
        ]
    }
]

# Product types and names
PRODUCT_TYPES = [
    "headphones", "laptop", "smartphone", "tablet", "smartwatch", "camera",
    "speaker", "keyboard", "mouse", "monitor", "desk", "chair", "lamp",
    "book", "clothing", "shoes", "bag", "jewelry", "home decor", "kitchen appliance",
    "fitness equipment", "gaming console", "coffee maker", "vacuum cleaner", "air purifier"
]

PRODUCT_NAMES = [
    "Premium Wireless Headphones", "Gaming Laptop Pro", "Latest Smartphone",
    "Professional Tablet", "Fitness Smartwatch", "DSLR Camera", "Bluetooth Speaker",
    "Mechanical Keyboard", "Wireless Mouse", "4K Monitor", "Standing Desk",
    "Ergonomic Chair", "LED Desk Lamp", "Bestselling Novel", "Designer Jacket",
    "Running Shoes", "Leather Handbag", "Gold Necklace", "Modern Art Print",
    "Coffee Maker", "Gaming Console", "Fitness Tracker", "Smart Home Hub"
]

def load_personas(personas_file: Path) -> List[Dict[str, Any]]:
    """Load personas from JSON file."""
    with open(personas_file, 'r') as f:
        data = json.load(f)
    return data['personas']

def create_persona_response(persona: Dict[str, Any], context: str, user_question: str) -> str:
    """Create a persona-specific response based on their characteristics."""
    persona_id = persona['id']
    system_prompt = persona.get('system_prompt', '')
    decision_constraints = persona.get('decision_constraints', '')
    ocean_scores = persona.get('ocean_scores', {})
    tags = persona.get('psychographic_tags', [])
    
    # Base response based on persona type
    if 'bargain_hunter' in persona_id:
        return _create_bargain_hunter_response(context, user_question)
    elif 'premium_loyalist' in persona_id:
        return _create_premium_loyalist_response(context, user_question)
    elif 'impulse_buyer' in persona_id:
        return _create_impulse_buyer_response(context, user_question)
    elif 'research_oriented' in persona_id:
        return _create_research_oriented_response(context, user_question)
    elif 'convenience_seeker' in persona_id:
        return _create_convenience_seeker_response(context, user_question)
    elif 'eco_conscious' in persona_id:
        return _create_eco_conscious_response(context, user_question)
    elif 'minimalist' in persona_id:
        return _create_minimalist_response(context, user_question)
    elif 'social_validator' in persona_id:
        return _create_social_validator_response(context, user_question)
    else:
        return _create_generic_response(persona, context, user_question)

def _create_bargain_hunter_response(context: str, user_question: str) -> str:
    """Create response for bargain hunter persona."""
    responses = {
        "product_recommendation": [
            "I'd recommend checking multiple sites for the best price. Look for refurbished or open-box deals - you can save 20-30%!",
            "Before buying, I always check price comparison sites and wait for sales. The best deals usually come during Black Friday or end-of-season clearances.",
            "I'd suggest waiting for a discount. Most items go on sale within 2-3 months. Set up price alerts to catch the best deals!"
        ],
        "product_evaluation": [
            "The price seems high. I'd wait for a sale or look for a refurbished version. You can often find the same quality for 40% less.",
            "Check if there are any coupon codes or cashback offers. I never pay full price - there's always a way to save money.",
            "This looks overpriced. I'd recommend comparing prices across at least 5 different stores before buying."
        ],
        "timing_advice": [
            "Definitely wait! Prices usually drop significantly during sales. I'd recommend waiting 2-4 weeks for a better deal.",
            "This is not a good time to buy. Wait for the next major sale - you'll save at least 25% off the current price.",
            "I'd suggest waiting. I've seen this item go for 30% less during previous sales. Patience pays off!"
        ],
        "product_comparison": [
            "Go with the cheaper option unless there's a significant quality difference. The extra features aren't worth the premium price.",
            "I'd choose the one with the better warranty and return policy. Price isn't everything, but value is.",
            "Compare the total cost including shipping and taxes. Sometimes the 'cheaper' option ends up costing more."
        ],
        "deal_seeking": [
            "I found this same item for 40% less on a different site. Always check multiple retailers and look for coupon codes.",
            "The best deals are usually on refurbished items or during clearance sales. Don't be afraid of open-box products!",
            "I'd recommend waiting for a flash sale or using a cashback credit card. You can save an additional 5-10% that way."
        ]
    }
    return random.choice(responses.get(context, ["I'd recommend comparing prices first."]))

def _create_premium_loyalist_response(context: str, user_question: str) -> str:
    """Create response for premium loyalist persona."""
    responses = {
        "product_recommendation": [
            "I'd recommend the premium version. The quality and durability make it worth the extra cost. You'll have it for years.",
            "Go with the top-tier model. The superior materials and craftsmanship justify the price. You get what you pay for.",
            "I always choose the best quality available. It's an investment that pays off in the long run with better performance and longevity."
        ],
        "product_evaluation": [
            "This is a solid choice from a reputable brand. The premium price reflects the superior quality and customer service.",
            "I'd recommend this. The brand has excellent reputation and the product comes with comprehensive warranty and support.",
            "This is worth the investment. Premium brands typically offer better customer service and longer product lifespan."
        ],
        "timing_advice": [
            "If you need it now, buy it. Quality products rarely go on significant sale, and the premium is worth it for the reliability.",
            "Don't wait for sales on premium items. The price is usually stable, and you'll benefit from using it sooner.",
            "Premium products maintain their value. Buy when you need it - the quality and service are worth the price."
        ],
        "product_comparison": [
            "Choose the premium option. The superior quality, warranty, and customer service make it the better long-term investment.",
            "I'd go with the higher-end model. The additional features and build quality justify the price difference.",
            "Premium brands offer better value over time. The initial cost is higher, but the quality and support are unmatched."
        ],
        "deal_seeking": [
            "Premium products rarely have significant discounts. The price reflects the quality and service you're getting.",
            "I'd recommend buying from authorized dealers. You get the full warranty and customer support, which is worth the premium.",
            "Don't compromise on quality for price. Premium brands offer better long-term value and customer satisfaction."
        ]
    }
    return random.choice(responses.get(context, ["I'd recommend the premium option."]))

def _create_impulse_buyer_response(context: str, user_question: str) -> str:
    """Create response for impulse buyer persona."""
    responses = {
        "product_recommendation": [
            "This looks amazing! I'd say go for it - you only live once! The excitement of getting something new is worth it.",
            "I love this! It's perfect for you. Sometimes you just have to treat yourself. You deserve it!",
            "This is exactly what you need! Don't overthink it - if you like it, get it. Life's too short to wait!"
        ],
        "product_evaluation": [
            "I love it! It's so cool and you'll definitely use it. Sometimes you just have to go with your gut feeling.",
            "This is perfect! I can see you using this all the time. Don't second-guess yourself - if it makes you happy, get it!",
            "I'm excited about this! It's exactly what you've been looking for. Trust your instincts and go for it!"
        ],
        "timing_advice": [
            "Buy it now! You never know when it might sell out. The excitement of getting it today is worth it!",
            "Don't wait! If you like it now, you'll love it even more when you have it. Strike while the iron is hot!",
            "Get it while you can! These things tend to sell out quickly, and you don't want to miss out on something you really want."
        ],
        "product_comparison": [
            "I'd go with the one that excites you more! Choose the one that makes you feel good when you think about it.",
            "Pick the one that gives you that 'yes!' feeling. Sometimes the heart knows what it wants better than the head.",
            "Go with your gut! The one that makes you smile when you imagine using it is the right choice."
        ],
        "deal_seeking": [
            "If you love it, the price is worth it! Don't let a few dollars stand between you and something that makes you happy.",
            "The best deal is getting something you really want! If it brings you joy, it's worth every penny.",
            "Don't overthink the price - if it makes you excited, that's the best deal you can get!"
        ]
    }
    return random.choice(responses.get(context, ["Go for it! You'll love it!"]))

def _create_research_oriented_response(context: str, user_question: str) -> str:
    """Create response for research-oriented persona."""
    responses = {
        "product_recommendation": [
            "I'd recommend doing thorough research first. Check multiple review sites, compare specifications, and read user feedback before deciding.",
            "Before recommending anything, I'd suggest comparing at least 5 different options. Look at detailed reviews and technical specifications.",
            "I'd advise checking Consumer Reports, reading professional reviews, and comparing features across multiple brands before making a decision."
        ],
        "product_evaluation": [
            "Let me analyze this systematically. I'd check the technical specifications, read multiple reviews, and compare it with similar products.",
            "I'd recommend researching the manufacturer's reputation, checking warranty terms, and reading detailed user reviews before deciding.",
            "Before making a decision, I'd suggest looking at the product's track record, checking for any known issues, and comparing it with alternatives."
        ],
        "timing_advice": [
            "I'd recommend researching the typical price patterns first. Check price history charts and wait for the optimal time to buy.",
            "Before buying, I'd suggest checking when similar products typically go on sale and monitoring price trends over the past year.",
            "I'd advise researching the product's release cycle and typical discount patterns to determine the best time to purchase."
        ],
        "product_comparison": [
            "I'd create a detailed comparison chart with specifications, reviews, and price points. Let me analyze the pros and cons of each option.",
            "I'd recommend reading professional reviews, checking user ratings, and comparing technical specifications before making a decision.",
            "I'd suggest creating a weighted scoring system based on your priorities and then comparing each option systematically."
        ],
        "deal_seeking": [
            "I'd recommend using price comparison tools and checking multiple sources. Also, look into cashback programs and credit card rewards.",
            "I'd suggest researching the typical price range, checking for manufacturer rebates, and looking into bundle deals for better value.",
            "I'd advise checking price history, looking for refurbished options, and researching the best times to buy this type of product."
        ]
    }
    return random.choice(responses.get(context, ["I'd recommend doing more research first."]))

def _create_convenience_seeker_response(context: str, user_question: str) -> str:
    """Create response for convenience seeker persona."""
    responses = {
        "product_recommendation": [
            "I'd recommend the one with the fastest shipping and easiest return policy. Convenience is key when shopping.",
            "Go with the option that offers same-day delivery or pickup. Time is valuable, and you want it as soon as possible.",
            "I'd suggest choosing the retailer with the most convenient pickup or delivery options. Make your life easier!"
        ],
        "product_evaluation": [
            "This looks good and has fast shipping. If it meets your basic needs, go for it - don't overcomplicate things.",
            "I'd recommend this if it's available for quick delivery. Sometimes good enough is perfect when you need it fast.",
            "This seems like a solid choice with convenient options. If it works for your needs, get it and move on."
        ],
        "timing_advice": [
            "Buy it now if you need it. Waiting around for sales isn't worth the time and effort when you can get it today.",
            "Don't wait - if you need it, get it. The convenience of having it now is worth more than saving a few dollars later.",
            "I'd say buy it now. Time is money, and the convenience of getting it immediately is worth the price."
        ],
        "product_comparison": [
            "Choose the one that's easiest to get and return if needed. Convenience trumps minor feature differences.",
            "I'd go with the option that offers the most convenient shopping experience. Don't make it more complicated than it needs to be.",
            "Pick the one with the best customer service and return policy. You want the easiest experience possible."
        ],
        "deal_seeking": [
            "I'd recommend buying from the most convenient retailer, even if it's slightly more expensive. Time is valuable.",
            "Go with the option that offers the fastest and most reliable service. The convenience is worth the extra cost.",
            "I'd suggest choosing based on delivery speed and return convenience rather than just price. Make it easy on yourself."
        ]
    }
    return random.choice(responses.get(context, ["I'd recommend the most convenient option."]))

def _create_eco_conscious_response(context: str, user_question: str) -> str:
    """Create response for eco-conscious persona."""
    responses = {
        "product_recommendation": [
            "I'd recommend looking for products with eco-friendly certifications and sustainable materials. Check the company's environmental practices.",
            "Go with brands that prioritize sustainability and have transparent supply chains. Look for products made from recycled materials.",
            "I'd suggest choosing products with minimal packaging and from companies committed to carbon neutrality."
        ],
        "product_evaluation": [
            "This looks good, but I'd check the company's environmental impact and whether the materials are sustainable.",
            "I'd recommend verifying the product's carbon footprint and whether it's made from renewable or recycled materials.",
            "This seems decent, but I'd look into the company's sustainability practices and product lifecycle impact."
        ],
        "timing_advice": [
            "I'd recommend buying from companies that offset their carbon emissions and use sustainable shipping methods.",
            "Consider the environmental impact of shipping and packaging. Sometimes buying locally is more eco-friendly than online.",
            "I'd suggest choosing retailers that use eco-friendly packaging and carbon-neutral delivery options."
        ],
        "product_comparison": [
            "I'd choose the option with the smallest environmental footprint and from the most sustainable company.",
            "Go with the product that uses the most eco-friendly materials and has the best sustainability practices.",
            "I'd recommend the option with the most transparent environmental impact and sustainable manufacturing process."
        ],
        "deal_seeking": [
            "I'd recommend looking for companies that offer eco-friendly options and sustainable practices, even if they cost a bit more.",
            "Go with retailers that prioritize environmental responsibility and offer carbon-neutral shipping options.",
            "I'd suggest choosing based on environmental impact rather than just price. Sustainable choices are worth the investment."
        ]
    }
    return random.choice(responses.get(context, ["I'd recommend the most eco-friendly option."]))

def _create_minimalist_response(context: str, user_question: str) -> str:
    """Create response for minimalist persona."""
    responses = {
        "product_recommendation": [
            "I'd recommend choosing the simplest option that meets your core needs. Less is more, and you'll appreciate the simplicity.",
            "Go with the most essential version. You don't need all the extra features - focus on what you actually use.",
            "I'd suggest the most streamlined option. Simple, functional, and without unnecessary complexity."
        ],
        "product_evaluation": [
            "This looks good if it serves a clear purpose. Make sure you'll actually use it regularly before buying.",
            "I'd recommend this only if it's truly necessary and you don't already have something that serves the same function.",
            "This seems useful, but ask yourself: do you really need it, or do you just want it? Be honest about necessity."
        ],
        "timing_advice": [
            "I'd recommend waiting until you're absolutely sure you need it. Impulse purchases clutter your space and mind.",
            "Don't buy it unless you've thought about it for at least a week. If you still want it then, it's probably necessary.",
            "I'd suggest waiting. Most things we think we need, we don't actually need. Give it time to see if the desire passes."
        ],
        "product_comparison": [
            "I'd choose the simplest option that does what you need. Extra features just add complexity and potential problems.",
            "Go with the most basic version that meets your requirements. You'll appreciate the simplicity and reliability.",
            "I'd recommend the option with the fewest features. Simple products are easier to use and maintain."
        ],
        "deal_seeking": [
            "I'd recommend buying quality over quantity. One good, simple item is better than multiple cheap, complex ones.",
            "Go with the most reliable, simple option. It's worth paying more for something that will last and won't break down.",
            "I'd suggest investing in fewer, better items rather than many cheap ones. Quality and simplicity are worth the price."
        ]
    }
    return random.choice(responses.get(context, ["I'd recommend the simplest option."]))

def _create_social_validator_response(context: str, user_question: str) -> str:
    """Create response for social validator persona."""
    responses = {
        "product_recommendation": [
            "I'd recommend checking what's popular and well-reviewed. Look for products with high ratings and positive social media buzz.",
            "Go with the option that's trending and has good social proof. You want something that others approve of and recommend.",
            "I'd suggest choosing products that are popular among your peers and have strong community support."
        ],
        "product_evaluation": [
            "This looks good and has great reviews. I'd check what others are saying about it on social media and review sites.",
            "I'd recommend this if it has positive feedback from the community. Social validation is important when making decisions.",
            "This seems popular and well-liked. I'd look at user reviews and social media mentions to confirm it's a good choice."
        ],
        "timing_advice": [
            "I'd recommend checking what others are saying about the best time to buy. Look for community discussions and recommendations.",
            "Go with the timing that others recommend. Check forums and social media for advice from people who've bought similar items.",
            "I'd suggest following the crowd on this one. If everyone's buying now, there's probably a good reason."
        ],
        "product_comparison": [
            "I'd choose the option that's more popular and has better social proof. Go with what others are recommending.",
            "Go with the product that has more positive reviews and social media mentions. Popularity often indicates quality.",
            "I'd recommend the option that's trending and has strong community support. Social validation matters."
        ],
        "deal_seeking": [
            "I'd recommend checking what deals others are finding and sharing. Look for community recommendations and shared discounts.",
            "Go with the retailer that others trust and recommend. Social proof is important when looking for deals.",
            "I'd suggest following community recommendations for the best deals. Others have already done the research for you."
        ]
    }
    return random.choice(responses.get(context, ["I'd recommend checking what others are saying."]))

def _create_generic_response(persona: Dict[str, Any], context: str, user_question: str) -> str:
    """Create a generic response based on persona characteristics."""
    tags = persona.get('psychographic_tags', [])
    
    if 'price_sensitive' in tags:
        return "I'd recommend comparing prices and looking for the best value option."
    elif 'quality_focused' in tags:
        return "I'd suggest focusing on quality and durability over price."
    elif 'brand_loyal' in tags:
        return "I'd recommend sticking with trusted brands you know and love."
    elif 'trend_follower' in tags:
        return "I'd suggest going with what's currently popular and trending."
    else:
        return "I'd recommend doing some research and choosing what works best for your needs."

def create_multi_turn_conversation(persona: Dict[str, Any], scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create a multi-turn conversation for a persona."""
    conversation = []
    
    # Choose random products
    product_type = random.choice(PRODUCT_TYPES)
    product_name = random.choice(PRODUCT_NAMES)
    product1 = random.choice(PRODUCT_NAMES)
    product2 = random.choice(PRODUCT_NAMES)
    
    # First turn - user question
    user_question = random.choice(scenario['user_questions']).format(
        product_type=product_type,
        product_name=product_name,
        product1=product1,
        product2=product2
    )
    
    conversation.append({
        "role": "user",
        "content": user_question
    })
    
    # Assistant response
    assistant_response = create_persona_response(persona, scenario['context'], user_question)
    conversation.append({
        "role": "assistant",
        "content": assistant_response
    })
    
    # Follow-up turn
    follow_up = random.choice(scenario['follow_ups'])
    conversation.append({
        "role": "user",
        "content": follow_up
    })
    
    # Final assistant response
    final_response = create_persona_response(persona, scenario['context'], follow_up)
    conversation.append({
        "role": "assistant",
        "content": final_response
    })
    
    return conversation

def convert_to_sft_format(conversation: List[Dict[str, Any]], persona: Dict[str, Any]) -> Dict[str, Any]:
    """Convert conversation to SFT training format."""
    text_parts = []
    for turn in conversation:
        if turn['role'] == 'user':
            text_parts.append(f"User: {turn['content']}")
        else:
            text_parts.append(f"Assistant: {turn['content']}")
    
    text = "\n".join(text_parts)
    
    return {
        "twin_id": persona['id'],
        "text": text,
        "conversation_length": len(conversation),
        "persona_style": persona.get('psychographic_tags', []),
        "context": "shopping_assistance"
    }

def main():
    parser = argparse.ArgumentParser(description="Prepare persona SFT training data")
    parser.add_argument("--personas_file", type=Path, default=Path("DATA/personas.json"),
                       help="Path to personas JSON file")
    parser.add_argument("--output_dir", type=Path, default=Path("DATA/sft"),
                       help="Output directory for SFT data")
    parser.add_argument("--max_examples_per_persona", type=int, default=500,
                       help="Maximum examples per persona")
    
    args = parser.parse_args()
    
    print("🔄 Loading personas...")
    personas = load_personas(args.personas_file)
    print(f"   Loaded {len(personas)} personas")
    
    print("💬 Creating multi-turn conversations...")
    all_sft_examples = []
    
    for persona in personas:
        print(f"   Processing {persona['id']}...")
        
        persona_examples = []
        for _ in range(args.max_examples_per_persona):
            # Choose random scenario
            scenario = random.choice(SHOPPING_SCENARIOS)
            
            # Create conversation
            conversation = create_multi_turn_conversation(persona, scenario)
            
            # Convert to SFT format
            sft_example = convert_to_sft_format(conversation, persona)
            persona_examples.append(sft_example)
        
        all_sft_examples.extend(persona_examples)
        
        # Save individual persona file
        persona_file = args.output_dir / f"{persona['id']}.jsonl"
        persona_file.parent.mkdir(parents=True, exist_ok=True)
        with open(persona_file, 'w') as f:
            for example in persona_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"     Created {len(persona_examples)} examples -> {persona_file}")
    
    # Save combined file
    combined_file = args.output_dir / "all_personas.jsonl"
    with open(combined_file, 'w') as f:
        for example in all_sft_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"\n✅ SFT data preparation complete!")
    print(f"   Total examples: {len(all_sft_examples)}")
    print(f"   Personas: {len(personas)}")
    print(f"   Output directory: {args.output_dir}")
    print(f"   Combined file: {combined_file}")

if __name__ == "__main__":
    main()

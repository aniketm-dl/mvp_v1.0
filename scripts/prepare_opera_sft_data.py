#!/usr/bin/env python3
"""
Prepare Multi-Turn SFT Training Data from OPeRA Dataset

This script creates multi-turn conversation training data for the 18 discovered personas
from the OPeRA dataset. It converts shopping sessions into conversational format suitable
for SFT training.

Usage:
    python scripts/prepare_opera_sft_data.py
    python scripts/prepare_opera_sft_data.py --max_examples_per_persona 1000
    python scripts/prepare_opera_sft_data.py --output_dir DATA/sft_opera
"""

from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import pickle

# Shopping conversation templates
SHOPPING_TEMPLATES = [
    {
        "user": "I'm looking for {product_type}. What would you recommend?",
        "assistant": "Based on your preferences, I'd suggest {product_name}. {rationale}",
        "context": "product_recommendation"
    },
    {
        "user": "What do you think about this {product_name}?",
        "assistant": "From my perspective, {rationale}. {additional_insight}",
        "context": "product_evaluation"
    },
    {
        "user": "Should I buy this now or wait?",
        "assistant": "Given your shopping style, {rationale}. {recommendation}",
        "context": "timing_advice"
    },
    {
        "user": "I'm comparing {product1} and {product2}. Which is better?",
        "assistant": "For someone with your preferences, {rationale}. {choice_explanation}",
        "context": "product_comparison"
    },
    {
        "user": "What's the best deal on {product_type} right now?",
        "assistant": "I'd recommend {product_name} because {rationale}. {deal_details}",
        "context": "deal_seeking"
    }
]

# Product types and names for template filling
PRODUCT_TYPES = [
    "headphones", "laptop", "smartphone", "tablet", "smartwatch", "camera",
    "speaker", "keyboard", "mouse", "monitor", "desk", "chair", "lamp",
    "book", "clothing", "shoes", "bag", "jewelry", "home decor", "kitchen appliance"
]

PRODUCT_NAMES = [
    "Premium Wireless Headphones", "Gaming Laptop Pro", "Latest Smartphone",
    "Professional Tablet", "Fitness Smartwatch", "DSLR Camera", "Bluetooth Speaker",
    "Mechanical Keyboard", "Wireless Mouse", "4K Monitor", "Standing Desk",
    "Ergonomic Chair", "LED Desk Lamp", "Bestselling Novel", "Designer Jacket",
    "Running Shoes", "Leather Handbag", "Gold Necklace", "Modern Art Print",
    "Coffee Maker"
]

def load_opera_data(data_dir: Path) -> pd.DataFrame:
    """Load OPeRA dataset from processed files."""
    train_file = data_dir / "train.parquet"
    val_file = data_dir / "val.parquet"
    test_file = data_dir / "test.parquet"
    
    dfs = []
    for file_path in [train_file, val_file, test_file]:
        if file_path.exists():
            df = pd.read_parquet(file_path)
            dfs.append(df)
    
    if not dfs:
        raise FileNotFoundError(f"No OPeRA data found in {data_dir}")
    
    return pd.concat(dfs, ignore_index=True)

def discover_personas_from_data(df: pd.DataFrame, n_personas: int = 18) -> Tuple[np.ndarray, KMeans]:
    """Discover personas using K-Means clustering on persona vectors."""
    # Extract persona vectors
    persona_vectors = np.array([vec for vec in df['persona_vec']])
    
    # Apply K-Means clustering
    kmeans = KMeans(n_clusters=n_personas, random_state=42, n_init=10)
    persona_labels = kmeans.fit_predict(persona_vectors)
    
    return persona_labels, kmeans

def create_persona_profiles(df: pd.DataFrame, persona_labels: np.ndarray) -> Dict[int, Dict[str, Any]]:
    """Create persona profiles from clustered data."""
    df_with_labels = df.copy()
    df_with_labels['persona_id'] = persona_labels
    
    personas = {}
    for persona_id in range(18):
        persona_data = df_with_labels[df_with_labels['persona_id'] == persona_id]
        
        if len(persona_data) == 0:
            continue
            
        # Analyze behavior patterns
        action_counts = persona_data['action'].value_counts()
        rationale_text = ' '.join(persona_data['rationale'].dropna().astype(str))
        
        # Create persona profile
        personas[persona_id] = {
            'id': f'persona_{persona_id}',
            'label': f'Persona {persona_id}',
            'session_count': len(persona_data),
            'primary_actions': action_counts.head(3).to_dict(),
            'rationale_patterns': rationale_text[:500],  # First 500 chars
            'avg_actions_per_session': len(persona_data) / len(persona_data['session_id'].unique()),
            'shopping_style': _infer_shopping_style(action_counts, rationale_text)
        }
    
    return personas

def _infer_shopping_style(action_counts: pd.Series, rationale_text: str) -> str:
    """Infer shopping style from actions and rationales."""
    text_lower = rationale_text.lower()
    
    if 'price' in text_lower or 'deal' in text_lower or 'discount' in text_lower:
        return "price_conscious"
    elif 'quality' in text_lower or 'premium' in text_lower or 'brand' in text_lower:
        return "quality_focused"
    elif 'quick' in text_lower or 'fast' in text_lower or 'convenient' in text_lower:
        return "convenience_seeker"
    elif 'compare' in text_lower or 'research' in text_lower or 'review' in text_lower:
        return "research_oriented"
    else:
        return "balanced_shopper"

def create_multi_turn_conversations(persona_data: pd.DataFrame, persona_profile: Dict[str, Any], 
                                  n_examples: int = 100) -> List[Dict[str, Any]]:
    """Create multi-turn conversation examples for a persona."""
    conversations = []
    
    # Group by session to create multi-turn conversations
    sessions = persona_data.groupby('session_id')
    
    for session_id, session_data in sessions:
        if len(session_data) < 2:  # Need at least 2 turns
            continue
            
        # Create conversation turns
        turns = []
        for i, (_, row) in enumerate(session_data.iterrows()):
            if i == 0:
                # First turn - user asks about product
                product_type = random.choice(PRODUCT_TYPES)
                user_msg = f"I'm looking for {product_type}. What would you recommend?"
            else:
                # Follow-up turns based on previous action
                if row['action'] == 'view':
                    user_msg = f"What do you think about this {random.choice(PRODUCT_NAMES)}?"
                elif row['action'] == 'add_to_cart':
                    user_msg = "Should I buy this now or wait?"
                elif row['action'] == 'compare':
                    user_msg = f"I'm comparing {random.choice(PRODUCT_NAMES)} and {random.choice(PRODUCT_NAMES)}. Which is better?"
                else:
                    user_msg = f"What's the best deal on {random.choice(PRODUCT_TYPES)} right now?"
            
            # Create assistant response based on rationale and persona style
            assistant_msg = _create_persona_response(row['rationale'], persona_profile, row['action'])
            
            turns.append({
                "role": "user",
                "content": user_msg
            })
            turns.append({
                "role": "assistant", 
                "content": assistant_msg
            })
        
        if len(turns) >= 4:  # At least 2 exchanges
            conversations.append({
                "twin_id": persona_profile['id'],
                "conversation": turns,
                "session_id": session_id,
                "persona_style": persona_profile['shopping_style']
            })
    
    # If we don't have enough real conversations, generate synthetic ones
    while len(conversations) < n_examples:
        conversation = _generate_synthetic_conversation(persona_profile)
        conversations.append(conversation)
    
    return conversations[:n_examples]

def _create_persona_response(rationale: str, persona_profile: Dict[str, Any], action: str) -> str:
    """Create a persona-specific response based on rationale and shopping style."""
    style = persona_profile['shopping_style']
    
    if style == "price_conscious":
        if "discount" in rationale.lower() or "sale" in rationale.lower():
            return f"I'd recommend this because {rationale}. The discount makes it a great value!"
        else:
            return f"While {rationale}, I'd suggest waiting for a better deal or comparing prices elsewhere."
    
    elif style == "quality_focused":
        if "quality" in rationale.lower() or "premium" in rationale.lower():
            return f"Excellent choice! {rationale}. Quality products are worth the investment."
        else:
            return f"Based on {rationale}, I'd recommend looking for higher quality alternatives."
    
    elif style == "convenience_seeker":
        if "quick" in rationale.lower() or "fast" in rationale.lower():
            return f"Perfect! {rationale}. Convenience is key when shopping."
        else:
            return f"While {rationale}, consider if there's a faster or more convenient option available."
    
    elif style == "research_oriented":
        return f"Interesting perspective. {rationale}. I'd also recommend checking reviews and comparing specifications."
    
    else:  # balanced_shopper
        return f"That makes sense. {rationale}. It seems like a reasonable choice for your needs."

def _generate_synthetic_conversation(persona_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a synthetic conversation for a persona."""
    template = random.choice(SHOPPING_TEMPLATES)
    product_type = random.choice(PRODUCT_TYPES)
    product_name = random.choice(PRODUCT_NAMES)
    
    # Create multi-turn conversation
    turns = []
    
    # Turn 1: Initial question
    user_msg = template["user"].format(
        product_type=product_type,
        product_name=product_name
    )
    turns.append({"role": "user", "content": user_msg})
    
    # Turn 2: Assistant response
    rationale = f"Based on your {persona_profile['shopping_style']} preferences"
    assistant_msg = template["assistant"].format(
        product_name=product_name,
        rationale=rationale,
        additional_insight="This aligns well with your shopping style.",
        recommendation="I'd suggest going for it.",
        choice_explanation="it better matches your needs.",
        deal_details="it offers good value."
    )
    turns.append({"role": "assistant", "content": assistant_msg})
    
    # Turn 3: Follow-up question
    follow_up = random.choice([
        "What about the warranty?",
        "How does the return policy work?",
        "Are there any accessories I should consider?",
        "What's the delivery time?"
    ])
    turns.append({"role": "user", "content": follow_up})
    
    # Turn 4: Final response
    final_response = f"Great question! {rationale}, I'd recommend checking the warranty details and return policy before purchasing."
    turns.append({"role": "assistant", "content": final_response})
    
    return {
        "twin_id": persona_profile['id'],
        "conversation": turns,
        "session_id": f"synthetic_{random.randint(1000, 9999)}",
        "persona_style": persona_profile['shopping_style']
    }

def convert_to_sft_format(conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert conversations to SFT training format."""
    sft_examples = []
    
    for conv in conversations:
        # Convert conversation to text format
        text_parts = []
        for turn in conv['conversation']:
            if turn['role'] == 'user':
                text_parts.append(f"User: {turn['content']}")
            else:
                text_parts.append(f"Assistant: {turn['content']}")
        
        text = "\n".join(text_parts)
        
        sft_examples.append({
            "twin_id": conv['twin_id'],
            "text": text,
            "conversation_length": len(conv['conversation']),
            "persona_style": conv['persona_style'],
            "session_id": conv['session_id']
        })
    
    return sft_examples

def main():
    parser = argparse.ArgumentParser(description="Prepare OPeRA SFT training data")
    parser.add_argument("--data_dir", type=Path, default=Path("DATA/OPeRA/processed"),
                       help="Directory containing OPeRA processed data")
    parser.add_argument("--output_dir", type=Path, default=Path("DATA/sft"),
                       help="Output directory for SFT data")
    parser.add_argument("--max_examples_per_persona", type=int, default=500,
                       help="Maximum examples per persona")
    parser.add_argument("--n_personas", type=int, default=18,
                       help="Number of personas to create")
    
    args = parser.parse_args()
    
    print("🔄 Loading OPeRA data...")
    df = load_opera_data(args.data_dir)
    print(f"   Loaded {len(df)} records from {len(df['session_id'].unique())} sessions")
    
    print("🔍 Discovering personas...")
    persona_labels, kmeans_model = discover_personas_from_data(df, args.n_personas)
    print(f"   Discovered {args.n_personas} personas")
    
    print("📊 Creating persona profiles...")
    persona_profiles = create_persona_profiles(df, persona_labels)
    print(f"   Created profiles for {len(persona_profiles)} personas")
    
    # Save persona profiles
    profiles_file = args.output_dir / "persona_profiles.json"
    profiles_file.parent.mkdir(parents=True, exist_ok=True)
    with open(profiles_file, 'w') as f:
        json.dump(persona_profiles, f, indent=2, default=str)
    print(f"   Saved persona profiles to {profiles_file}")
    
    # Save clustering model
    model_file = args.output_dir / "persona_clustering_model.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump(kmeans_model, f)
    print(f"   Saved clustering model to {model_file}")
    
    print("💬 Creating multi-turn conversations...")
    all_sft_examples = []
    
    for persona_id, profile in persona_profiles.items():
        print(f"   Processing {profile['id']} ({profile['session_count']} sessions)...")
        
        # Get data for this persona
        persona_data = df[persona_labels == persona_id]
        
        # Create conversations
        conversations = create_multi_turn_conversations(
            persona_data, profile, args.max_examples_per_persona
        )
        
        # Convert to SFT format
        sft_examples = convert_to_sft_format(conversations)
        all_sft_examples.extend(sft_examples)
        
        # Save individual persona file
        persona_file = args.output_dir / f"{profile['id']}.jsonl"
        with open(persona_file, 'w') as f:
            for example in sft_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"     Created {len(sft_examples)} examples -> {persona_file}")
    
    # Save combined file
    combined_file = args.output_dir / "all_personas.jsonl"
    with open(combined_file, 'w') as f:
        for example in all_sft_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"\n✅ SFT data preparation complete!")
    print(f"   Total examples: {len(all_sft_examples)}")
    print(f"   Personas: {len(persona_profiles)}")
    print(f"   Output directory: {args.output_dir}")
    print(f"   Combined file: {combined_file}")

if __name__ == "__main__":
    main()

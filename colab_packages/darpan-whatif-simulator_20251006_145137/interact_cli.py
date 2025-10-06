#!/usr/bin/env python3
"""
Interactive CLI for chatting with all 18 Darpan Labs digital twins.
"""

import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.reasoning.llm_runtime import RUNTIME

def load_personas():
    """Load all personas from DATA/personas.json."""
    personas_file = Path("DATA/personas.json")
    data = json.loads(personas_file.read_text())
    return data["personas"]

def print_personas(personas):
    """Print all available personas."""
    print("\n" + "=" * 80)
    print("🎯 DARPAN LABS - 18 DIGITAL TWIN PERSONAS")
    print("=" * 80)

    for i, persona in enumerate(personas, 1):
        twin_id = persona["id"]
        label = persona["label"]
        blurb = persona.get("blurb", "")
        tags = ", ".join(persona.get("psychographic_tags", []))

        print(f"\n{i:2d}. {label}")
        print(f"    ID: {twin_id}")
        print(f"    {blurb}")
        print(f"    Tags: {tags}")

    print("\n" + "=" * 80)

def chat_with_twin(persona):
    """Interactive chat with a specific twin."""
    twin_id = persona["id"]
    label = persona["label"]
    tags = persona.get("psychographic_tags", [])
    blurb = persona.get("blurb", "")

    print("\n" + "=" * 80)
    print(f"💬 CHATTING WITH: {label}")
    print("=" * 80)
    print(f"About: {blurb}")
    print(f"Tags: {', '.join(tags)}")
    print("\nMode: {'REAL LLM' if not RUNTIME.use_stub else 'STUB (Deterministic)'}")
    print("\nType your questions below. Type 'back' to return to menu, 'quit' to exit.")
    print("=" * 80 + "\n")

    history = []

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                sys.exit(0)

            if user_input.lower() in ['back', 'b', 'menu']:
                print("\n↩️  Returning to menu...\n")
                return

            # Get response from twin
            response = RUNTIME.chat(
                twin_label=label,
                twin_id=twin_id,
                prompt=user_input,
                psych_tags=tags
            )

            print(f"{label}: {response}\n")

            history.append({"user": user_input, "twin": response})

        except KeyboardInterrupt:
            print("\n\n↩️  Returning to menu...\n")
            return
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

def main():
    """Main interactive loop."""
    personas = load_personas()

    print("\n" + "=" * 80)
    print("🚀 WELCOME TO DARPAN LABS DIGITAL TWIN SIMULATOR")
    print("=" * 80)
    print(f"\nMode: {'REAL LLM' if not RUNTIME.use_stub else 'STUB (Deterministic)'}")
    print(f"Total Personas: {len(personas)}")

    while True:
        print_personas(personas)

        print("\nChoose a persona to chat with:")
        print("  • Enter number (1-18) to select a persona")
        print("  • Type 'quit' to exit")

        choice = input("\nYour choice: ").strip()

        if choice.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(personas):
                chat_with_twin(personas[idx])
            else:
                print(f"\n❌ Invalid choice. Please enter 1-{len(personas)}\n")
        except ValueError:
            print("\n❌ Invalid input. Please enter a number.\n")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test all 18 MVP twins with stub mode.
Verifies that the updated stub implementation works for all personas.
"""

from __future__ import annotations
import json
from pathlib import Path
from src.reasoning.llm_runtime import RUNTIME

def test_all_twins():
    """Test chat functionality for all 18 personas."""

    # Load personas
    personas_file = Path("DATA/personas.json")
    personas_data = json.loads(personas_file.read_text())
    personas = personas_data["personas"]

    print(f"🎯 Testing All {len(personas)} MVP Twins\n")
    print(f"Mode: {'STUB' if RUNTIME.use_stub else 'REAL LLM'}\n")
    print("=" * 80)

    # Test questions
    questions = [
        "What do you value most when shopping?",
        "How do you feel about prices?",
        "What's important to you about delivery?",
        "How do you make purchase decisions?"
    ]

    passed = 0
    failed = 0

    for i, persona in enumerate(personas, 1):
        twin_id = persona["id"]
        label = persona["label"]
        tags = persona.get("psychographic_tags", [])

        print(f"\n[{i}/{len(personas)}] Testing: {label}")
        print(f"   Twin ID: {twin_id}")
        print(f"   Tags: {', '.join(tags)}")

        try:
            # Test with first question
            question = questions[0]
            response = RUNTIME.chat(
                twin_label=label,
                twin_id=twin_id,
                prompt=question,
                psych_tags=tags
            )

            # Verify response is not empty and reasonable
            if not response or len(response) < 10:
                print(f"   ❌ FAIL: Response too short: '{response}'")
                failed += 1
                continue

            # Verify response doesn't contain error indicators
            error_keywords = ["error", "failed", "exception", "traceback"]
            if any(kw in response.lower() for kw in error_keywords):
                print(f"   ❌ FAIL: Error in response: '{response}'")
                failed += 1
                continue

            print(f"   ✅ PASS: \"{response}\"")
            passed += 1

        except Exception as e:
            print(f"   ❌ FAIL: Exception: {e}")
            failed += 1

    # Summary
    print("\n" + "=" * 80)
    print(f"\n📊 Test Summary:")
    print(f"   • Total twins: {len(personas)}")
    print(f"   • Passed: {passed}")
    print(f"   • Failed: {failed}")
    print(f"   • Success rate: {passed/len(personas)*100:.1f}%")

    if passed == len(personas):
        print(f"\n✅ All {len(personas)} twins working correctly!")
        return 0
    else:
        print(f"\n⚠️  {failed} twins failed - review errors above")
        return 1

def test_persona_variety():
    """Test that different personas give different responses."""

    personas_file = Path("DATA/personas.json")
    personas_data = json.loads(personas_file.read_text())
    personas = personas_data["personas"]

    print(f"\n\n🔍 Testing Response Variety Across Personas\n")
    print("=" * 80)

    question = "What matters most when you shop?"

    responses = {}

    for persona in personas[:5]:  # Test first 5 for variety
        twin_id = persona["id"]
        label = persona["label"]

        response = RUNTIME.chat(
            twin_label=label,
            twin_id=twin_id,
            prompt=question,
            psych_tags=persona.get("psychographic_tags", [])
        )

        responses[twin_id] = response
        print(f"   {label:40s}: \"{response}\"")

    # Check for variety (responses should be different)
    unique_responses = len(set(responses.values()))

    print(f"\n   Unique responses: {unique_responses}/{len(responses)}")

    if unique_responses >= 3:  # At least 3 different responses
        print(f"   ✅ Good variety in responses!")
    else:
        print(f"   ⚠️  Low variety - personas may be too similar")

if __name__ == "__main__":
    import sys

    exit_code = test_all_twins()
    test_persona_variety()

    sys.exit(exit_code)

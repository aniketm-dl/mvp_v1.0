#!/usr/bin/env python3
"""
Validate Personas Against Schema and Repo Invariants

Validates all persona files in DATA/personas/ against:
1. JSON Schema (persona.schema.json)
2. Repo-level invariants (unique IDs, required counts, no LLM params)

Exit codes:
  0 - All validations passed
  1 - Validation failures found
  2 - Script error

Usage:
    python scripts/personas/validate_personas.py
    python scripts/personas/validate_personas.py --verbose
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
import argparse

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("⚠️  jsonschema not installed. Run: pip install jsonschema")


@dataclass
class ValidationResult:
    """Result of validating a single persona."""
    persona_id: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PersonaValidator:
    """Validates personas against schema and repo invariants."""

    def __init__(self, personas_dir: Path, schema_path: Path, verbose: bool = False):
        self.personas_dir = personas_dir
        self.schema_path = schema_path
        self.verbose = verbose
        self.results: List[ValidationResult] = []
        self.schema = None

        # Load schema
        if HAS_JSONSCHEMA and schema_path.exists():
            with open(schema_path) as f:
                self.schema = json.load(f)

    def validate_against_schema(
        self, persona_id: str, persona_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate against JSON Schema."""
        if not HAS_JSONSCHEMA or not self.schema:
            return True, []

        errors = []
        try:
            jsonschema.validate(instance=persona_data, schema=self.schema)
        except jsonschema.exceptions.ValidationError as e:
            errors.append(f"Schema validation failed: {e.message}")
            if self.verbose:
                errors.append(f"  Path: {'.'.join(str(p) for p in e.path)}")
                errors.append(f"  Schema path: {'.'.join(str(p) for p in e.schema_path)}")

        return len(errors) == 0, errors

    def check_decision_heuristics(self, persona_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check decision heuristics meet requirements."""
        errors = []
        heuristics = persona_data.get("decision_heuristics", [])

        if len(heuristics) < 5:
            errors.append(f"Insufficient decision_heuristics: {len(heuristics)} (minimum: 5)")

        # Check structure
        for i, h in enumerate(heuristics):
            if not all(k in h for k in ["if", "then", "because"]):
                errors.append(f"Heuristic {i} missing required fields (if/then/because)")

        return len(errors) == 0, errors

    def check_evaluation_probes(self, persona_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check evaluation probes meet requirements."""
        errors = []
        probes = persona_data.get("evaluation_probes", [])

        if len(probes) < 6:
            errors.append(f"Insufficient evaluation_probes: {len(probes)} (minimum: 6)")

        # Check required categories
        categories = {p.get("category") for p in probes}
        required_categories = {"price", "promo", "delivery", "ad_copy", "returns", "risk"}
        missing = required_categories - categories

        if missing:
            errors.append(f"Missing evaluation probe categories: {missing}")

        return len(errors) == 0, errors

    def check_style_capsule(self, persona_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check style capsule requirements."""
        errors = []
        style = persona_data.get("style_capsule", {})

        target_length = style.get("target_length")
        if target_length != "3-6 sentences":
            errors.append(f"Invalid target_length: '{target_length}' (must be '3-6 sentences')")

        return len(errors) == 0, errors

    def check_no_decoding_params(self, persona_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Ensure no decoding parameters present in persona."""
        errors = []
        warnings = []

        # Recursively check for forbidden keys
        forbidden_keys = {
            "temperature", "top_p", "top_k", "max_tokens", "max_new_tokens",
            "max_length", "num_beams", "do_sample"
        }

        def check_dict(d: Dict[str, Any], path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key

                if key in forbidden_keys:
                    errors.append(
                        f"Forbidden decoding parameter found: {current_path}={value}"
                    )

                if isinstance(value, dict):
                    check_dict(value, current_path)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            check_dict(item, f"{current_path}[{i}]")

        check_dict(persona_data)

        return len(errors) == 0, errors, warnings

    def check_psychographic_ranges(self, persona_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate psychographic trait ranges."""
        errors = []
        psycho = persona_data.get("psychographics", {})
        big_five = psycho.get("big_five", {})

        for trait, value in big_five.items():
            if not isinstance(value, (int, float)):
                errors.append(f"Big Five trait '{trait}' must be numeric, got {type(value)}")
            elif not (-2 <= value <= 2):
                errors.append(f"Big Five trait '{trait}' out of range: {value} (must be -2 to +2)")

        return len(errors) == 0, errors

    def validate_persona(self, persona_file: Path) -> ValidationResult:
        """Validate a single persona file."""
        persona_id = persona_file.stem
        result = ValidationResult(persona_id=persona_id, passed=True)

        try:
            # Load persona
            with open(persona_file) as f:
                persona_data = json.load(f)

            # Run all checks
            checks = [
                ("Schema", self.validate_against_schema(persona_id, persona_data)),
                ("Decision Heuristics", self.check_decision_heuristics(persona_data)),
                ("Evaluation Probes", self.check_evaluation_probes(persona_data)),
                ("Style Capsule", self.check_style_capsule(persona_data)),
                ("Psychographic Ranges", self.check_psychographic_ranges(persona_data)),
            ]

            # Check for decoding params
            passed, errors, warnings = self.check_no_decoding_params(persona_data)
            checks.append(("No Decoding Params", (passed, errors)))
            result.warnings.extend(warnings)

            # Collect errors
            for check_name, (passed, errors) in checks:
                if not passed:
                    result.passed = False
                    for error in errors:
                        result.errors.append(f"[{check_name}] {error}")

        except json.JSONDecodeError as e:
            result.passed = False
            result.errors.append(f"Invalid JSON: {e}")
        except Exception as e:
            result.passed = False
            result.errors.append(f"Validation error: {e}")

        return result

    def check_repo_invariants(self) -> Tuple[bool, List[str]]:
        """Check repo-level invariants (uniqueness, etc.)."""
        errors = []

        # Check unique persona_ids
        persona_files = list(self.personas_dir.glob("*.json"))
        persona_files = [f for f in persona_files if f.name not in ["registry.json", "schema"]]

        persona_ids = []
        for pf in persona_files:
            try:
                with open(pf) as f:
                    data = json.load(f)
                    persona_ids.append(data.get("persona_id"))
            except Exception:
                pass

        # Check for duplicates
        seen = set()
        duplicates = set()
        for pid in persona_ids:
            if pid in seen:
                duplicates.add(pid)
            seen.add(pid)

        if duplicates:
            errors.append(f"Duplicate persona_ids found: {duplicates}")

        # Check filename matches persona_id
        for pf in persona_files:
            try:
                with open(pf) as f:
                    data = json.load(f)
                    pid = data.get("persona_id")
                    if pf.stem != pid:
                        errors.append(f"Filename '{pf.stem}' does not match persona_id '{pid}'")
            except Exception:
                pass

        return len(errors) == 0, errors

    def run_validation(self) -> int:
        """Run validation on all personas."""
        print("🔍 Validating personas...")
        print(f"Directory: {self.personas_dir}")
        print(f"Schema: {self.schema_path}")
        print()

        # Find all persona files
        persona_files = sorted(self.personas_dir.glob("*.json"))
        persona_files = [f for f in persona_files if f.name not in ["registry.json"]]

        if not persona_files:
            print("❌ No persona files found")
            return 1

        print(f"Found {len(persona_files)} persona files\n")

        # Validate each persona
        for persona_file in persona_files:
            result = self.validate_persona(persona_file)
            self.results.append(result)

            if result.passed:
                print(f"✅ {result.persona_id}")
            else:
                print(f"❌ {result.persona_id}")
                for error in result.errors:
                    print(f"    {error}")

            if result.warnings and self.verbose:
                for warning in result.warnings:
                    print(f"    ⚠️  {warning}")

        # Check repo-level invariants
        print("\n🔍 Checking repo-level invariants...")
        inv_passed, inv_errors = self.check_repo_invariants()

        if inv_passed:
            print("✅ All repo invariants satisfied")
        else:
            print("❌ Repo invariant failures:")
            for error in inv_errors:
                print(f"    {error}")

        # Summary
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        print("\n" + "=" * 70)
        print(f"Validation Summary:")
        print(f"  Total personas: {len(self.results)}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Repo invariants: {'✅ PASS' if inv_passed else '❌ FAIL'}")
        print("=" * 70)

        # Return exit code
        if failed == 0 and inv_passed:
            print("\n✅ ALL VALIDATIONS PASSED")
            return 0
        else:
            print("\n❌ VALIDATION FAILED")
            return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate personas against schema and invariants")
    parser.add_argument(
        "--personas-dir",
        type=Path,
        default=Path("DATA/personas"),
        help="Directory containing persona files",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("DATA/personas/schema/persona.schema.json"),
        help="Path to persona schema",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output with warnings",
    )

    args = parser.parse_args()

    # Check dependencies
    if not HAS_JSONSCHEMA:
        print("❌ Missing dependency: jsonschema")
        print("Install with: pip install jsonschema")
        return 2

    # Run validation
    validator = PersonaValidator(
        personas_dir=args.personas_dir,
        schema_path=args.schema,
        verbose=args.verbose,
    )

    return validator.run_validation()


if __name__ == "__main__":
    sys.exit(main())

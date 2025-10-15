#!/usr/bin/env python3
"""
CI Check: Detect Hardcoded Parameters

Scans codebase for hardcoded generation parameters that should be in config files.
Enforces Phase 1 goal: single place to control models, decoding, data, and RAG.

Exit codes:
  0 - All checks passed
  1 - Violations found (fails CI)
  2 - Script error

Usage:
  python scripts/ci_check_hardcoded_params.py
  python scripts/ci_check_hardcoded_params.py --strict  # Fail on warnings too
"""

from __future__ import annotations
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import argparse


@dataclass
class Violation:
    """Represents a config violation."""
    file_path: str
    line_number: int
    line_content: str
    violation_type: str
    severity: str  # ERROR, WARNING, INFO
    message: str


class ConfigChecker:
    """Checks for hardcoded configuration parameters."""

    def __init__(self, root_dir: Path, strict: bool = False):
        self.root_dir = root_dir
        self.strict = strict
        self.violations: List[Violation] = []

        # Directories to scan
        self.scan_dirs = ["src", "scripts"]

        # Directories/files to exclude
        self.exclude_patterns = [
            "*/test_*.py",
            "*/TESTS/*",
            "*/__pycache__/*",
            "*/venv/*",
            "*/.git/*",
            "*/archive/*",
        ]

        # Patterns to detect (pattern, violation_type, severity, message_template)
        self.patterns = [
            # Temperature != 0 (ERROR)
            (
                r'temperature\s*=\s*(?!0(?:\.0)?(?:\s|,|$))\d+\.?\d*',
                "non_zero_temperature",
                "ERROR",
                "Non-zero temperature found: {}. Must be 0 for determinism.",
            ),
            # max_tokens literal (WARNING unless in test/script with args)
            (
                r'max_tokens\s*=\s*\d+',
                "hardcoded_max_tokens",
                "WARNING",
                "Hardcoded max_tokens: {}. Should use config.gen.max_new_tokens",
            ),
            # max_length literal
            (
                r'max_length\s*=\s*\d+',
                "hardcoded_max_length",
                "WARNING",
                "Hardcoded max_length: {}. Should use config.gen.max_length",
            ),
            # max_new_tokens literal
            (
                r'max_new_tokens\s*=\s*\d+',
                "hardcoded_max_new_tokens",
                "WARNING",
                "Hardcoded max_new_tokens: {}. Should use config.gen.max_new_tokens",
            ),
            # learning_rate literal
            (
                r'learning_rate\s*=\s*\d+\.?\d*e?-?\d*',
                "hardcoded_learning_rate",
                "WARNING",
                "Hardcoded learning_rate: {}. Should use config.train.learning_rate",
            ),
            # batch_size literal
            (
                r'batch_size\s*=\s*\d+',
                "hardcoded_batch_size",
                "WARNING",
                "Hardcoded batch_size: {}. Should use config.train.batch_size",
            ),
            # epochs literal
            (
                r'(?:num_train_)?epochs\s*=\s*\d+',
                "hardcoded_epochs",
                "WARNING",
                "Hardcoded epochs: {}. Should use config.train.num_train_epochs",
            ),
            # top_p != 1
            (
                r'top_p\s*=\s*(?!1(?:\.0)?(?:\s|,|$))\d+\.?\d*',
                "non_one_top_p",
                "ERROR",
                "top_p != 1.0 found: {}. Must be 1.0 for determinism.",
            ),
            # Model name literal (not via config)
            (
                r'["\'](?:mistralai|gpt|llama|claude)[/\-\w]+["\']',
                "hardcoded_model_name",
                "WARNING",
                "Hardcoded model name: {}. Should use config.model.base_model",
            ),
        ]

    def should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning."""
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            # Simple glob-like matching
            pattern_re = pattern.replace("*", ".*").replace("?", ".")
            if re.search(pattern_re, file_str):
                return True
        return False

    def is_acceptable_context(self, line: str, pattern_match: str) -> bool:
        """Check if the matched pattern is in an acceptable context."""
        # Allow if it's part of a comment
        if "#" in line and line.index("#") < line.index(pattern_match):
            return True

        # Allow if using args. or config.
        if "args." in line or "config." in line:
            return True

        # Allow if it's in a string literal (not assignment)
        if '"' in line or "'" in line:
            # Check if it's a string value, not an assignment
            if "=" not in line or line.index(pattern_match) < line.index("="):
                return True

        return False

    def scan_file(self, file_path: Path) -> None:
        """Scan a single Python file for violations."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                line_stripped = line.strip()

                # Skip comments and empty lines
                if not line_stripped or line_stripped.startswith("#"):
                    continue

                # Check each pattern
                for pattern, vtype, severity, msg_template in self.patterns:
                    matches = list(re.finditer(pattern, line))

                    for match in matches:
                        matched_text = match.group()

                        # Check if this is acceptable context
                        if self.is_acceptable_context(line_stripped, matched_text):
                            continue

                        # Create violation
                        violation = Violation(
                            file_path=str(file_path.relative_to(self.root_dir)),
                            line_number=line_num,
                            line_content=line_stripped[:100],  # Truncate long lines
                            violation_type=vtype,
                            severity=severity,
                            message=msg_template.format(matched_text),
                        )
                        self.violations.append(violation)

        except Exception as e:
            print(f"Error scanning {file_path}: {e}", file=sys.stderr)

    def scan_directory(self, dir_name: str) -> None:
        """Scan a directory recursively for Python files."""
        dir_path = self.root_dir / dir_name
        if not dir_path.exists():
            return

        for py_file in dir_path.rglob("*.py"):
            if not self.should_exclude(py_file):
                self.scan_file(py_file)

    def run_checks(self) -> int:
        """Run all checks and return exit code."""
        print("🔍 Scanning for hardcoded parameters...")
        print(f"Root: {self.root_dir}")
        print(f"Scan dirs: {', '.join(self.scan_dirs)}")
        print()

        # Scan all directories
        for dir_name in self.scan_dirs:
            self.scan_directory(dir_name)

        # Group violations by severity
        errors = [v for v in self.violations if v.severity == "ERROR"]
        warnings = [v for v in self.violations if v.severity == "WARNING"]
        infos = [v for v in self.violations if v.severity == "INFO"]

        # Report results
        if errors:
            print(f"\n❌ {len(errors)} ERROR(S) FOUND:\n")
            for v in errors:
                print(f"  {v.file_path}:{v.line_number}")
                print(f"    {v.message}")
                print(f"    Line: {v.line_content}")
                print()

        if warnings:
            print(f"\n⚠️  {len(warnings)} WARNING(S) FOUND:\n")
            for v in warnings:
                print(f"  {v.file_path}:{v.line_number}")
                print(f"    {v.message}")
                print(f"    Line: {v.line_content}")
                print()

        if infos:
            print(f"\nℹ️  {len(infos)} INFO:\n")
            for v in infos:
                print(f"  {v.file_path}:{v.line_number}")
                print(f"    {v.message}")
                print()

        # Summary
        print("=" * 70)
        print(f"Total violations: {len(self.violations)}")
        print(f"  Errors: {len(errors)}")
        print(f"  Warnings: {len(warnings)}")
        print(f"  Info: {len(infos)}")
        print("=" * 70)

        # Determine exit code
        if errors:
            print("\n❌ CI CHECK FAILED: Errors found")
            return 1
        elif warnings and self.strict:
            print("\n⚠️  CI CHECK FAILED: Warnings in strict mode")
            return 1
        elif not self.violations:
            print("\n✅ CI CHECK PASSED: No violations found")
            return 0
        else:
            print("\n✅ CI CHECK PASSED: Only warnings (non-strict mode)")
            return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check for hardcoded configuration parameters"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (not just errors)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (default: current directory)",
    )

    args = parser.parse_args()

    # Run checks
    checker = ConfigChecker(root_dir=args.root, strict=args.strict)
    exit_code = checker.run_checks()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

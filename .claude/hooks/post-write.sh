#!/bin/bash
# Post-write hook: runs after any file write operation
# Validates code quality, formatting, and project-specific rules

FILE="$1"
OPERATION="$2"

# Exit early for non-Python files
if [[ ! "$FILE" =~ \.py$ ]]; then
    exit 0
fi

# Skip checks for test files and venv
if [[ "$FILE" =~ venv/ ]] || [[ "$FILE" =~ __pycache__/ ]]; then
    exit 0
fi

echo "🔍 Post-write validation: $FILE"

# 1. Auto-format with black (if available)
if command -v black &> /dev/null; then
    black --quiet "$FILE" 2>/dev/null || true
fi

# 2. Check for determinism violations (critical)
if grep -n "temperature\s*=\s*[^0]" "$FILE" 2>/dev/null; then
    echo "❌ ERROR: Non-zero temperature found in $FILE"
    echo "   All LLM calls must use temperature=0 for determinism"
    exit 1
fi

# 3. Check for missing type hints in function definitions
if grep -Pn "^def \w+\([^)]*\):\s*$" "$FILE" 2>/dev/null | grep -v "__init__" | head -5; then
    echo "⚠️  WARNING: Functions without return type hints found in $FILE"
    echo "   Add -> ReturnType to function signatures"
fi

# 4. Check for hardcoded model parameters (warning only)
if grep -Pn "(model_name|learning_rate|batch_size|epochs)\s*=\s*[\"']?\d" "$FILE" 2>/dev/null | grep -v "args\." | grep -v "config\."; then
    if [[ ! "$FILE" =~ test_ ]] && [[ ! "$FILE" =~ TESTS/ ]]; then
        echo "⚠️  WARNING: Hardcoded parameters found in $FILE"
        echo "   Move to CONFIGS/ for production code"
    fi
fi

# 5. Check imports order
if head -20 "$FILE" | grep -n "^import\|^from" | head -1 | grep -v "from __future__"; then
    echo "⚠️  INFO: First import should be 'from __future__ import annotations'"
fi

# 6. Check for guard usage when dealing with reasons
if grep -n "twin.*decide\|twin.*chat" "$FILE" 2>/dev/null; then
    if ! grep -q "guard\.check\|ReasonGuard" "$FILE" 2>/dev/null; then
        if [[ ! "$FILE" =~ guard\.py ]]; then
            echo "⚠️  WARNING: LLM twin calls without guard.check() in $FILE"
            echo "   All twin reasons must pass through ReasonGuard"
        fi
    fi
fi

# 7. Check for magic number violations in generation params
if grep -Pn "max_tokens\s*=\s*\d+|max_length\s*=\s*\d+" "$FILE" 2>/dev/null | grep -v "args\." | grep -v "config\."; then
    if [[ ! "$FILE" =~ test_ ]] && [[ ! "$FILE" =~ TESTS/ ]]; then
        echo "⚠️  WARNING: Magic numbers for generation params in $FILE"
    fi
fi

echo "✅ Post-write validation complete"
exit 0

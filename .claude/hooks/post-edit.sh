#!/bin/bash
# Post-edit hook: runs after Edit tool usage
# Validates edits maintain code quality and project standards

FILE="$1"
OLD_STRING="$2"
NEW_STRING="$3"

echo "🔍 Post-edit validation: $FILE"

# Exit early for non-code files
if [[ ! "$FILE" =~ \.(py|yaml|json)$ ]]; then
    exit 0
fi

# 1. Check if edit introduced non-deterministic patterns
if [[ "$NEW_STRING" =~ temperature.*=[^0] ]] && [[ ! "$OLD_STRING" =~ temperature ]]; then
    echo "❌ ERROR: Edit introduced non-zero temperature"
    echo "   All LLM calls must use temperature=0"
    exit 1
fi

if [[ "$NEW_STRING" =~ random\. ]] && [[ ! "$NEW_STRING" =~ random\.seed ]]; then
    echo "⚠️  WARNING: Edit introduced random without seed"
fi

# 2. Check if edit removed guard checks
if [[ "$OLD_STRING" =~ guard\.check ]] && [[ ! "$NEW_STRING" =~ guard\.check ]]; then
    echo "❌ ERROR: Edit removed guard.check() call"
    echo "   All LLM reasons must pass through ReasonGuard"
    exit 1
fi

# 3. Check if edit modified allowed_mutables
if [[ "$OLD_STRING" =~ (price_mean|price_min|price_max|promo_badge|delivery_eta_days|copy_variant_id) ]]; then
    if [[ "$NEW_STRING" =~ context_overrides ]] && [[ ! "$NEW_STRING" =~ (price_mean|price_min|price_max|promo_badge|delivery_eta_days|copy_variant_id) ]]; then
        echo "⚠️  WARNING: Edit may have introduced disallowed context override key"
        echo "   Only allowed_mutables can be modified"
    fi
fi

# 4. Check if edit changed test assertions to be less strict
if [[ "$FILE" =~ test_ ]] || [[ "$FILE" =~ TESTS/ ]]; then
    if [[ "$OLD_STRING" =~ assert.*==.* ]] && [[ "$NEW_STRING" =~ assert.*!=.* ]]; then
        echo "⚠️  WARNING: Edit weakened test assertion"
    fi
fi

# 5. Verify file syntax after edit (Python only)
if [[ "$FILE" =~ \.py$ ]]; then
    if command -v python3 &> /dev/null; then
        if ! python3 -m py_compile "$FILE" 2>/dev/null; then
            echo "❌ ERROR: Edit introduced Python syntax error in $FILE"
            exit 1
        fi
    fi
fi

# 6. Check if edit introduced obvious comments (what vs why)
if [[ "$NEW_STRING" =~ #.*(loop through|initialize|return|create a|set.*to) ]]; then
    echo "⚠️  INFO: Consider if comment explains WHY, not WHAT"
    echo "   Comments should add context, not repeat code"
fi

echo "✅ Post-edit validation complete"
exit 0

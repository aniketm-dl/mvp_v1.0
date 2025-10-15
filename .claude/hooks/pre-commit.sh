#!/bin/bash
# Pre-commit hook: runs before git commit operations
# Comprehensive validation to ensure code quality before version control

echo "🚦 Pre-commit validation starting..."

# 1. Run determinism check
echo "1️⃣  Checking determinism..."
if grep -r "temperature\s*=\s*[^0]" src/ scripts/ 2>/dev/null | grep -v test_ | grep -v "\.pyc"; then
    echo "❌ ERROR: Non-deterministic code found"
    exit 1
fi

# 2. Run quick type check (if mypy available)
if command -v mypy &> /dev/null; then
    echo "2️⃣  Running type check..."
    if ! mypy src/ --ignore-missing-imports --no-error-summary 2>/dev/null | head -20; then
        echo "⚠️  WARNING: Type errors found (not blocking)"
    fi
fi

# 3. Check for guard usage
echo "3️⃣  Checking ReasonGuard usage..."
for file in src/api/*.py src/reasoning/*.py; do
    if [[ -f "$file" ]] && grep -q "twin.*decide\|twin.*chat" "$file" 2>/dev/null; then
        if ! grep -q "guard\.check\|ReasonGuard" "$file" 2>/dev/null; then
            if [[ ! "$file" =~ guard\.py ]]; then
                echo "⚠️  WARNING: $file may have unguarded LLM calls"
            fi
        fi
    fi
done

# 4. Check for hardcoded parameters
echo "4️⃣  Checking for hardcoded parameters..."
if grep -r "(model_name|learning_rate|batch_size)\s*=\s*[\"']\w" src/ 2>/dev/null | grep -v "args\." | grep -v "config\." | grep -v test_ | head -5; then
    echo "⚠️  WARNING: Hardcoded parameters found (should be in CONFIGS/)"
fi

# 5. Run test suite (quick mode)
echo "5️⃣  Running test suite..."
if ! PYTHONPATH=. python -m pytest tests/ -q --tb=no 2>&1 | tail -5; then
    echo "❌ ERROR: Tests failing"
    echo "   Fix tests before committing"
    exit 1
fi

# 6. Check quality gates if twin logic modified
if git diff --cached --name-only | grep -q "src/reasoning/\|src/models/mixture"; then
    echo "6️⃣  Twin logic modified - checking quality gates..."
    if command -v make &> /dev/null; then
        if ! make gate 2>&1 | grep -E "(silhouette|JSD|ARI)"; then
            echo "⚠️  WARNING: Quality gates check recommended"
        fi
    fi
fi

echo "✅ Pre-commit validation passed"
exit 0

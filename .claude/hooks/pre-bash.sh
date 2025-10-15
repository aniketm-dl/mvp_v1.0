#!/bin/bash
# Pre-bash hook: validates bash commands before execution
# Prevents dangerous operations and enforces safe practices

COMMAND="$1"

echo "🛡️  Pre-bash validation: $COMMAND"

# 1. Block destructive file operations
if [[ "$COMMAND" =~ rm\ +-rf\ +/ ]]; then
    echo "❌ BLOCKED: Recursive delete from root is not allowed"
    exit 1
fi

if [[ "$COMMAND" =~ sudo ]]; then
    echo "❌ BLOCKED: sudo commands are not allowed"
    exit 1
fi

if [[ "$COMMAND" =~ chmod\ +777 ]]; then
    echo "❌ BLOCKED: chmod 777 is a security risk"
    exit 1
fi

# 2. Prevent modification of protected files
if [[ "$COMMAND" =~ DATA/twin_bank\.json ]] && [[ "$COMMAND" =~ (echo|sed|awk|>|tee) ]]; then
    echo "❌ BLOCKED: Cannot manually edit DATA/twin_bank.json"
    echo "   Regenerate via: python scripts/distill_policies.py"
    exit 1
fi

if [[ "$COMMAND" =~ \.git/config ]] && [[ "$COMMAND" =~ (echo|sed|awk|>|tee) ]]; then
    echo "❌ BLOCKED: Direct git config modification not allowed"
    echo "   Use: git config commands instead"
    exit 1
fi

# 3. Enforce package manager consistency
if [[ "$COMMAND" =~ (pip3|conda|easy_install)\ +install ]] && [[ ! "$COMMAND" =~ pip\ +install ]]; then
    echo "⚠️  WARNING: Use 'pip install' for consistency"
    echo "   Current command: $COMMAND"
fi

# 4. Block operations on lockfiles
if [[ "$COMMAND" =~ (requirements\.txt|poetry\.lock|Pipfile\.lock) ]] && [[ "$COMMAND" =~ (echo|sed|awk|>|tee) ]]; then
    echo "⚠️  WARNING: Manual lockfile edits can break reproducibility"
fi

# 5. Check for use of /tmp or temp paths in production code
if [[ "$COMMAND" =~ /tmp/ ]] && [[ "$COMMAND" =~ (mv|cp).*src/ ]]; then
    echo "⚠️  WARNING: Copying from /tmp to src/ may be unintentional"
fi

# 6. Verify test command format
if [[ "$COMMAND" =~ pytest ]] && [[ ! "$COMMAND" =~ PYTHONPATH ]]; then
    echo "⚠️  INFO: pytest should use PYTHONPATH=. for consistency"
fi

echo "✅ Pre-bash validation passed"
exit 0

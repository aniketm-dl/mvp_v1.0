---
description: Run pre-commit checks before any code changes
---

Before committing code changes, run these checks:

1. **Determinism Check**: Scan for temperature != 0, missing seeds
2. **Type Check**: Run mypy or verify type hints are present
3. **Format Check**: Verify code follows black/ruff formatting
4. **Import Order**: Check imports follow __future__ → stdlib → third-party → local
5. **Config Audit**: Ensure no hardcoded model params in src/
6. **Guard Check**: Verify all LLM outputs go through ReasonGuard
7. **Test Run**: Execute `make test` to ensure no regressions
8. **Gate Check**: Run `make gate` if twin logic was modified

Report all check results. Block commit if any ERROR-level violations found.
Allow commit with warnings but report them clearly.

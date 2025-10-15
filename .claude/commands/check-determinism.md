---
description: Check codebase for non-deterministic patterns
---

Scan the codebase for violations of determinism rules:

1. Search for LLM calls without `temperature=0` and `top_p=1`
2. Find random number generation without seed setting
3. Identify any sampling operations with temperature > 0
4. Check for missing `set_global_seed()` calls in entry points
5. Look for non-canonical sorting (must be by probability desc, then id asc)

Report all violations with file paths and line numbers.
Suggest fixes for each violation found.

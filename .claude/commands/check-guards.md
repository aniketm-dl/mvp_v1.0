---
description: Verify ReasonGuard is used for all LLM outputs
---

Check that all LLM twin reasons pass through ReasonGuard:

1. Find all places where twin.decide() or twin.chat() are called
2. Verify each call is followed by guard.check()
3. Check for direct reason assignments that bypass guard
4. Ensure fallback_reason is provided for guard failures
5. Verify reason caching includes guard validation

Report any unguarded LLM outputs with file:line references.

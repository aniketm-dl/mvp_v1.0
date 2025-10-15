---
description: Run systematic debugging loop for an issue
---

When you encounter a bug or test failure, follow this systematic debugging loop:

## 1. Enumerate Possible Causes
- List all potential root causes based on error message and stack trace
- Consider: schema issues, missing guards, incorrect types, state management, race conditions
- Rank causes by likelihood

## 2. Add Strategic Logging
- Add logging at entry points to functions involved
- Log inputs, intermediate state, and outputs
- Include type information in logs
- Add assertions for invariants

## 3. Validate Hypotheses
- Run tests or reproduce the issue with new logging
- Analyze log output to narrow down root cause
- Test one hypothesis at a time
- Document findings

## 4. Apply Fix
- Implement minimal fix for root cause
- Ensure fix doesn't violate determinism rules
- Update tests to prevent regression
- Verify fix works with full test suite

## 5. Clean Up
- Remove debug logging that's no longer needed
- Keep useful logging that helps future debugging
- Document the issue and fix in comments if non-obvious
- Update CHANGELOG.md if it affects public interface

Report progress at each stage.

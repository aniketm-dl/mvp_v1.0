---
description: Run all quality gates and report metrics
---

Execute the quality gate checks for twin separation:

1. Run `make gate` to check separation metrics
2. Verify silhouette ≥ 0.35
3. Verify mean pairwise JSD ≥ 0.10
4. Verify ARI stability ≥ 0.80
5. Check counterfactual fairness (L1 delta ≤ threshold)

Report all metrics with pass/fail status.
If any gate fails, explain which twins are too similar and suggest remediation.

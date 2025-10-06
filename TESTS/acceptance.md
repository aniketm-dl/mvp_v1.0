Acceptance Tests
1) Determinism: three identical /simulate requests return byte-identical JSON.
2) Separation: silhouette ≥ 0.35; mean pairwise JSD ≥ 0.10 on 1k contexts; ARI ≥ 0.80 across seeds.
3) Faithfulness: zero reasons referencing non-visible attributes; ≤ 20 tokens.
4) Performance: p95 ≤ 200 ms for 5 scenarios × top-5 using distilled heads; ≤ 1 s with per-twin reasons.
5) Accuracy and calibration: keep base MVP targets.

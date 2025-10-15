---
description: Audit for hardcoded parameters that should be in config
---

Find hardcoded model parameters that should live in CONFIGS/:

1. Search for hardcoded model names (e.g., "gpt-3.5", "mistral")
2. Find hardcoded hyperparameters (learning_rate, batch_size, epochs)
3. Identify magic numbers for generation (max_tokens, max_length)
4. Check for hardcoded thresholds in logic
5. Look for URLs, API keys, or environment-specific values

Report violations with suggestions to move to CONFIGS/defaults.yaml or CONFIGS/serve/*.yaml.
Exclude test files from this check.

# SFT Data Format

SFT data format (JSONL, one object per line):
```json
{
  "twin_id": "k3",
  "input": "User: I care about price and delivery.\nAssistant:",
  "output": "I look for a fair price and quick shipping.",
  "meta": {
    "psychographic_tags": ["thrift","speed_focus"],
    "demographic_profile": {"age_band":"25_34","locale":"urban","sex":"F"}
  }
}
```

## Training sources
1) OPeRA behavior + profile slices -> prompts that reflect context and decisions.
2) Your curated prompts per persona.

Place files under `DATA/sft/{twin_id}.jsonl`.

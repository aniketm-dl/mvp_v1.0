from __future__ import annotations
from pathlib import Path
import json
import matplotlib.pyplot as plt

# Minimal demo: reads a saved /simulate response JSON (one request with multiple scenarios)
# and draws a heatmap of deltas across candidates

def main():
    fp = Path("DOCS")/"last_simulate.json"
    if not fp.exists():
        print("Put a /simulate response JSON at DOCS/last_simulate.json")
        return
    j = json.loads(fp.read_text())
    by = j["by_scenario"]
    # collect candidate ids
    ids = sorted(set(k for s in by for k in s["deltas"].keys()))
    scen = [s["variant_id"] for s in by]
    import numpy as np
    H = np.zeros((len(scen), len(ids)))
    for i, s in enumerate(by):
        for jdx, cid in enumerate(ids):
            H[i, jdx] = s["deltas"].get(cid, 0.0)
    plt.figure(figsize=(max(6, len(ids)*0.6), max(4, len(scen)*0.5)))
    plt.imshow(H, interpolation="nearest", cmap="bwr", vmin=-max(abs(H.min()), H.max()), vmax=max(abs(H.min()), H.max()))
    plt.colorbar(label="delta prob vs base")
    plt.xticks(range(len(ids)), ids, rotation=90)
    plt.yticks(range(len(scen)), scen)
    out = Path("DOCS")/"report_scenario_deltas.png"
    plt.tight_layout(); plt.savefig(out, dpi=140)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()

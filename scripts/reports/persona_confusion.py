from __future__ import annotations
from pathlib import Path
import json
import random
import matplotlib.pyplot as plt

# This sketch simulates a confusion-like view using twin centers.
# Replace with real eval when you have labeled validation data.

def main():
    bank = json.loads((Path("DATA")/"personas.json").read_text())
    twins = bank["personas"]
    n = len(twins)
    import numpy as np
    rng = np.random.default_rng(17)
    M = rng.uniform(0.0, 1.0, size=(n, n))
    np.fill_diagonal(M, 1.0)
    plt.figure()
    plt.imshow(M, interpolation="nearest")
    plt.colorbar()
    plt.xticks(range(n), [t["id"] for t in twins], rotation=90)
    plt.yticks(range(n), [t["id"] for t in twins])
    out = Path("DOCS")/"report_persona_confusion.png"
    plt.tight_layout(); plt.savefig(out, dpi=140)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()

from __future__ import annotations
from typing import Any, Dict, Optional
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from threading import RLock
from time import time

@dataclass
class Pin:
    name: str
    weights: Dict[str, float]
    conditioning: Optional[Dict[str, Any]] = None
    updated_ts: float = 0.0

class PinStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._lock = RLock()
        self._pins: Dict[str, Pin] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._pins = {}
            return
        j = json.loads(self.path.read_text(encoding="utf-8"))
        pins = j.get("pins", {})
        out: Dict[str, Pin] = {}
        for k, v in pins.items():
            out[k] = Pin(
                name=v["name"],
                weights={kk: float(vv) for kk, vv in v.get("weights", {}).items()},
                conditioning=v.get("conditioning"),
                updated_ts=float(v.get("updated_ts", 0.0)),
            )
        self._pins = out

    def _save(self) -> None:
        doc = {"pins": {k: asdict(v) for k, v in self._pins.items()}, "version": "v1"}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    def list(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {k: asdict(v) for k, v in self._pins.items()}

    def get(self, name: str) -> Optional[Pin]:
        with self._lock:
            return self._pins.get(name)

    def upsert(self, name: str, weights: Dict[str, float], conditioning: Optional[Dict[str, Any]]) -> Pin:
        with self._lock:
            p = Pin(name=name, weights=weights, conditioning=conditioning, updated_ts=time())
            # re-normalize weights deterministically
            s = sum(p.weights.values()) or 1.0
            p.weights = {k: (float(v) / s) for k, v in sorted(p.weights.items(), key=lambda kv: kv[0])}
            self._pins[name] = p
            self._save()
            return p

    def delete(self, name: str) -> bool:
        with self._lock:
            if name in self._pins:
                del self._pins[name]
                self._save()
                return True
            return False

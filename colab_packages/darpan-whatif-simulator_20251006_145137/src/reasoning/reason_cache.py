from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
from dataclasses import dataclass

@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    puts: int = 0
    size: int = 0
    maxsize: int = 0

class ReasonCache:
    def __init__(self, maxsize: int = 10000) -> None:
        self.maxsize = maxsize
        self._d: "OrderedDict[str, str]" = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.puts = 0

    def get(self, key: str) -> Optional[str]:
        if key in self._d:
            self.hits += 1
            val = self._d.pop(key)
            self._d[key] = val
            return val
        self.misses += 1
        return None

    def put(self, key: str, val: str) -> None:
        if key in self._d:
            self._d.pop(key)
        elif len(self._d) >= self.maxsize:
            self._d.popitem(last=False)
        self._d[key] = val
        self.puts += 1

    def stats(self) -> CacheStats:
        return CacheStats(
            hits=self.hits, misses=self.misses, puts=self.puts,
            size=len(self._d), maxsize=self.maxsize
        )

    def clear(self) -> None:
        self._d.clear()
        self.hits = self.misses = self.puts = 0

REASON_CACHE = ReasonCache(maxsize=10000)

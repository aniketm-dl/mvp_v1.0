from __future__ import annotations
from typing import Dict, Tuple
import time
from fastapi import Request, HTTPException

class SimpleRateLimiter:
    def __init__(self, max_per_min: int = 120) -> None:
        self.max = max(1, int(max_per_min))
        self.bucket: Dict[str, Tuple[int, float]] = {}  # key -> (count, window_start)

    def _key(self, request: Request) -> str:
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        return f"{ip}:{path}"

    async def __call__(self, request: Request, call_next):
        now = time.time()
        key = self._key(request)
        count, start = self.bucket.get(key, (0, now))
        if now - start >= 60.0:
            count, start = 0, now
        count += 1
        self.bucket[key] = (count, start)
        if count > self.max:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")
        return await call_next(request)

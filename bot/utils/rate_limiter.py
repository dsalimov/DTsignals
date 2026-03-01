import asyncio
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, calls_per_second: float = 2.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self._last_call: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def wait(self, key: str = "default"):
        async with self._lock:
            now = time.monotonic()
            last = self._last_call.get(key, 0)
            elapsed = now - last
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self._last_call[key] = time.monotonic()


# Global rate limiter instance
api_limiter = RateLimiter(calls_per_second=2.0)

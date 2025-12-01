from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

import redis
from cachetools import TTLCache

logger = logging.getLogger(__name__)


@dataclass
class CacheBackend:
    ttl_seconds: int = 900

    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    def set(self, key: str, value: Any) -> None:
        raise NotImplementedError


class MemoryCache(CacheBackend):
    def __init__(self, ttl_seconds: int = 900, maxsize: int = 256) -> None:
        super().__init__(ttl_seconds)
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value


class RedisCache(CacheBackend):
    def __init__(self, url: str, ttl_seconds: int = 900) -> None:
        super().__init__(ttl_seconds)
        self._client = redis.Redis.from_url(url)

    def get(self, key: str) -> Optional[Any]:
        raw_value = self._client.get(key)
        if raw_value is None:
            return None
        return json.loads(raw_value)

    def set(self, key: str, value: Any) -> None:
        payload = json.dumps(value)
        self._client.setex(key, self.ttl_seconds, payload)


def build_cache(backend: str, url: str | None = None, ttl_seconds: int = 900) -> CacheBackend:
    normalized = backend.strip().lower()
    if normalized == "redis" and url:
        try:
            client = RedisCache(url=url, ttl_seconds=ttl_seconds)
            client.set("valinor:startup", {"status": "ready"})
            return client
        except Exception as exc:  # noqa: BLE001
            logger.warning("Fallo al inicializar redis, usando cache en memoria: %s", exc)
    return MemoryCache(ttl_seconds=ttl_seconds)

import asyncio
import random
from typing import Optional

import httpx

from .config import settings


class HttpClient:
    def __init__(self, concurrency: int) -> None:
        self._semaphore = asyncio.Semaphore(concurrency)
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (parlay-updater)'
            }
            timeout = httpx.Timeout(30.0)
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
            self._client = httpx.AsyncClient(headers=headers, timeout=timeout, limits=limits)
        return self._client

    async def _jitter(self) -> None:
        await asyncio.sleep(random.uniform(0.1, 0.3))

    async def get(self, url: str) -> httpx.Response:
        client = await self.get_client()
        async with self._semaphore:
            await self._jitter()
            # Simple retry with backoff
            delay = 0.5
            for attempt in range(5):
                try:
                    resp = await client.get(url)
                    return resp
                except Exception:
                    if attempt == 4:
                        raise
                    await asyncio.sleep(delay)
                    delay *= 2

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


http = HttpClient(concurrency=settings.CONCURRENCY)

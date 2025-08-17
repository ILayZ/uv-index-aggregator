from __future__ import annotations

import httpx
import os
from typing import Any, Dict, List

from .base import UVProvider, ProviderResult, clamp_uv


class OpenUVProvider(UVProvider):
    name = "openuv"

    async def fetch(
        self, *, lat: float, lon: float, date: str, tz: str
    ) -> ProviderResult:
        api_key = os.getenv("OPENUV_API_KEY")
        if not api_key:
            return ProviderResult(
                name=self.name, tz=tz, hourly=[], error="disabled (no OPENUV_API_KEY)"
            )
        # OpenUV's public API primarily returns current + short-term forecasts.
        # We'll sample each hour of the day with dt parameter if supported; otherwise return current only.
        headers = {"x-access-token": api_key}
        hourly: List[Dict[str, Any]] = []
        try:
            # Try a simple "current" call; if rate-limited, degrade gracefully.
            url = f"https://api.openuv.io/api/v1/uv?lat={lat}&lng={lon}"
            async with httpx.AsyncClient(timeout=20, headers=headers) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            current = data.get("result", {}).get("uv")
            if current is not None:
                # We don't have forecast by hour in the free tier; emit a single sample at 12:00 local
                hourly.append({"time": f"{date}T12:00:00Z", "uv": clamp_uv(current)})
            return ProviderResult(name=self.name, tz=tz, hourly=hourly)
        except Exception as e:
            return ProviderResult(name=self.name, tz=tz, hourly=[], error=str(e))

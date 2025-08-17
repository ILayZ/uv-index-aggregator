from __future__ import annotations
import httpx
from .base import UVProvider, ProviderResult, clamp_uv


class OpenMeteoProvider(UVProvider):
    name = "open_meteo"

    async def fetch(
        self, *, lat: float, lon: float, date: str, tz: str
    ) -> ProviderResult:
        # Open-Meteo supports hourly uv_index and uv_index_clear_sky.
        # We request UTC by default; tz can be like 'UTC' or 'Europe/Madrid'.
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=uv_index,uv_index_clear_sky&timezone={tz}"
            f"&start_date={date}&end_date={date}"
        )
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            times = data.get("hourly", {}).get("time", [])
            uv = data.get("hourly", {}).get("uv_index", []) or []
            # Fallback to clear-sky if uv is empty
            if not uv:
                uv = data.get("hourly", {}).get("uv_index_clear_sky", []) or []
            hourly = []
            for t, u in zip(times, uv):
                hourly.append({"time": t, "uv": clamp_uv(u)})
            return ProviderResult(name=self.name, tz=tz, hourly=hourly)
        except Exception as e:
            return ProviderResult(name=self.name, tz=tz, hourly=[], error=str(e))

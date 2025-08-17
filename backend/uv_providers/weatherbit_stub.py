from __future__ import annotations
import os, httpx
from typing import Dict, Any, List
from .base import UVProvider, ProviderResult, clamp_uv

class WeatherbitProvider(UVProvider):
    name = "weatherbit"

    async def fetch(self, *, lat: float, lon: float, date: str, tz: str) -> ProviderResult:
        api_key = os.getenv("WEATHERBIT_API_KEY")
        if not api_key:
            return ProviderResult(name=self.name, tz=tz, hourly=[], error="disabled (no WEATHERBIT_API_KEY)")
        # Weatherbit paid plans support hourly UV; for demo we call daily and duplicate as a placeholder.
        try:
            url = f"https://api.weatherbit.io/v2.0/forecast/daily?lat={lat}&lon={lon}&key={api_key}"
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            days = data.get("data", [])
            uv_day = None
            for d in days:
                if d.get("valid_date") == date:
                    uv_day = d.get("uv")
                    break
            hourly: List[Dict[str, Any]] = []
            if uv_day is not None:
                # Fill 24 hours with the same value as a coarse forecast (placeholder)
                for h in range(24):
                    hourly.append({"time": f"{date}T{h:02d}:00:00Z", "uv": clamp_uv(uv_day)})
            return ProviderResult(name=self.name, tz=tz, hourly=hourly)
        except Exception as e:
            return ProviderResult(name=self.name, tz=tz, hourly=[], error=str(e))

from __future__ import annotations
import httpx
from .base import UVProvider, ProviderResult, clamp_uv


class OpenMeteoProvider(UVProvider):
    name = "open_meteo"

    async def fetch(
        self, *, lat: float, lon: float, date: str, tz: str
    ) -> ProviderResult:
        print(f"[DEBUG] {self.name}: Starting fetch for lat={lat}, lon={lon}, date={date}, tz={tz}")
        
        # Open-Meteo supports hourly uv_index and uv_index_clear_sky.
        # We request UTC by default; tz can be like 'UTC' or 'Europe/Madrid'.
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=uv_index,uv_index_clear_sky&timezone={tz}"
            f"&start_date={date}&end_date={date}"
        )
        print(f"[DEBUG] {self.name}: Making request to URL: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            
            print(f"[DEBUG] {self.name}: Received response with status {r.status_code}")
            print(f"[DEBUG] {self.name}: Response data keys: {list(data.keys())}")
            
            times = data.get("hourly", {}).get("time", [])
            uv = data.get("hourly", {}).get("uv_index", []) or []
            # Fallback to clear-sky if uv is empty
            if not uv:
                print(f"[DEBUG] {self.name}: No uv_index data, falling back to uv_index_clear_sky")
                uv = data.get("hourly", {}).get("uv_index_clear_sky", []) or []
            
            print(f"[DEBUG] {self.name}: Found {len(times)} time entries and {len(uv)} UV values")
            
            hourly = []
            for t, u in zip(times, uv):
                hourly.append({"time": t, "uv": clamp_uv(u)})
            
            result = ProviderResult(name=self.name, tz=tz, hourly=hourly)
            print(f"[DEBUG] {self.name}: Returning {len(hourly)} hourly data points")
            return result
        except Exception as e:
            print(f"[DEBUG] {self.name}: Error occurred: {str(e)}")
            return ProviderResult(name=self.name, tz=tz, hourly=[], error=str(e))

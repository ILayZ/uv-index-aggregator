from __future__ import annotations

import httpx
import os
from typing import Any, Dict, List

from .base import UVProvider, ProviderResult, clamp_uv


class WeatherbitProvider(UVProvider):
    name = "weatherbit"

    async def fetch(
        self, *, lat: float, lon: float, date: str, tz: str
    ) -> ProviderResult:
        print(f"[DEBUG] {self.name}: Starting fetch for lat={lat}, lon={lon}, date={date}, tz={tz}")
        
        api_key = os.getenv("WEATHERBIT_API_KEY")
        if not api_key:
            print(f"[DEBUG] {self.name}: No API key found, returning disabled error")
            return ProviderResult(
                name=self.name,
                tz=tz,
                hourly=[],
                error="disabled (no WEATHERBIT_API_KEY)",
            )
        
        # Weatherbit paid plans support hourly UV; for demo we call daily and duplicate as a placeholder.
        try:
            url = f"https://api.weatherbit.io/v2.0/forecast/daily?lat={lat}&lon={lon}&key={api_key}"
            print(f"[DEBUG] {self.name}: Making request to URL: {url}")
            
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            
            print(f"[DEBUG] {self.name}: Received response with status {r.status_code}")
            print(f"[DEBUG] {self.name}: Response data keys: {list(data.keys())}")
            
            days = data.get("data", [])
            print(f"[DEBUG] {self.name}: Found {len(days)} days in response")
            
            uv_day = None
            for d in days:
                if d.get("valid_date") == date:
                    uv_day = d.get("uv")
                    print(f"[DEBUG] {self.name}: Found UV value for {date}: {uv_day}")
                    break
            
            if uv_day is None:
                print(f"[DEBUG] {self.name}: No UV data found for date {date}")
            
            hourly: List[Dict[str, Any]] = []
            if uv_day is not None:
                print(f"[DEBUG] {self.name}: Generating 24 hourly points with UV value {uv_day}")
                # Fill 24 hours with the same value as a coarse forecast (placeholder)
                for h in range(24):
                    hourly.append(
                        {"time": f"{date}T{h:02d}:00:00Z", "uv": clamp_uv(uv_day)}
                    )
            
            result = ProviderResult(name=self.name, tz=tz, hourly=hourly)
            print(f"[DEBUG] {self.name}: Returning {len(hourly)} hourly data points")
            return result
        except Exception as e:
            print(f"[DEBUG] {self.name}: Error occurred: {str(e)}")
            return ProviderResult(name=self.name, tz=tz, hourly=[], error=str(e))

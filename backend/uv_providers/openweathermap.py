from __future__ import annotations

import httpx
import os
from typing import Any, Dict, List
from datetime import datetime, timedelta
import pytz

from .base import UVProvider, ProviderResult, clamp_uv


class OpenWeatherMapProvider(UVProvider):
    name = "openweathermap"

    async def fetch(
        self, *, lat: float, lon: float, date: str, tz: str
    ) -> ProviderResult:
        print(f"[DEBUG] {self.name}: Starting fetch for lat={lat}, lon={lon}, date={date}, tz={tz}")
        
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            print(f"[DEBUG] {self.name}: No API key found, returning disabled error")
            return ProviderResult(
                name=self.name,
                tz=tz,
                hourly=[],
                error="disabled (no OPENWEATHERMAP_API_KEY)",
            )
        
        # OpenWeatherMap UV Index API provides current and forecast data
        # We'll use the forecast endpoint which gives UV index for the next 8 days
        try:
            url = f"https://api.openweathermap.org/data/2.5/uvi/forecast?lat={lat}&lon={lon}&appid={api_key}"
            print(f"[DEBUG] {self.name}: Making request to URL: {url}")
            
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            
            print(f"[DEBUG] {self.name}: Received response with status {r.status_code}")
            print(f"[DEBUG] {self.name}: Response data length: {len(data) if isinstance(data, list) else 'not a list'}")
            
            hourly: List[Dict[str, Any]] = []
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            print(f"[DEBUG] {self.name}: Looking for data for target date: {target_date}")
            
            for item in data:
                # OpenWeatherMap returns unix timestamp
                dt = datetime.fromtimestamp(item.get("date", 0), tz=pytz.UTC)
                if dt.date() == target_date:
                    # Convert to ISO format for consistency
                    time_str = dt.isoformat().replace("+00:00", "Z")
                    uv_value = item.get("value", 0)
                    hourly.append({
                        "time": time_str,
                        "uv": clamp_uv(uv_value)
                    })
            
            print(f"[DEBUG] {self.name}: Found {len(hourly)} matching data points for target date")
            
            # If we don't have hourly data, try to get at least one point for the day
            if not hourly:
                print(f"[DEBUG] {self.name}: No forecast data found, trying current UV endpoint")
                # Fallback: use current UV index if available for the target date
                current_url = f"https://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={api_key}"
                print(f"[DEBUG] {self.name}: Making fallback request to: {current_url}")
                r_current = await client.get(current_url)
                if r_current.status_code == 200:
                    current_data = r_current.json()
                    current_uv = current_data.get("value", 0)
                    print(f"[DEBUG] {self.name}: Got current UV value: {current_uv}")
                    # Add a single point at noon for the requested date
                    hourly.append({
                        "time": f"{date}T12:00:00Z",
                        "uv": clamp_uv(current_uv)
                    })
                else:
                    print(f"[DEBUG] {self.name}: Fallback request failed with status {r_current.status_code}")
            
            result = ProviderResult(name=self.name, tz=tz, hourly=hourly)
            print(f"[DEBUG] {self.name}: Returning {len(hourly)} hourly data points")
            return result
        except Exception as e:
            print(f"[DEBUG] {self.name}: Error occurred: {str(e)}")
            return ProviderResult(name=self.name, tz=tz, hourly=[], error=str(e))

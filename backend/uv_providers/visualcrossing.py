from __future__ import annotations

import httpx
import os
from typing import Any, Dict, List
from datetime import datetime

from .base import UVProvider, ProviderResult, clamp_uv


class VisualCrossingProvider(UVProvider):
    name = "visualcrossing"

    async def fetch(
        self, *, lat: float, lon: float, date: str, tz: str
    ) -> ProviderResult:
        print(f"[DEBUG] {self.name}: Starting fetch for lat={lat}, lon={lon}, date={date}, tz={tz}")
        
        api_key = os.getenv("VISUALCROSSING_API_KEY")
        if not api_key:
            print(f"[DEBUG] {self.name}: No API key found, returning disabled error")
            return ProviderResult(
                name=self.name,
                tz=tz,
                hourly=[],
                error="disabled (no VISUALCROSSING_API_KEY)",
            )
        
        # Visual Crossing Weather API provides UV index in hourly forecast
        try:
            # Visual Crossing API endpoint for timeline weather data
            url = (
                f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
                f"{lat},{lon}/{date}?key={api_key}&include=hours&elements=uvindex"
            )
            print(f"[DEBUG] {self.name}: Making request to URL: {url}")
            
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            
            print(f"[DEBUG] {self.name}: Received response with status {r.status_code}")
            print(f"[DEBUG] {self.name}: Response data keys: {list(data.keys())}")
            
            hourly: List[Dict[str, Any]] = []
            
            # Extract hourly data from the response
            days = data.get("days", [])
            print(f"[DEBUG] {self.name}: Found {len(days)} days in response")
            
            if days:
                day_data = days[0]  # First day should be our target date
                hours = day_data.get("hours", [])
                print(f"[DEBUG] {self.name}: Found {len(hours)} hours for the day")
                
                for hour_data in hours:
                    hour_time = hour_data.get("datetime", "")  # Format: "HH:MM:SS"
                    uv_value = hour_data.get("uvindex")
                    
                    if hour_time and uv_value is not None:
                        # Convert to ISO format
                        time_str = f"{date}T{hour_time}Z"
                        hourly.append({
                            "time": time_str,
                            "uv": clamp_uv(uv_value)
                        })
            
            result = ProviderResult(name=self.name, tz=tz, hourly=hourly)
            print(f"[DEBUG] {self.name}: Returning {len(hourly)} hourly data points")
            return result
        except Exception as e:
            print(f"[DEBUG] {self.name}: Error occurred: {str(e)}")
            return ProviderResult(name=self.name, tz=tz, hourly=[], error=str(e))

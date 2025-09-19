from __future__ import annotations

import os
from datetime import datetime, time
from typing import Any, Dict, List

import httpx
import pytz

from .base import UVProvider, ProviderResult, clamp_uv


class OpenWeatherMapProvider(UVProvider):
    name = "openweathermap"

    async def fetch(
        self, *, lat: float, lon: float, date: str, tz: str
    ) -> ProviderResult:
        print(
            f"[DEBUG] {self.name}: Starting fetch for lat={lat}, lon={lon}, date={date}, tz={tz}"
        )

        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            print(f"[DEBUG] {self.name}: No API key found, returning disabled error")
            return ProviderResult(
                name=self.name,
                tz=tz,
                hourly=[],
                error="disabled (no OPENWEATHERMAP_API_KEY)",
            )

        # OpenWeatherMap deprecated the dedicated UV API. Use the One Call
        # endpoint which returns hourly data including UV index values.
        try:
            url_primary = "https://api.openweathermap.org/data/3.0/onecall"
            url_fallback = "https://api.openweathermap.org/data/2.5/onecall"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                # We only need hourly/daily/current blocks; omit minutely & alerts
                "exclude": "minutely,alerts",
            }
            print(
                f"[DEBUG] {self.name}: Making request to URL: {url_primary} with params: {params}"
            )

            try:
                target_tz = pytz.timezone(tz)
            except Exception:
                target_tz = pytz.UTC

            async with httpx.AsyncClient(timeout=20) as client:
                data = None

                try:
                    r = await client.get(url_primary, params=params)
                    r.raise_for_status()
                    data = r.json()
                    print(
                        f"[DEBUG] {self.name}: Received response with status {r.status_code}"
                    )
                except httpx.HTTPStatusError as exc:
                    print(
                        f"[DEBUG] {self.name}: Primary endpoint failed with status"
                        f" {exc.response.status_code}: {exc}"
                    )
                    if exc.response.status_code in {400, 401, 403, 404}:
                        print(
                            f"[DEBUG] {self.name}: Retrying with fallback URL: {url_fallback}"
                        )
                        r = await client.get(url_fallback, params=params)
                        r.raise_for_status()
                        data = r.json()
                        print(
                            f"[DEBUG] {self.name}: Fallback response status {r.status_code}"
                        )
                    else:
                        raise

                if data is None:
                    raise RuntimeError("No data retrieved from OpenWeatherMap")

                hourly: List[Dict[str, Any]] = []
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                print(
                    f"[DEBUG] {self.name}: Looking for hourly data for target date: {target_date}"
                )

                for item in data.get("hourly", []):
                    dt_utc = datetime.fromtimestamp(item.get("dt", 0), tz=pytz.UTC)
                    dt_local = dt_utc.astimezone(target_tz)
                    if dt_local.date() != target_date:
                        continue
                    uv_value = item.get("uvi")
                    if uv_value is None:
                        continue
                    hourly.append(
                        {
                            "time": dt_utc.isoformat().replace("+00:00", "Z"),
                            "uv": clamp_uv(uv_value),
                        }
                    )

                print(
                    f"[DEBUG] {self.name}: Found {len(hourly)} matching hourly data points"
                )

                if not hourly:
                    print(
                        f"[DEBUG] {self.name}: No hourly data for date, checking daily summary"
                    )
                    for item in data.get("daily", []):
                        dt_utc = datetime.fromtimestamp(item.get("dt", 0), tz=pytz.UTC)
                        dt_local = dt_utc.astimezone(target_tz)
                        if dt_local.date() != target_date:
                            continue
                        uv_value = item.get("uvi")
                        if uv_value is None:
                            continue
                        noon_naive = datetime.combine(target_date, time(12, 0))
                        if hasattr(target_tz, "localize"):
                            noon_local = target_tz.localize(noon_naive)
                        else:
                            noon_local = noon_naive.replace(tzinfo=target_tz)
                        noon_utc = noon_local.astimezone(pytz.UTC)
                        hourly.append(
                            {
                                "time": noon_utc.isoformat().replace("+00:00", "Z"),
                                "uv": clamp_uv(uv_value),
                            }
                        )
                        break

                if not hourly and data.get("current"):
                    print(
                        f"[DEBUG] {self.name}: Falling back to current UV value for date"
                    )
                    current = data["current"]
                    current_uv = current.get("uvi")
                    if current_uv is not None:
                        current_dt_utc = datetime.fromtimestamp(
                            current.get("dt", 0), tz=pytz.UTC
                        )
                        current_dt_local = current_dt_utc.astimezone(target_tz)
                        if current_dt_local.date() == target_date:
                            hourly.append(
                                {
                                    "time": current_dt_utc.isoformat().replace(
                                        "+00:00", "Z"
                                    ),
                                    "uv": clamp_uv(current_uv),
                                }
                            )

            result = ProviderResult(name=self.name, tz=tz, hourly=hourly)
            print(f"[DEBUG] {self.name}: Returning {len(hourly)} hourly data points")
            return result
        except Exception as e:
            print(f"[DEBUG] {self.name}: Error occurred: {str(e)}")
            return ProviderResult(name=self.name, tz=tz, hourly=[], error=str(e))

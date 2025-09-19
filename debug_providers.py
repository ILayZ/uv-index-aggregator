#!/usr/bin/env python
"""
Debug provider responses.
"""
import sys
import asyncio
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from uv_providers.open_meteo import OpenMeteoProvider
from uv_providers.openuv_stub import OpenUVProvider
from uv_providers.weatherbit_stub import WeatherbitProvider
from uv_providers.openweathermap import OpenWeatherMapProvider
from uv_providers.visualcrossing import VisualCrossingProvider

async def debug_providers():
    """Debug individual provider responses."""
    print("Debugging UV Index Providers...")
    print("=" * 50)
    
    lat, lon = 37.1882, -3.6067  # Granada, Spain
    date = "2025-09-17"
    tz = "Europe/Madrid"
    
    providers = [
        OpenMeteoProvider(),
        OpenUVProvider(), 
        WeatherbitProvider(),
        OpenWeatherMapProvider(),
        VisualCrossingProvider()
    ]
    
    for provider in providers:
        print(f"\n🔍 Testing {provider.name}...")
        try:
            result = await provider.fetch(lat=lat, lon=lon, date=date, tz=tz)
            print(f"  ✅ Success: {len(result.get('hourly', []))} data points")
            if result.get('error'):
                print(f"  ⚠️  Error: {result['error']}")
            if result.get('hourly'):
                sample = result['hourly'][0] if result['hourly'] else None
                if sample:
                    print(f"  📊 Sample: {sample}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_providers())

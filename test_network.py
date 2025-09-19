#!/usr/bin/env python
"""
Test network connectivity to Open-Meteo API.
"""
import asyncio
import httpx

async def test_open_meteo():
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.1882&longitude=-3.6067&hourly=uv_index&timezone=UTC&start_date=2025-09-19&end_date=2025-09-19"
    
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            print(f"Testing URL: {url}")
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Data keys: {list(data.keys())}")
                if 'hourly' in data:
                    hourly = data['hourly']
                    print(f"Hourly data keys: {list(hourly.keys())}")
                    if 'uv_index' in hourly:
                        uv_values = hourly['uv_index']
                        print(f"UV values: {uv_values[:5]}...")  # First 5 values
            else:
                print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
        print(f"Exception type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_open_meteo())

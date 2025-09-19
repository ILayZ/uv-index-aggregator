#!/usr/bin/env python
"""
Test script for the UV Index Aggregator API.
"""
import asyncio
import httpx

async def test_api():
    """Test the main API endpoints."""
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient() as client:
        print("Testing UV Index Aggregator API...")
        print("=" * 50)
        
        # Test health endpoint
        try:
            response = await client.get(f"{base_url}/health")
            print(f"✅ Health check: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return
        
        # Test providers endpoint
        try:
            response = await client.get(f"{base_url}/providers")
            print(f"✅ Providers: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Providers check failed: {e}")
        
        # Test UV data endpoint (Granada, Spain coordinates)
        try:
            params = {
                "lat": 37.1882,
                "lon": -3.6067,
                "date": "2025-09-17",
                "tz": "auto"
            }
            response = await client.get(f"{base_url}/uv", params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ UV data: {response.status_code}")
                print(f"   Location: {data['lat']}, {data['lon']}")
                print(f"   Date: {data['date']}")
                print(f"   Timezone: {data['tz']}")
                print(f"   Providers: {len(data['providers'])}")
                print(f"   Hourly data points: {len(data['hourly'])}")
                if data['summary']['uv_max']:
                    print(f"   Max UV: {data['summary']['uv_max']} at {data['summary']['uv_max_time']}")
                print(f"   Advice: {data['summary']['advice'][0] if data['summary']['advice'] else 'No advice'}")
            else:
                print(f"❌ UV data failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ UV data request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())

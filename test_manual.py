#!/usr/bin/env python
"""
Manual test to debug the server.
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import and test the app
from app import app
from fastapi.testclient import TestClient

def test_application():
    """Test the FastAPI application manually."""
    client = TestClient(app)
    
    print("Testing UV Index Aggregator...")
    print("=" * 40)
    
    # Test health endpoint
    response = client.get("/health")
    print(f"Health: {response.status_code} - {response.json()}")
    
    # Test providers endpoint
    response = client.get("/providers")
    print(f"Providers: {response.status_code} - {response.json()}")
    
    # Test UV endpoint with sample coordinates
    response = client.get("/uv?lat=37.1882&lon=-3.6067&date=2025-09-17&tz=auto")
    print(f"UV data: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Location: {data['lat']}, {data['lon']}")
        print(f"  Date: {data['date']}")
        print(f"  Timezone: {data['tz']}")
        print(f"  Providers: {[p['name'] for p in data['providers']]}")
        print(f"  Hourly data points: {len(data['hourly'])}")
        if data['summary']['uv_max']:
            print(f"  Max UV: {data['summary']['uv_max']} at {data['summary']['uv_max_time']}")
    else:
        print(f"  Error: {response.text}")

if __name__ == "__main__":
    test_application()

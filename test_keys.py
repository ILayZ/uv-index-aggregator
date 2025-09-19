#!/usr/bin/env python
"""
Test API keys status
"""
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "backend" / ".env")

print("🔍 API Key Status Check")
print("=" * 40)

# Check each API key
keys = {
    "OpenUV": "OPENUV_API_KEY",
    "Weatherbit": "WEATHERBIT_API_KEY", 
    "OpenWeatherMap": "OPENWEATHERMAP_API_KEY",
    "Visual Crossing": "VISUALCROSSING_API_KEY"
}

for provider, key_name in keys.items():
    key_value = os.getenv(key_name)
    if key_value:
        # Mask the key for security
        masked = key_value[:8] + "*" * (len(key_value) - 12) + key_value[-4:] if len(key_value) > 12 else "*" * len(key_value)
        print(f"✅ {provider}: {masked}")
    else:
        print(f"❌ {provider}: Not set")

print("\n🌐 Backend directory check")
print("=" * 40)
backend_env = Path(__file__).parent / "backend" / ".env"
print(f"Backend .env exists: {backend_env.exists()}")
if backend_env.exists():
    print(f"Backend .env path: {backend_env}")
    
root_env = Path(__file__).parent / ".env"  
print(f"Root .env exists: {root_env.exists()}")
if root_env.exists():
    print(f"Root .env path: {root_env}")

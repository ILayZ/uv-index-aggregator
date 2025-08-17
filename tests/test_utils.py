import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import backend.app as app_module
from backend.app import cache_key, detect_tz
from backend.uv_providers.base import clamp_uv


def test_clamp_uv_none():
    assert clamp_uv(None) is None


def test_clamp_uv_bounds():
    assert clamp_uv(-3.0) == 0.0
    assert clamp_uv(20.0) == 15.0
    assert clamp_uv(5.5) == 5.5


def test_cache_key_format():
    latitude = 12.345678
    longitude = 98.765432
    date_string = "2024-02-03"
    timezone = "UTC"
    result = cache_key(lat=latitude, lon=longitude, date=date_string, tz=timezone)
    assert result == "12.3457,98.7654,2024-02-03,UTC"


def test_detect_tz_known_location():
    latitude = 40.7128
    longitude = -74.0060
    timezone = detect_tz(latitude, longitude)
    assert timezone == "America/New_York"


def test_detect_tz_fallback(monkeypatch):
    class DummyFinder:
        def timezone_at(self, *positional_arguments, **keyword_arguments):
            return None

    monkeypatch.setattr(app_module, "TF", DummyFinder())
    timezone = detect_tz(0.0, 0.0)
    assert timezone == "UTC"

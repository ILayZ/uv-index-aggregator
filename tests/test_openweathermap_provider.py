from __future__ import annotations

import asyncio
import importlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List

import httpx
import pytz

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OpenWeatherMapProvider = importlib.import_module(
    "backend.uv_providers.openweathermap"
).OpenWeatherMapProvider


class FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload
        self.request = None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = httpx.Response(
                status_code=self.status_code,
                request=self.request,
            )
            raise httpx.HTTPStatusError(
                message=f"HTTP {self.status_code}",
                request=self.request,
                response=response,
            )

    def json(self) -> Any:
        return self._payload


class FakeAsyncClient:
    def __init__(
        self, responses: Iterable[FakeResponse], *args: Any, **kwargs: Any
    ) -> None:
        self._responses: List[FakeResponse] = list(responses)

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None

    async def get(self, url: str, params=None) -> FakeResponse:  # type: ignore[override]
        if not self._responses:
            raise AssertionError("No more fake responses configured")
        response = self._responses.pop(0)
        response.request = httpx.Request("GET", url, params=params)
        return response


def run_fetch(provider: OpenWeatherMapProvider, **kwargs: Any):
    return asyncio.run(provider.fetch(**kwargs))


def test_fetch_uses_hourly_data(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    timestamp = int(datetime(2023, 10, 1, 9, tzinfo=pytz.UTC).timestamp())
    responses = [
        FakeResponse(
            200,
            {
                "hourly": [{"dt": timestamp, "uvi": 5.0}],
                "daily": [],
                "current": {},
            },
        )
    ]

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: FakeAsyncClient(responses, *args, **kwargs),
    )

    provider = OpenWeatherMapProvider()
    result = run_fetch(
        provider,
        lat=1.0,
        lon=2.0,
        date="2023-10-01",
        tz="UTC",
    )

    assert result["hourly"] == [{"time": "2023-10-01T09:00:00Z", "uv": 5.0}]


def test_daily_fallback_when_hourly_missing(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    timestamp = int(datetime(2023, 10, 1, 16, tzinfo=pytz.UTC).timestamp())
    responses = [
        FakeResponse(
            200,
            {
                "hourly": [],
                "daily": [{"dt": timestamp, "uvi": 6.5}],
                "current": {},
            },
        )
    ]

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: FakeAsyncClient(responses, *args, **kwargs),
    )

    provider = OpenWeatherMapProvider()
    result = run_fetch(
        provider,
        lat=40.0,
        lon=-73.0,
        date="2023-10-01",
        tz="America/New_York",
    )

    assert result["hourly"] == [{"time": "2023-10-01T16:00:00Z", "uv": 6.5}]


def test_current_fallback_when_no_hourly_or_daily(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    timestamp = int(datetime(2023, 10, 1, 12, tzinfo=pytz.UTC).timestamp())
    responses = [
        FakeResponse(
            200,
            {
                "hourly": [],
                "daily": [],
                "current": {"dt": timestamp, "uvi": 3.2},
            },
        )
    ]

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: FakeAsyncClient(responses, *args, **kwargs),
    )

    provider = OpenWeatherMapProvider()
    result = run_fetch(
        provider,
        lat=10.0,
        lon=20.0,
        date="2023-10-01",
        tz="UTC",
    )

    assert result["hourly"] == [{"time": "2023-10-01T12:00:00Z", "uv": 3.2}]


def test_fallback_to_legacy_endpoint(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "dummy")

    timestamp = int(datetime(2023, 10, 1, 9, tzinfo=pytz.UTC).timestamp())
    responses = [
        FakeResponse(404, {}),
        FakeResponse(
            200,
            {
                "hourly": [{"dt": timestamp, "uvi": 4.4}],
                "daily": [],
                "current": {},
            },
        ),
    ]

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: FakeAsyncClient(responses, *args, **kwargs),
    )

    provider = OpenWeatherMapProvider()
    result = run_fetch(
        provider,
        lat=1.0,
        lon=2.0,
        date="2023-10-01",
        tz="UTC",
    )

    assert result["hourly"] == [{"time": "2023-10-01T09:00:00Z", "uv": 4.4}]

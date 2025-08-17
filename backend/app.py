from __future__ import annotations

import asyncio
import datetime as dt
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo

from .uv_providers.open_meteo import OpenMeteoProvider
from .uv_providers.openuv_stub import OpenUVProvider
from .uv_providers.weatherbit_stub import WeatherbitProvider

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="UV Index Aggregator", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TF = TimezoneFinder(in_memory=True)


class HourBucket(BaseModel):
    time: str
    consensus: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    confidence: Optional[float] = None
    providers: Dict[str, Optional[float]] = Field(default_factory=dict)
    outliers: List[str] = Field(default_factory=list)


class Summary(BaseModel):
    uv_max: Optional[float] = None
    uv_max_time: Optional[str] = None
    advice: List[str] = Field(default_factory=list)
    windows: Dict[str, List[Dict[str, str]]] = Field(
        default_factory=dict
    )  # keys: best/moderate/avoid


class UVResponse(BaseModel):
    lat: float
    lon: float
    date: str
    tz: str
    now_local_iso: str
    now_bucket_time: Optional[str] = None
    providers: List[Dict[str, Any]]
    hourly: List[HourBucket]
    summary: Summary


# Simple in-memory cache: key -> (timestamp, data)
_CACHE: Dict[str, Any] = {}


def cache_key(lat: float, lon: float, date: str, tz: str) -> str:
    return f"{lat:.4f},{lon:.4f},{date},{tz}"


def detect_tz(lat: float, lon: float) -> str:
    tzname = TF.timezone_at(lat=lat, lng=lon)
    return tzname or "UTC"


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/providers")
def providers_status():
    return {
        "open_meteo": True,
        "openuv": bool(os.getenv("OPENUV_API_KEY")),
        "weatherbit": bool(os.getenv("WEATHERBIT_API_KEY")),
    }


@app.get("/uv", response_model=UVResponse)
async def uv(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    date: str = Query(None, description="YYYY-MM-DD (defaults to today in UTC)"),
    tz: Optional[str] = Query(
        None,
        description="IANA tz like 'UTC' or 'Europe/Madrid'. Use 'auto' or leave empty to detect.",
    ),
):
    # Resolve tz
    if not tz or (isinstance(tz, str) and tz.lower() == "auto"):
        tz = detect_tz(lat, lon)

    # Cache
    key = cache_key(lat, lon, date or "", tz)
    if key in _CACHE:
        return _CACHE[key]

    if not date:
        date = dt.datetime.utcnow().strftime("%Y-%m-%d")

    # Time context
    try:
        zone = ZoneInfo(tz)
    except Exception:
        tz = "UTC"
        zone = ZoneInfo("UTC")
    now_local = dt.datetime.now(dt.timezone.utc).astimezone(zone)

    providers = [OpenMeteoProvider(), OpenUVProvider(), WeatherbitProvider()]

    async def run(p):
        return await p.fetch(lat=lat, lon=lon, date=date, tz=tz)

    results = await asyncio.gather(*[run(p) for p in providers])

    # Build provider meta & frame list
    frames: List[pd.DataFrame] = []
    meta: List[Dict[str, Any]] = []
    for r in results:
        meta.append({"name": r.get("name"), "error": r.get("error")})
        hourly = r.get("hourly") or []
        if not hourly:
            continue
        df = pd.DataFrame(hourly)
        df = df.set_index("time").sort_index()
        df = df.rename(columns={"uv": r.get("name")})
        frames.append(df)

    if frames:
        df_all = pd.concat(frames, axis=1)
    else:
        df_all = pd.DataFrame()

    # Hourly aggregation
    hourly_out: List[HourBucket] = []
    times_index: List[str] = []

    if not df_all.empty:
        df_all = df_all.apply(pd.to_numeric, errors="coerce")
        times_index = [str(i) for i in df_all.index]
        for ts, row in df_all.iterrows():
            vals = row.dropna().values.tolist()
            pb = HourBucket(time=str(ts), providers=row.to_dict())
            if len(vals) == 0:
                hourly_out.append(pb)
                continue
            series = pd.Series(vals)
            median = float(series.median())
            mad = float((series - median).abs().median())
            low = max(0.0, median - mad)
            high = min(15.0, median + mad)
            confidence = max(0.0, min(1.0, 1.0 - (mad / 3.0)))
            outliers = []
            if mad > 0:
                for name, v in row.items():
                    if pd.isna(v):
                        continue
                    if abs(float(v) - median) > 1.5 * mad:
                        outliers.append(name)
            pb.consensus = round(median, 2)
            pb.low = round(low, 2)
            pb.high = round(high, 2)
            pb.confidence = round(confidence, 2)
            pb.outliers = outliers
            hourly_out.append(pb)

    # Daily summary helpers
    def parse_local(ts: str) -> dt.datetime:
        # Provider timestamps are already in the requested tz; parse as naive local for ordering/display
        try:
            return dt.datetime.fromisoformat(ts.replace("Z", ""))
        except Exception:
            # Fallback: strip seconds
            return dt.datetime.fromisoformat(ts.split("+")[0])

    def compress_windows(
        points: List[tuple[str, Optional[float]]], predicate
    ) -> List[Dict[str, str]]:
        """Compress consecutive hourly points satisfying predicate into [start,end) intervals."""
        intervals: List[Dict[str, str]] = []
        run_start = None
        prev_t = None
        for ts, v in points:
            ok = (v is not None) and predicate(v)
            if ok and run_start is None:
                run_start = ts
                prev_t = ts
            elif ok and run_start is not None:
                prev_t = ts
            elif (not ok) and run_start is not None:
                # close the interval at prev_t + 1h
                end = (parse_local(prev_t) + dt.timedelta(hours=1)).isoformat(
                    timespec="minutes"
                )
                intervals.append({"start": run_start, "end": end})
                run_start = None
        if run_start is not None:
            end = (parse_local(prev_t) + dt.timedelta(hours=1)).isoformat(
                timespec="minutes"
            )
            intervals.append({"start": run_start, "end": end})
        return intervals

    # Build summary
    summary = Summary()
    if hourly_out:
        # Max UV & time
        pairs = [(h.time, h.consensus) for h in hourly_out if h.consensus is not None]
        if pairs:
            uv_max_time, uv_max = max(pairs, key=lambda t: t[1])
            summary.uv_max = float(uv_max)
            summary.uv_max_time = uv_max_time

            # SPF advice by peak UV (simple WHO-inspired guidance)
            peak = uv_max
            advice: List[str] = []
            if peak <= 2:
                advice.append("Low: SPF optional; sunglasses if bright.")
            elif 3 <= peak <= 5:
                advice.append(
                    "Moderate: SPF 30+, sunglasses, hat; seek shade around midday."
                )
            elif 6 <= peak <= 7:
                advice.append(
                    "High: SPF 50, reapply every 2h; cover up; limit 11:00–17:00."
                )
            elif 8 <= peak <= 10:
                advice.append(
                    "Very High: SPF 50+, reapply 2h; cover up; avoid 11:00–17:00."
                )
            else:
                advice.append(
                    "Extreme: SPF 50+, minimize time outdoors; full cover; avoid 10:00–18:00."
                )
            advice.append(
                "Reapply sunscreen every ~2 hours, and after swimming/sweating."
            )
            summary.advice = advice

            # Windows
            best = compress_windows(pairs, lambda v: v < 3)  # best exposure (low)
            moderate = compress_windows(pairs, lambda v: 3 <= v < 6)  # moderate caution
            avoid = compress_windows(pairs, lambda v: v >= 8)  # avoid peak
            summary.windows = {"best": best, "moderate": moderate, "avoid": avoid}

    # Choose now_bucket_time as the nearest hourly label
    now_bucket_time: Optional[str] = None
    if times_index:
        # Convert now_local to naive local hour string comparable to index
        now_hour_local = now_local.replace(minute=0, second=0, microsecond=0)
        # Find exact match first
        if str(now_hour_local) in times_index:
            now_bucket_time = str(now_hour_local)
        else:
            # Pick nearest by absolute difference
            def abs_minutes(ts: str) -> int:
                try:
                    return abs(
                        int((parse_local(ts) - now_hour_local).total_seconds() // 60)
                    )
                except Exception:
                    return 10**9

            now_bucket_time = min(times_index, key=abs_minutes)

    payload = UVResponse(
        lat=lat,
        lon=lon,
        date=date,
        tz=tz,
        now_local_iso=now_local.isoformat(timespec="seconds"),
        now_bucket_time=now_bucket_time,
        providers=meta,
        hourly=hourly_out,
        summary=summary,
    ).model_dump()

    _CACHE[key] = payload
    return payload

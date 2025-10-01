# UV Index Aggregator (weekend project)

FastAPI backend with pluggable UV providers and a tiny static frontend (HTMX + Plotly). The service aggregates hourly UV forecasts into a single consensus view with a MAD‑based confidence band, outlier flags, and per‑provider traces. It can automatically detect the timezone for the supplied coordinates and caches responses in‑memory to limit upstream API calls.

## Features

- Aggregate data from multiple providers: Open‑Meteo, OpenUV (optional), and Weatherbit (optional).
- Median consensus with a Median Absolute Deviation (MAD) confidence band and outlier detection.
- Automatic timezone detection via [`timezonefinder`](https://github.com/MrMinimal64/timezonefinder) or specify an IANA zone manually.
- Lightweight in‑memory caching.
- Static frontend for visualization using HTMX and Plotly.

## Run (no Docker)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `frontend/index.html` in your browser and click **Fetch** (backend runs at `http://localhost:8080`).

## Record a frontend demo

You can capture a short video that demonstrates the frontend changes without
starting the backend. The recorder spins up a temporary static file server,
mocks the `/uv` API response with bundled sample data, and saves a WebM video.

```bash
pip install playwright
playwright install chromium
python scripts/record_demo.py --output demo/uv-index-demo.webm
```

The script writes the clip to the `demo/` directory by default; pass a
different `--output` path if you prefer another location or filename.

## Docker

```bash
cd backend
docker build -t uv-agg .
docker run --rm -p 8080:8080 --env-file .env uv-agg
```

## Environment variables

Copy `.env.example` to `.env` and set keys if you want to try optional providers:
- `OPENUV_API_KEY`
- `WEATHERBIT_API_KEY`

Without keys, those providers are disabled; Open‑Meteo works out‑of‑the‑box.

## API

- `GET /health` → `{ "ok": true }`
- `GET /providers` → provider availability and key presence
- `GET /uv?lat=..&lon=..&date=YYYY-MM-DD&tz=UTC`
  - `date` defaults to **today (UTC)** if omitted
  - `tz` accepts an IANA string or `auto` to detect timezone from the coordinates

### Response shape (example)

```json
{
  "lat": 37.1882,
  "lon": -3.6067,
  "date": "2025-08-17",
  "tz": "UTC",
  "providers": [
    {"name":"open_meteo","error":null},
    {"name":"openuv","error":"disabled (no OPENUV_API_KEY)"},
    {"name":"weatherbit","error":"disabled (no WEATHERBIT_API_KEY)"}
  ],
  "hourly": [
    {
      "time": "2025-08-17T06:00:00Z",
      "consensus": 0.12,
      "low": 0.05,
      "high": 0.2,
      "confidence": 0.98,
      "providers": {"open_meteo": 0.12},
      "outliers": []
    }
  ]
}
```

The response also includes a `summary` object with the peak UV for the day, SPF guidance, and recommended exposure windows (`best`, `moderate`, `avoid`).

## Notes

- The confidence band uses Median Absolute Deviation (MAD) for robustness.
- Outliers are providers with |value − median| > 1.5 × MAD for a given hour.
- Values are clamped to [0, 15] for safety; the standard UV scale is 0–11+.
- This is a weekend build: the OpenUV and Weatherbit adapters are **stubs** designed to be safely disabled unless you add keys.

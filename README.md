# UV Index Aggregator (weekend project)

FastAPI backend with pluggable UV providers and a tiny static frontend (HTMX + Plotly). Ships consensus (median), confidence band (MAD), outlier flags, and per‑provider traces.

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
  - `tz` is passed through to providers (Open‑Meteo supports IANA strings, e.g., `Europe/Madrid`)

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

## Notes

- The confidence band uses Median Absolute Deviation (MAD) for robustness.
- Outliers are providers with |value − median| > 1.5 × MAD for a given hour.
- Values are clamped to [0, 15] for safety; the standard UV scale is 0–11+.
- This is a weekend build: the OpenUV and Weatherbit adapters are **stubs** designed to be safely disabled unless you add keys.

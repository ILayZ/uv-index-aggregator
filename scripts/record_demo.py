"""Record a short demo video of the UV Index frontend with mocked data.

This script uses Playwright to open the static frontend, intercept the
API request for UV data, and render the graph using a bundled demo JSON
payload. The browser session records a video that can be shared with
testers or stakeholders.

Example:
    python scripts/record_demo.py --output demo/session.webm
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import socketserver
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

from playwright.async_api import Playwright, async_playwright


class ThreadingHTTPServer(socketserver.ThreadingTCPServer):
    """Threading HTTP server with address reuse enabled."""

    allow_reuse_address = True


class FrontendServer(contextlib.AbstractAsyncContextManager):
    """Serve the static frontend directory during the demo run."""

    def __init__(self, directory: Path, port: int = 0) -> None:
        self._directory = directory
        self._port = port
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    async def __aenter__(self) -> "FrontendServer":
        handler = partial(SimpleHTTPRequestHandler, directory=str(self._directory))
        self._httpd = ThreadingHTTPServer(("127.0.0.1", self._port), handler)
        self._port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=5)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._port}/index.html"


async def record_demo(
    playwright: Playwright, data_path: Path, output: Path, duration: int
) -> Path:
    frontend_dir = Path(__file__).parent.parent / "frontend"

    async with FrontendServer(frontend_dir) as server:
        browser = await playwright.chromium.launch(headless=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        context = await browser.new_context(record_video_dir=str(output.parent))
        page = await context.new_page()

        demo_payload = json.loads(data_path.read_text(encoding="utf-8"))

        async def fulfill_demo(route):
            await route.fulfill(
                content_type="application/json", body=json.dumps(demo_payload)
            )

        await page.route("**/uv?*", fulfill_demo)

        await page.goto(server.url)
        await page.wait_for_load_state("domcontentloaded")

        await page.fill("#lat", f"{demo_payload['lat']:.4f}")
        await page.fill("#lon", f"{demo_payload['lon']:.4f}")
        await page.fill("#date", demo_payload.get("date", ""))
        await page.fill("#tz", demo_payload.get("tz", ""))
        await page.click("#go")

        await page.wait_for_selector("text=Data Providers", timeout=10000)
        await page.wait_for_timeout(duration)

        video_relative = await page.video.path() if page.video else None
        await context.close()
        await browser.close()

    if not video_relative:
        raise RuntimeError("Playwright did not record a video for the session")

    video_path = Path(video_relative)
    final_path = output.with_suffix(output.suffix or video_path.suffix)
    video_path.rename(final_path)
    return final_path


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record a demo run of the UV Index frontend."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("frontend/demo-data.json"),
        help="Path to the demo JSON payload used to mock the API response.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo/uv-index-demo.webm"),
        help="Where to write the recorded video.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=2000,
        help="Additional milliseconds to wait after the chart is rendered before closing.",
    )
    args = parser.parse_args()

    async with async_playwright() as playwright:
        video_path = await record_demo(
            playwright, args.data, args.output, args.duration
        )
    print(f"Demo recorded to {video_path}")


if __name__ == "__main__":
    asyncio.run(main())

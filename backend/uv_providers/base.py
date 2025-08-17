from __future__ import annotations
from abc import ABC, abstractmethod


class ProviderResult(dict):
    """
    Keys:
      - name: provider name
      - tz: timezone string used (e.g., 'UTC')
      - hourly: list of { "time": ISO8601, "uv": float }
      - error: Optional[str]
    """

    pass


class UVProvider(ABC):
    name: str

    @abstractmethod
    async def fetch(
        self, *, lat: float, lon: float, date: str, tz: str
    ) -> ProviderResult: ...


def clamp_uv(x: float) -> float:
    # UV index scale: 0..11+; clamp for safety
    if x is None:
        return None
    return max(0.0, min(float(x), 15.0))  # allow some headroom beyond 11

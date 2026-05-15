"""Tunable defaults for async report create/poll (single-account runs)."""

from __future__ import annotations

import random
from typing import Final

# Wall-clock cap for polling (primary stop condition).
MAX_POLL_MINUTES: Final[float] = 60.0

# Jitter added to each sleep to avoid synchronized retries.
POLL_JITTER_MAX_SECONDS: Final[float] = 3.0

# Create-report retries (transient errors / 429).
CREATE_RETRY_ATTEMPTS: Final[int] = 6

# Safety cap on poll iterations if wall-clock logic misconfigured.
MAX_POLL_ATTEMPTS_SAFETY: Final[int] = 500


def compute_poll_interval_seconds(attempt_index: int, *, jitter_max: float | None = None) -> float:
    """
    Aggressive polling for faster results: Fixed 5s for first 30 attempts (2.5 mins).
    Amazon reports typically ready in 20-90s.
    """
    jm = POLL_JITTER_MAX_SECONDS if jitter_max is None else jitter_max
    if attempt_index < 30:
        base = 5.0
    else:
        base = 15.0 + float((attempt_index - 30) % 10)
    return base + random.uniform(0.0, jm)

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
    Staged backoff: 5,8,12 then 20,25,30 then steady 45-60s, plus jitter.
    attempt_index is 0-based (first sleep after attempt 0 status check uses index 0).
    """
    jm = POLL_JITTER_MAX_SECONDS if jitter_max is None else jitter_max
    if attempt_index < 3:
        base = (5.0, 8.0, 12.0)[attempt_index]
    elif attempt_index < 6:
        base = (20.0, 25.0, 30.0)[attempt_index - 3]
    else:
        base = 45.0 + float((attempt_index - 6) % 16)
    return base + random.uniform(0.0, jm)

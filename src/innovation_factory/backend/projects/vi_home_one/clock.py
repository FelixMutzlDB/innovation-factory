"""Reference clock for vi-home-one's time-relative data.

vi-home-one's energy data is anchored to "now": the seed lays down 24 hourly
readings ending at the current time, and the read APIs filter to a trailing
window ("last 24h/30d"). Seed writes and API reads therefore both go through
``reference_now()`` so they always agree on the same instant — otherwise a
frozen seed time would fall outside the read window and the charts would come
back empty.

Determinism: set ``VH_REFERENCE_NOW`` to an ISO-8601 timestamp and every
time-relative value is measured from that fixed instant, so the pages render
identically on every run (used by the visual-regression CI job). Unset — in
prod and normal dev — it is the real wall clock, so this module is a no-op.
"""
import os
from datetime import datetime, timezone

from ...logger import logger

_ENV_VAR = "VH_REFERENCE_NOW"


def reference_now() -> datetime:
    """Timezone-aware UTC "now", or a frozen instant from ``VH_REFERENCE_NOW``.

    A naive override is assumed to be UTC. A malformed value is ignored (falls
    back to the wall clock) with a warning, so a bad env var can never take the
    app down.
    """
    raw = os.environ.get(_ENV_VAR)
    if raw:
        try:
            parsed = datetime.fromisoformat(raw)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning(
                f"{_ENV_VAR}={raw!r} is not a valid ISO-8601 timestamp; "
                "falling back to the wall clock."
            )
    return datetime.now(timezone.utc)

import asyncio
from datetime import datetime, time, timedelta
from typing import Awaitable, Callable
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def seconds_until(time_str: str, tz_name: str) -> float:
    """Return seconds from now until the next occurrence of HH:MM in tz.
    time_str: 'HH:MM' 24h.
    tz_name: IANA tz name.
    """
    if ZoneInfo is None:
        # Fallback: assume local time
        tz = None
    else:
        tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    hh, mm = [int(x) for x in time_str.split(":", 1)]
    target_today = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target_today <= now:
        target_today = target_today + timedelta(days=1)
    delta = target_today - now
    return max(0.0, delta.total_seconds())


async def run_daily(task: Callable[[], Awaitable[bool]], time_str: str, tz_name: str) -> None:
    """Run task once per day at specified local time. Sleeps until next run, executes, repeats."""
    while True:
        delay = seconds_until(time_str, tz_name)
        await asyncio.sleep(delay)
        try:
            await task()
        except Exception:
            # swallow and continue
            pass

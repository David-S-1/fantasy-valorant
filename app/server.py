import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import settings, configured_event_urls
from .pipeline import refresh_event, daily_refresh
from .scheduler import run_daily
from .storage import get_storage_stats


class Broadcaster:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def publish(self, message: str) -> None:
        await self._queue.put(message)

    async def events(self) -> AsyncGenerator[str, None]:
        while True:
            msg = await self._queue.get()
            yield msg


broadcaster = Broadcaster()


async def poller_task() -> None:
    while True:
        try:
            changed, written = await refresh_event()
            if changed:
                await broadcaster.publish('points-updated')
        except Exception:
            # ignore errors, continue polling
            pass
        await asyncio.sleep(settings.POLL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    poll_task = asyncio.create_task(poller_task())
    daily_task = None
    if settings.DAILY_RUN:
        async def daily_job():
            changed = await daily_refresh(configured_event_urls())
            if changed:
                await broadcaster.publish('points-updated')
                await broadcaster.publish('daily-snapshot')
            return changed
        daily_task = asyncio.create_task(run_daily(daily_job, settings.DAILY_RUN_AT, settings.TIMEZONE))
    try:
        yield
    finally:
        poll_task.cancel()
        if daily_task:
            daily_task.cancel()
        try:
            await poll_task
        except Exception:
            pass


app = FastAPI(lifespan=lifespan)

# Serve only specific static roots to avoid shadowing /api/*
app.mount('/templates', StaticFiles(directory='templates', html=False), name='templates')
app.mount('/json', StaticFiles(directory='json', html=False), name='json')


@app.get('/api/points')
async def api_points(event: Optional[str] = None):
    # mirrors JSON files; simplest is to return combined latest *_points.json for event slug
    event = event or ''
    files: List[str] = []
    for name in os.listdir(settings.JSON_DIR):
        if name.endswith('_points.json') and (not event or name.startswith(event)):
            files.append(os.path.join(settings.JSON_DIR, name))
    merged = {}
    for path in files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                merged.update(json.load(f))
        except Exception:
            continue
    return merged


@app.get('/api/status')
async def api_status():
    stats = get_storage_stats()
    return {
        'poll_seconds': settings.POLL_SECONDS,
        'write_policy': stats['write_policy'],
        'json_dir_file_count': stats['json_dir_file_count'],
        'json_dir_bytes': stats['json_dir_bytes'],
        'last_daily_run': 'N/A',  # TODO: track this in state
        'files_written': 0,  # TODO: track this in state
        'snapshots_enabled': stats['snapshots_enabled'],
        'snapshot_dir_bytes': stats['snapshot_dir_bytes'],
        'snapshot_retention_days': stats['snapshot_retention_days']
    }


@app.get('/api/stream')
async def api_stream():
    async def event_gen():
        async for msg in broadcaster.events():
            yield f"data: {msg}\n\n"
    return StreamingResponse(event_gen(), media_type='text/event-stream')


@app.get('/api/snapshots/latest')
async def snapshots_latest():
    root = settings.SNAPSHOT_DIR
    if not os.path.isdir(root):
        return {'latest': None}
    dates = sorted([d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))])
    latest = dates[-1] if dates else None
    meta = None
    if latest and os.path.exists(os.path.join(root, latest, '_manifest.json')):
        try:
            with open(os.path.join(root, latest, '_manifest.json'), 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception:
            meta = None
    return {'latest': latest, 'manifest': meta}


@app.get('/api/snapshots/{date}')
async def snapshots_by_date(date: str):
    root = os.path.join(settings.SNAPSHOT_DIR, date)
    if not os.path.isdir(root):
        return {'date': date, 'files': []}
    files = [f for f in os.listdir(root) if f.endswith('.json')]
    return {'date': date, 'files': files}

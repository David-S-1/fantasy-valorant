import asyncio
import json
import os
from typing import List, Tuple

from .config import settings, configured_event_urls
from .vlr_event import discover_matches
from .vlr_match import fetch_match, content_hash, parse_overview_for_maps, parse_performance_all, parse_maps_with_players
from .state import get_match_state, upsert_match_state
from .scoring import compute_points
from .postprocess import build_player_display
from .storage import write_json, cleanup_old_snapshots, get_storage_stats


from typing import Optional


async def refresh_event(event_url: Optional[str] = None) -> Tuple[int, List[str]]:
    """Incremental refresh: discover matches, detect changes, parse and write json for changed ones only.
    Returns (num_changed, list_of_written_files)
    """
    event_url = event_url or settings.EVENT_URL
    if not event_url:
        return 0, []
    matches = await discover_matches(event_url)
    # Derive event slug for output filenames (keep ./json schema compatible)
    parts = event_url.split('/')
    event_slug = parts[5] if len(parts) > 5 else 'event'
    changed_prefixes: List[str] = []
    written_files: List[str] = []
    for m in matches:
        overview_html, perf_html = await fetch_match(m.url)
        digest = content_hash(overview_html, perf_html)
        prev = get_match_state(m.match_id)
        if prev and prev[3] == digest:
            continue  # no change
        # parse and write minimal *_stats.json compatible with existing consumers
        perf_all = parse_performance_all(perf_html)
        maps = parse_maps_with_players(m.url, overview_html, perf_all)
        # write per-event stage stats json path like existing pipeline
        stage = (m.stage or 'playoffs').replace(' ', '_')
        event_prefix = f"{event_slug}_{stage}"
        stats_filename = f"{event_prefix}_stats.json"
        flat: List[dict] = []
        for mp in maps:
            for p in mp.players:
                d = p.dict()
                d['map_name'] = mp.map_name
                d['match_url'] = m.url
                flat.append(d)

        # Use new storage system
        written = write_json(stats_filename, flat)
        written_files.extend(written)

        upsert_match_state(m.match_id, m.url, digest, m.status or 'unknown')
        changed_prefixes.append(event_prefix)

    # recompute points for changed prefixes
    if changed_prefixes:
        written_files.extend(compute_points(changed_prefixes, json_dir=settings.JSON_DIR))
        written_files.append(build_player_display(json_dir=settings.JSON_DIR))

    return len(changed_prefixes), written_files


async def daily_refresh(event_urls: Optional[List[str]] = None) -> bool:
    """Run a full refresh for the configured events according to write policy.
    Returns True if any changes or snapshots were written.
    """
    urls = event_urls or configured_event_urls()
    any_changes = False
    written_any = []

    # Clean up old snapshots on startup
    folders_deleted, bytes_reclaimed = cleanup_old_snapshots()
    if folders_deleted > 0:
        print(f"Cleaned up {folders_deleted} old snapshot folders, reclaimed {bytes_reclaimed} bytes")

    for url in urls:
        changed, written = await refresh_event(url)
        any_changes = any_changes or (changed > 0)
        written_any.extend(written)

    # Handle snapshots according to policy
    if settings.SNAPSHOT_ENABLE and settings.WRITE_POLICY in ('snapshot', 'both'):
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
        snapshot_root = os.path.join(settings.SNAPSHOT_DIR, date_str)
        os.makedirs(snapshot_root, exist_ok=True)
        files = []

        # Copy points and stats files for event slugs
        slugs = []
        slug_variants = set()
        for url in urls:
            parts = url.split('/')
            base = parts[5] if len(parts) > 5 else 'event'
            slugs.append(base)
            slug_variants.add(base)
            slug_variants.add(base.replace('-', '_'))

        for name in os.listdir(settings.JSON_DIR):
            if any(name.startswith(slug) for slug in slug_variants):
                src = os.path.join(settings.JSON_DIR, name)
                dst = os.path.join(snapshot_root, name)
                try:
                    with open(src, 'rb') as rf, open(dst, 'wb') as wf:
                        wf.write(rf.read())
                    files.append(name)
                except Exception:
                    pass

        # Write manifest
        manifest = {
            'date': date_str,
            'events': slugs,
            'files': files,
            'generated_at': datetime.now().isoformat(),
        }
        manifest_path = os.path.join(snapshot_root, '_manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        written_any.append(manifest_path)

    # Print storage report
    stats = get_storage_stats()
    files_written = len([f for f in written_any if f.endswith('.json')])
    print(f"Daily refresh complete: {files_written} files written, policy={stats['write_policy']}, snapshots={stats['snapshots_enabled']}")

    return any_changes or bool(written_any)

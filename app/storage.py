import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .config import settings
from .state import get_file_hash, upsert_file_hash


def compute_content_hash(data: dict) -> str:
    """Compute a stable hash of JSON data."""
    # Sort keys for consistent hashing
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def atomic_write_json(file_path: str, data: dict) -> bool:
    """Write JSON data atomically using temp file then replace.
    Returns True if file was written, False if skipped due to no change."""

    # Compute content hash
    content_hash = compute_content_hash(data)

    # Check if we need to write
    stored = get_file_hash(file_path)
    if stored and stored[0] == content_hash:
        return False  # No change, skip write

    # Ensure directory exists (skip for root files)
    dirname = os.path.dirname(file_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    # Write to temp file first
    temp_dir = os.path.dirname(file_path) if os.path.dirname(file_path) else '.'
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, dir=temp_dir) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path = f.name

    try:
        # Atomic replace
        os.replace(temp_path, file_path)

        # Update stored hash
        upsert_file_hash(file_path, content_hash, os.path.getmtime(file_path))
        return True
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except:
            pass
        raise


def write_json(file_path: str, data: dict, policy: str = None) -> List[str]:
    """Write JSON data according to the specified policy.
    Returns list of written file paths."""

    policy = policy or settings.WRITE_POLICY
    written_files = []

    # Handle special case for files that should be written to repo root
    if os.path.basename(file_path) == 'player_display.json':
        # Write to repo root for compatibility
        if atomic_write_json(file_path, data):
            written_files.append(file_path)
        return written_files

    # Always write to main JSON_DIR if policy is replace or both
    if policy in ('replace', 'both'):
        main_path = os.path.join(settings.JSON_DIR, os.path.basename(file_path))
        if atomic_write_json(main_path, data):
            written_files.append(main_path)

    # Write to snapshot if policy is snapshot or both, and snapshots are enabled
    if policy in ('snapshot', 'both') and settings.SNAPSHOT_ENABLE:
        date_str = datetime.now().strftime('%Y-%m-%d')
        snapshot_dir = os.path.join(settings.SNAPSHOT_DIR, date_str)
        snapshot_path = os.path.join(snapshot_dir, os.path.basename(file_path))

        if atomic_write_json(snapshot_path, data):
            written_files.append(snapshot_path)

    return written_files


def cleanup_old_snapshots() -> Tuple[int, int]:
    """Delete snapshot folders older than retention period.
    Returns (folders_deleted, bytes_reclaimed)."""

    if not settings.SNAPSHOT_ENABLE:
        return 0, 0

    cutoff_date = datetime.now() - timedelta(days=settings.SNAPSHOT_RETENTION_DAYS)
    folders_deleted = 0
    bytes_reclaimed = 0

    if not os.path.exists(settings.SNAPSHOT_DIR):
        return 0, 0

    for folder_name in os.listdir(settings.SNAPSHOT_DIR):
        folder_path = os.path.join(settings.SNAPSHOT_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue

        try:
            folder_date = datetime.strptime(folder_name, '%Y-%m-%d')
            if folder_date < cutoff_date:
                # Calculate size before deletion
                folder_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(folder_path)
                    for filename in filenames
                )

                shutil.rmtree(folder_path)
                folders_deleted += 1
                bytes_reclaimed += folder_size
        except ValueError:
            # Skip folders that don't match date format
            continue

    return folders_deleted, bytes_reclaimed


def get_storage_stats() -> Dict:
    """Get current storage statistics."""
    stats = {
        'write_policy': settings.WRITE_POLICY,
        'snapshots_enabled': settings.SNAPSHOT_ENABLE,
        'snapshot_retention_days': settings.SNAPSHOT_RETENTION_DAYS,
    }

    # JSON_DIR stats
    if os.path.exists(settings.JSON_DIR):
        json_files = [f for f in os.listdir(settings.JSON_DIR) if f.endswith('.json')]
        stats['json_dir_file_count'] = len(json_files)
        stats['json_dir_bytes'] = sum(
            os.path.getsize(os.path.join(settings.JSON_DIR, f)) for f in json_files
        )
    else:
        stats['json_dir_file_count'] = 0
        stats['json_dir_bytes'] = 0

    # Snapshot stats
    if settings.SNAPSHOT_ENABLE and os.path.exists(settings.SNAPSHOT_DIR):
        snapshot_bytes = 0
        for root, dirs, files in os.walk(settings.SNAPSHOT_DIR):
            snapshot_bytes += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        stats['snapshot_dir_bytes'] = snapshot_bytes
    else:
        stats['snapshot_dir_bytes'] = 0

    return stats

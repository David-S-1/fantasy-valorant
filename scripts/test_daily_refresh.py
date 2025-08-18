#!/usr/bin/env python3
"""
Test script to verify daily refresh works with new storage policy.
Run with: python test_daily_refresh.py
"""

import asyncio
import os
from app.pipeline import daily_refresh
from app.storage import get_storage_stats

async def test_daily_refresh():
    """Test that daily refresh works with default settings."""
    print("Testing daily refresh with default storage policy...")

    # Get initial stats
    initial_stats = get_storage_stats()
    print(f"Initial stats: {initial_stats}")

    # Run daily refresh
    result = await daily_refresh()
    print(f"Daily refresh result: {result}")

    # Get final stats
    final_stats = get_storage_stats()
    print(f"Final stats: {final_stats}")

    print("✓ Daily refresh test completed")

if __name__ == "__main__":
    asyncio.run(test_daily_refresh())

"""
Monthly evaluation counter reset script.

Run this at the start of each month (e.g., via cron or scheduler):
    0 0 1 * * cd /path/to/backend && ./venv/bin/python scripts/reset_monthly_counters.py

Resets evaluations_this_month to 0 for all users. This is simpler than
tracking rolling windows or storing per-month records — KISS wins here.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend root to sys.path so app modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import AsyncSessionLocal


async def reset_counters():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("UPDATE users SET evaluations_this_month = 0 WHERE evaluations_this_month > 0")
        )
        await session.commit()
        print(f"✅ Reset evaluations_this_month for {result.rowcount} users")


if __name__ == "__main__":
    asyncio.run(reset_counters())

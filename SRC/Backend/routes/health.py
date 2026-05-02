"""
Backend documentation for `routes/health.py`.

This route module keeps HTTP concerns thin: validate inputs, call service-layer logic, and return typed API responses.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.db.session import get_db

router = APIRouter(tags=["ops"])


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/health")
async def health(session: AsyncSession = Depends(get_db)):
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}


# Explanation:
# `health` performs a minimal DB round-trip to confirm the application and
# database connectivity are functioning. It returns a simple status JSON.
#
# Alternative (commented, placed immediately below function as requested):
# Instead of a DB check, a lightweight in-memory check can be used when
# DB reachability is not required, or combine both for fuller health info.
#
# @router.get("/health")
# async def health_no_db():
#     return {"status": "ok", "db": "skipped"}

"""
Backend documentation for `db/session.py`.

This backend module participates in the appointment platform and is documented to make future changes safer.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from SRC.Backend.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


# Function explanation:
# `get_db` is an async generator dependency that yields a database
# session for request-scoped operations. Using `expire_on_commit=False`
# avoids detaching loaded objects on commit, which simplifies some workflows.
#
# Alternative (commented): use a request-scoped middleware to set up the
# session and attach it to the request state, or use synchronous sessions
# in environments where async DB drivers are not required.
#
# async def get_db_middleware():
#     # middleware pattern that creates session and assigns it to request.state
#     pass

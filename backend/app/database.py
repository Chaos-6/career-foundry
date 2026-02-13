"""
Database connection and session management.

Key concepts:
- We use SQLAlchemy 2.0's async API with asyncpg driver
- AsyncSession gives us non-blocking database calls (important for a web server
  handling many concurrent requests)
- get_db() is a "dependency" that FastAPI injects into route handlers —
  it provides a session and ensures cleanup after each request
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Create the async engine
# - echo=True logs all SQL in development (helpful for debugging)
# - pool_size=5 keeps 5 connections ready (good for dev, increase for prod)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
)

# Session factory — creates new database sessions
# - expire_on_commit=False means objects stay usable after commit
#   (without this, accessing an attribute after commit triggers a lazy load,
#    which fails with async)
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Every model inherits from this. It provides the table mapping machinery.
    """

    pass


async def get_db():
    """FastAPI dependency that provides a database session.

    Usage in a route:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically closed when the request finishes,
    even if an error occurs (that's what the try/finally does).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables defined by our models.

    Called once at startup. In production, you'd use Alembic migrations
    instead, but for MVP this is simpler.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

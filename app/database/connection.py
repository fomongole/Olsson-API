from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlunparse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings
from app.database.models import Base

# Render/Neon give postgres:// or postgresql://; SQLAlchemy async requires postgresql+asyncpg://
db_url = settings.DATABASE_URL
is_postgres = db_url.startswith("postgres://") or db_url.startswith("postgresql://") or "asyncpg" in db_url

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine_kwargs = {"echo": False, "future": True}

if is_postgres:
    # asyncpg expects ssl parameters via connect_args rather than query string arguments
    # Strip ?sslmode=... / ?channel_binding=... appended by Neon connection strings
    if "?" in db_url:
        base_part, query_part = db_url.split("?", 1)
        query_params = parse_qs(query_part)
        query_params.pop("sslmode", None)
        query_params.pop("channel_binding", None)
        # Rebuild if other query params exist, or use clean base
        db_url = base_part

    engine_kwargs["connect_args"] = {"ssl": "require"}
    engine_kwargs["pool_pre_ping"] = True  # Auto-reconnects on idle Neon/Render instances
    engine_kwargs["pool_recycle"] = 300

engine = create_async_engine(db_url, **engine_kwargs)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database tables asynchronously on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def reset_db() -> None:
    """Ensures tables match updated models by creating any missing tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper providing an active async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
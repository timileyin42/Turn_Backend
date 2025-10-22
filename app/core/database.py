"""
Database configuration and session management using SQLAlchemy 2.0+.
"""
from typing import AsyncGenerator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


# SQLAlchemy 2.0+ declarative base
class Base(DeclarativeBase):
    """Base class for all database models."""
    
    # Naming convention for constraints
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )


# Async engine for main application with enhanced connection pooling
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections after 5 minutes
    pool_size=10,      # Number of connections to maintain
    max_overflow=20,   # Additional connections allowed
    pool_timeout=30,   # Timeout for getting connection from pool
    connect_args={
        "connect_timeout": 10,
        "command_timeout": 30,
    }
)

# Sync engine for Alembic migrations with connection pooling
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,       # Smaller pool for sync operations
    max_overflow=10,
    pool_timeout=30,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Sync session factory (for migrations)
SessionLocal = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides async database sessions.
    
    Yields:
        AsyncSession: Database session for async operations
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for backwards compatibility
get_db = get_async_session


def get_sync_session():
    """
    Get synchronous database session (mainly for migrations).
    
    Returns:
        Session: Database session for sync operations
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        # Import all models to ensure they are registered
        # Import them inside the function to avoid circular imports
        import app.database.user_models
        import app.database.project_models
        import app.database.cv_models
        import app.database.job_models
        import app.database.portfolio_models
        import app.database.community_models
        import app.database.industry_models
        import app.database.platform_models
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.core.database import Base
from app.core.dependencies import get_db

# Test database URL (use a separate test database)
TEST_DATABASE_URL = settings.database_url.replace("/turn_db", "/turn_test_db")

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Create test database tables."""
    # Import all models to ensure they are registered
    from app.database import (
        user_models, project_models, cv_models, job_models,
        portfolio_models, community_models, industry_models
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Teardown
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden dependencies."""
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
        "location": "Test City",
        "date_of_birth": "1990-01-01",
        "gender": "male"
    }


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "title": "Test Project",
        "description": "This is a test project description",
        "status": "completed",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "budget": 50000.00,
        "team_size": 5,
        "technologies": ["Python", "FastAPI", "PostgreSQL"],
        "key_achievements": ["Delivered on time", "Under budget"],
        "client_name": "Test Client",
        "project_url": "https://example.com",
        "is_public": True
    }
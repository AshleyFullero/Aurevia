"""
Pytest configuration — shared fixtures for async test client and test DB.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.property import Property
from app.models.waitlist import WaitlistEntry  # noqa: F401 — ensure table is registered
from app.models.contact import ContactSubmission  # noqa: F401 — ensure table is registered

# ── In-memory SQLite database for tests ───────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Provide a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Provide an async HTTP test client with the test database injected."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_property(db_session: AsyncSession) -> Property:
    """Insert and return a single test property."""
    prop = Property(
        address="123 Test St",
        city="Austin",
        state="TX",
        zip_code="78704",
        bedrooms=2,
        bathrooms=2.0,
        square_feet=1200,
        property_type="apartment",
        list_price=900_000,
        price_per_sqft=750.0,
        fair_value_estimate=920_000,
        cap_rate=0.08,
        rental_yield=0.077,
        monthly_rent_estimate=6_000,
        five_year_appreciation=0.35,
        yoy_growth=0.065,
        risk_score=25,
        vacancy_rate=0.03,
        is_active=True,
        days_on_market=14,
    )
    db_session.add(prop)
    await db_session.commit()
    await db_session.refresh(prop)
    return prop


@pytest_asyncio.fixture
async def multiple_properties(db_session: AsyncSession) -> list[Property]:
    """Insert several test properties with varied attributes."""
    props = [
        Property(
            address=f"{i*100} Sample Ave",
            city="Austin" if i % 2 == 0 else "Miami",
            state="TX" if i % 2 == 0 else "FL",
            zip_code="78704",
            bedrooms=i % 4 + 1,
            bathrooms=float(i % 3 + 1),
            square_feet=800 + i * 200,
            property_type=["apartment", "condo", "townhouse"][i % 3],
            list_price=400_000 + i * 100_000,
            cap_rate=0.06 + i * 0.005,
            rental_yield=0.058 + i * 0.005,
            monthly_rent_estimate=2_500 + i * 500,
            yoy_growth=0.04 + i * 0.01,
            risk_score=20 + i * 5,
            vacancy_rate=0.03 + i * 0.005,
            is_active=True,
            days_on_market=i * 3,
        )
        for i in range(1, 7)
    ]
    for p in props:
        db_session.add(p)
    await db_session.commit()
    for p in props:
        await db_session.refresh(p)
    return props

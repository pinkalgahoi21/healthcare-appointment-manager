import uuid
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.auth.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_test_user(db_session: AsyncSession):
    async def _create(
        email: str,
        password: str = "Password123!",
        name: str = "Test User",
        role: UserRole = UserRole.PATIENT,
    ) -> User:
        user = User(
            name=name,
            email=email.lower().strip(),
            password_hash=hash_password(password),
            role=role.value if isinstance(role, UserRole) else role,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create


@pytest_asyncio.fixture
async def patient_auth(create_test_user):
    uid = uuid.uuid4().hex[:6]
    user = await create_test_user(email=f"patient_{uid}@example.com", role=UserRole.PATIENT)
    token = create_access_token(subject=user.id, role=user.role)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest_asyncio.fixture
async def doctor_auth(create_test_user):
    uid = uuid.uuid4().hex[:6]
    user = await create_test_user(email=f"doctor_{uid}@example.com", role=UserRole.DOCTOR)
    token = create_access_token(subject=user.id, role=user.role)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest_asyncio.fixture
async def admin_auth(create_test_user):
    uid = uuid.uuid4().hex[:6]
    user = await create_test_user(email=f"admin_{uid}@example.com", role=UserRole.ADMIN)
    token = create_access_token(subject=user.id, role=user.role)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

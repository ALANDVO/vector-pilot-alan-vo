import jwt as pyjwt
from datetime import datetime, timezone, timedelta
from jose import jwk

# Load RSA key for RS256 signing at module level
with open("/tmp/private_key.pem", "r") as f:
    _private_key_pem = f.read()
_private_jwk = jwk.construct(_private_key_pem, "RS256")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.app.main import create_app
from backend.app.core.database import Base, get_db, set_test_engine, init_db
from backend.app.models.evaluation import Evaluation, EvaluationRun, EvaluationMetric, EvaluationStatus
from backend.app.models.user import User, Role


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestAsyncSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Original client fixture (from before OIDC auth)
@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    set_test_engine(test_engine)
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    # Manually initialize database
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(db_session, test_user):
    """Create an authenticated test client using the provided test_user."""
    async def override_get_db():
        yield db_session

    set_test_engine(test_engine)
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    # Manually initialize database
    await init_db()

    import jwt as pyjwt
    from datetime import datetime, timezone, timedelta
    
    from backend.app.core.config import get_settings
    settings = get_settings()
    secret_key = settings.secret_key
    
    # Use the test_user's credentials for the token
    user = test_user
    
    # Token payload
    token_data = {
        "sub": user.keycloak_id,
        "email": user.email,
        "preferred_username": user.username,
        "realm_access": {
            "roles": [user.role.value]
        },
        "resource_access": {
            "vector-pilot": {
                "roles": [user.role.value]
            }
        },
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        "iss": "http://localhost:8080/realms/vector-pilot",
        "aud": "vector-pilot-alan-vo",
    }
    
    token = pyjwt.encode(token_data, secret_key, algorithm="HS256")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Authorization": f"Bearer {token}"}) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_auth_client(db_session, test_user):
    """Create an authenticated test client with admin role."""
    async def override_get_db():
        yield db_session

    set_test_engine(test_engine)
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    # Manually initialize database
    await init_db()

    import jwt as pyjwt
    from datetime import datetime, timezone, timedelta
    
    from backend.app.core.config import get_settings
    settings = get_settings()
    secret_key = settings.secret_key
    
    # Token payload with admin role
    token_data = {
        "sub": "admin-User",
        "email": "admin@example.com",
        "preferred_username": "admin",
        "realm_access": {
            "roles": ["admin"]
        },
        "resource_access": {
            "vector-pilot": {
                "roles": ["admin"]
            }
        },
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        "iss": "http://localhost:8080/realms/vector-pilot",
        "aud": "vector-pilot-alan-vo",
    }
    
    token = pyjwt.encode(token_data, secret_key, algorithm="HS256")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Authorization": f"Bearer {token}"}) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    user = User(
        keycloak_id="test-user-123",
        email="test@example.com",
        username="testuser",
        role=Role.ANALYST,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

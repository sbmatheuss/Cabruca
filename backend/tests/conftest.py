import uuid
from collections.abc import AsyncIterator

import boto3
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from moto import mock_aws
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_session
from app.core.config import settings
from app.db.session import engine
from app.main import app
from app.models.property import Property
from app.models.user import User
from app.models.user_property import UserProperty


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    # Sessão presa a uma transação externa via savepoint: session.commit() nas
    # rotas só fecha o savepoint, nunca a transação de fato — no fim do teste
    # ela é desfeita, sem sujar o Postgres de dev entre testes.
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,  # mesma config de app/db/session.py
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def test_user_id() -> uuid.UUID:
    # UUID novo a cada teste — não reaproveita DEV_USER_ID (app/core/dev_auth.py)
    # porque esse ID já existe na base de dev real (seed manual anterior) e
    # colidiria com o insert abaixo.
    return uuid.uuid4()


@pytest_asyncio.fixture
async def seeded_property(db_session: AsyncSession, test_user_id: uuid.UUID) -> Property:
    """User + Property associados, prontos para os testes de autorização."""
    # Sem relationship() entre User e Property, o flush não sabe ordenar pela
    # FK sozinho — insere o User primeiro, num flush à parte.
    db_session.add(User(id=test_user_id))
    await db_session.flush()

    property_ = Property(
        id=uuid.uuid4(),
        name="Fazenda de teste",
        property_code=f"T{uuid.uuid4().hex[:10]}",
        created_by=test_user_id,
    )
    db_session.add_all(
        [property_, UserProperty(user_id=test_user_id, property_id=property_.id)]
    )
    await db_session.flush()
    return property_


@pytest.fixture
def s3_bucket():
    with mock_aws():
        client = boto3.client("s3", region_name=settings.aws_region)
        client.create_bucket(Bucket=settings.s3_bucket_name)
        yield client


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, test_user_id: uuid.UUID
) -> AsyncIterator[AsyncClient]:
    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def _override_get_current_user_id() -> uuid.UUID:
        return test_user_id

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[get_current_user_id] = _override_get_current_user_id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

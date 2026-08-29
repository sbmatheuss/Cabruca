import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session as OrmSession

from worker.db import engine


@pytest.fixture
def db_session() -> Iterator[OrmSession]:
    # Mesmo padrão do backend/tests/conftest.py: sessão presa a uma transação
    # externa via savepoint — os commits de run_once só fecham o savepoint,
    # nunca a transação de fato, então nada suja o Postgres de dev entre testes.
    with engine.connect() as connection:
        transaction = connection.begin()
        session = OrmSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def queued_image(db_session: OrmSession) -> uuid.UUID:
    """Insere user + property + image (status=queued) via SQL cru.

    users/properties não fazem parte de worker/models.py (só as colunas que o
    worker lê/escreve, ver REVISAR nesse arquivo), mas images.property_id e
    images.uploaded_by são FKs NOT NULL de verdade no schema — precisam de
    linhas reais pra o INSERT não violar a constraint.
    """
    user_id = uuid.uuid4()
    property_id = uuid.uuid4()
    image_id = uuid.uuid4()
    db_session.execute(text("INSERT INTO users (id) VALUES (:id)"), {"id": user_id})
    db_session.execute(
        text(
            "INSERT INTO properties (id, name, property_code, created_by) "
            "VALUES (:id, 'Fazenda de teste', :code, :created_by)"
        ),
        {"id": property_id, "code": f"T{uuid.uuid4().hex[:10]}", "created_by": user_id},
    )
    db_session.execute(
        text(
            "INSERT INTO images (id, property_id, uploaded_by, object_key, status) "
            "VALUES (:id, :property_id, :uploaded_by, 'test/object.jpg', 'queued')"
        ),
        {"id": image_id, "property_id": property_id, "uploaded_by": user_id},
    )
    db_session.commit()
    return image_id

from sqlalchemy import create_engine, inspect

from worker.config import settings
from worker.models import Base


def test_worker_schema_matches_database() -> None:
    """Falha se uma coluna que o worker depende (worker/models.py) sumir da
    tabela real — sinal de que uma migration no backend/ mudou o schema sem
    que este worker fosse atualizado (ver REVISAR em worker/models.py).
    Não detecta colunas novas que o worker ainda não usa, nem mudança de
    tipo — só protege contra remoção/renomeio do que o worker já depende.
    Requer um Postgres real migrado (mesmo `docker compose` do backend/),
    igual aos testes de backend/tests/conftest.py.
    """
    engine = create_engine(settings.database_url)
    try:
        inspector = inspect(engine)
        for table in Base.metadata.sorted_tables:
            real_columns = {col["name"] for col in inspector.get_columns(table.name)}
            expected_columns = {col.name for col in table.columns}
            missing = expected_columns - real_columns
            assert not missing, (
                f"Colunas esperadas pelo worker sumiram de '{table.name}': "
                f"{missing}. Atualize worker/models.py (ver REVISAR)."
            )
    finally:
        engine.dispose()

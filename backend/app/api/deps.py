import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DEV_USER_ID
from app.db.session import async_session


# REVISAR: deveria extrair o header Authorization: Bearer <JWT>, validar a
# assinatura/expiração contra o JWKS do Cognito (ADR 0007) e retornar o claim
# `sub`. Por ora retorna sempre o usuário fixo de dev (app/core/dev_auth.py,
# populado por scripts/seed_dev.py) até o User Pool do Cognito existir.
async def get_current_user_id() -> uuid.UUID:
    return DEV_USER_ID


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

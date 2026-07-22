import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dev_auth import DEV_USER_ID
from app.db.session import async_session


# Stub deliberado até o Cognito existir (ver app/core/dev_auth.py e ADR 0007).
# Quando o User Pool existir, isto passa a extrair o header
# Authorization: Bearer <JWT>, validar assinatura/expiração contra o JWKS do
# Cognito e retornar o claim `sub`.
async def get_current_user_id() -> uuid.UUID:
    return DEV_USER_ID


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

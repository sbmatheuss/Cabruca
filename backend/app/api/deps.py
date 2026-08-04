import asyncio
import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cognito_auth import InvalidTokenError, get_user_id_from_token
from app.db.session import async_session
from app.models.user import User

_bearer_scheme = HTTPBearer()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> uuid.UUID:
    try:
        user_id = await asyncio.to_thread(get_user_id_from_token, credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Lazy-create (ADR 0007): a primeira chamada de um `sub` novo do Cognito
    # cria a linha em `users` aqui mesmo. ON CONFLICT DO NOTHING em vez de
    # SELECT-depois-INSERT evita condição de corrida entre requests
    # concorrentes do mesmo usuário novo, sem precisar de lock explícito.
    stmt = insert(User).values(id=user_id).on_conflict_do_nothing(index_elements=["id"])
    await session.execute(stmt)
    await session.commit()

    return user_id

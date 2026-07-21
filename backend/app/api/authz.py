import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from app.models.user_property import UserProperty


async def ensure_property_access(
    session: AsyncSession, property_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Levanta 404 se a propriedade não existe, 403 se existe mas o usuário
    não está associado a ela — semântica exigida por POST /images
    (docs/api/contrato-endpoints.md). Não usar como está para os endpoints
    GET/DELETE /images/{image_id}: lá o contrato pede 404 para os dois casos,
    para não vazar a existência da propriedade a quem não tem acesso.
    """
    if await session.get(Property, property_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Propriedade não encontrada")

    if await session.get(UserProperty, (user_id, property_id)) is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Usuário não associado a esta propriedade"
        )

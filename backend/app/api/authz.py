import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
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


async def get_accessible_image(
    session: AsyncSession, image_id: uuid.UUID, user_id: uuid.UUID
) -> Image:
    """Busca a Image e garante acesso do usuário via propriedade. Levanta 404
    tanto se a imagem não existe quanto se existe mas o usuário não está
    associado à propriedade dela — semântica exigida por GET/DELETE/confirm
    de /images (docs/api/contrato-endpoints.md), ao contrário de
    ensure_property_access (usada só em POST /images).
    """
    image = await session.get(Image, image_id)
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")

    if await session.get(UserProperty, (user_id, image.property_id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada")

    return image


async def ensure_property_membership(
    session: AsyncSession, property_id: uuid.UUID, user_id: uuid.UUID
) -> Property:
    """Busca a Property e garante que o usuário está associado a ela. Levanta
    404 tanto se a propriedade não existe quanto se existe mas o usuário não
    está associado — semântica de "Autorização por propriedade"
    (docs/api/contrato-endpoints.md), usada por GET /properties/{id}/members
    e outros endpoints de leitura de propriedade. Diferente de
    ensure_property_access (que usa 403 para "existe mas sem acesso",
    semântica exigida só em POST /images).
    """
    property_ = await session.get(Property, property_id)
    if property_ is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Propriedade não encontrada")

    if await session.get(UserProperty, (user_id, property_id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Propriedade não encontrada")

    return property_

import secrets
import string
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import ensure_property_membership
from app.api.deps import get_current_user_id, get_session
from app.models.property import Property
from app.models.user_property import UserProperty

router = APIRouter(prefix="/properties", tags=["properties"])

# REVISAR: alfabeto sem 0/O/1/I para reduzir ambiguidade ao compartilhar o
# código verbalmente em campo — decisão confirmada com o usuário.
_PROPERTY_CODE_ALPHABET = "".join(
    c for c in string.ascii_uppercase + string.digits if c not in "01OI"
)
_PROPERTY_CODE_LENGTH = 8
_PROPERTY_CODE_MAX_ATTEMPTS = 5


async def _generate_unique_property_code(session: AsyncSession) -> str:
    for _ in range(_PROPERTY_CODE_MAX_ATTEMPTS):
        code = "".join(
            secrets.choice(_PROPERTY_CODE_ALPHABET) for _ in range(_PROPERTY_CODE_LENGTH)
        )
        collision = await session.scalar(
            select(Property.id).where(Property.property_code == code)
        )
        if collision is None:
            return code
    raise RuntimeError("Não foi possível gerar property_code único")


class PropertyLocation(BaseModel):
    lat: float
    lng: float


class PropertyCreateRequest(BaseModel):
    name: str
    location: PropertyLocation | None = None


class PropertyCreateResponse(BaseModel):
    property_id: uuid.UUID
    name: str
    property_code: str
    created_at: datetime


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PropertyCreateResponse)
async def create_property(
    body: PropertyCreateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PropertyCreateResponse:
    property_code = await _generate_unique_property_code(session)

    property_ = Property(
        id=uuid.uuid4(),
        name=body.name,
        location_lat=body.location.lat if body.location else None,
        location_lng=body.location.lng if body.location else None,
        property_code=property_code,
        created_by=user_id,
    )
    session.add(property_)
    await session.flush()
    session.add(UserProperty(user_id=user_id, property_id=property_.id))
    await session.commit()

    return PropertyCreateResponse(
        property_id=property_.id,
        name=property_.name,
        property_code=property_.property_code,
        created_at=property_.created_at,
    )


class PropertyJoinRequest(BaseModel):
    property_code: str


class PropertyJoinResponse(BaseModel):
    property_id: uuid.UUID
    name: str


@router.post("/join", response_model=PropertyJoinResponse)
async def join_property(
    body: PropertyJoinRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PropertyJoinResponse:
    property_ = await session.scalar(
        select(Property).where(Property.property_code == body.property_code)
    )
    if property_ is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Código não corresponde a nenhuma propriedade"
        )

    # REVISAR: contrato não define o comportamento se o usuário já estiver
    # associado — tratado como idempotente (sem erro) em vez de rejeitar.
    already_associated = await session.get(UserProperty, (user_id, property_.id))
    if already_associated is None:
        session.add(UserProperty(user_id=user_id, property_id=property_.id))
        await session.commit()

    return PropertyJoinResponse(property_id=property_.id, name=property_.name)


class PropertyListItem(BaseModel):
    property_id: uuid.UUID
    name: str
    is_creator: bool


class PropertyListResponse(BaseModel):
    items: list[PropertyListItem]


@router.get("", response_model=PropertyListResponse)
async def list_properties(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PropertyListResponse:
    result = await session.execute(
        select(Property)
        .join(UserProperty, UserProperty.property_id == Property.id)
        .where(UserProperty.user_id == user_id)
        .order_by(Property.created_at)
    )
    items = [
        PropertyListItem(property_id=p.id, name=p.name, is_creator=p.created_by == user_id)
        for p in result.scalars().all()
    ]
    return PropertyListResponse(items=items)


class PropertyMemberItem(BaseModel):
    user_id: uuid.UUID
    is_creator: bool
    associated_at: datetime


class PropertyMemberListResponse(BaseModel):
    items: list[PropertyMemberItem]


@router.get("/{property_id}/members", response_model=PropertyMemberListResponse)
async def list_property_members(
    property_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PropertyMemberListResponse:
    property_ = await ensure_property_membership(session, property_id, user_id)

    result = await session.execute(
        select(UserProperty)
        .where(UserProperty.property_id == property_id)
        .order_by(UserProperty.associated_at)
    )
    items = [
        PropertyMemberItem(
            user_id=member.user_id,
            is_creator=member.user_id == property_.created_by,
            associated_at=member.associated_at,
        )
        for member in result.scalars().all()
    ]
    return PropertyMemberListResponse(items=items)


class PropertyTransferRequest(BaseModel):
    new_owner_user_id: uuid.UUID


class PropertyTransferResponse(BaseModel):
    property_id: uuid.UUID
    created_by: uuid.UUID


@router.post("/{property_id}/transfer", response_model=PropertyTransferResponse)
async def transfer_property(
    property_id: uuid.UUID,
    body: PropertyTransferRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PropertyTransferResponse:
    property_ = await session.get(Property, property_id)
    if property_ is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Propriedade não encontrada")

    if property_.created_by != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Usuário não é o criador desta propriedade"
        )

    new_owner_membership = await session.get(
        UserProperty, (body.new_owner_user_id, property_id)
    )
    if new_owner_membership is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Novo dono informado não está associado a esta propriedade",
        )

    property_.created_by = body.new_owner_user_id
    await session.commit()

    return PropertyTransferResponse(property_id=property_.id, created_by=property_.created_by)


@router.delete("/{property_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_property_member(
    property_id: uuid.UUID,
    user_id: uuid.UUID,
    caller_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    property_ = await session.get(Property, property_id)
    if property_ is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Propriedade não encontrada")

    membership = await session.get(UserProperty, (user_id, property_id))
    if membership is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Usuário não associado a esta propriedade"
        )

    is_creator_caller = caller_id == property_.created_by
    is_self_removal = caller_id == user_id
    if not is_creator_caller and not is_self_removal:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Sem permissão para remover esta associação"
        )

    if user_id == property_.created_by:
        other_members = await session.scalar(
            select(func.count())
            .select_from(UserProperty)
            .where(UserProperty.property_id == property_id, UserProperty.user_id != user_id)
        )
        if other_members:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Transfira a posse da propriedade antes de sair",
            )

    await session.delete(membership)
    await session.commit()

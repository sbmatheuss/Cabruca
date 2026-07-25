import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import ensure_property_access, get_accessible_image
from app.api.deps import get_current_user_id, get_session
from app.core.config import settings
from app.core.s3 import build_object_key, generate_upload_url, object_exists
from app.models.image import Image, ImageStatus

router = APIRouter(prefix="/images", tags=["images"])


class ImageCreateRequest(BaseModel):
    property_id: uuid.UUID
    content_type: str

    @field_validator("content_type")
    @classmethod
    def content_type_must_be_image(cls, value: str) -> str:
        if not value.startswith("image/"):
            raise ValueError("content_type deve começar com 'image/'")
        return value


class ImageCreateResponse(BaseModel):
    image_id: uuid.UUID
    upload_url: str
    expires_at: datetime
    status: str


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ImageCreateResponse)
async def create_image(
    body: ImageCreateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ImageCreateResponse:
    await ensure_property_access(session, body.property_id, user_id)

    image_id = uuid.uuid4()
    object_key = build_object_key(body.property_id, image_id)

    image = Image(
        id=image_id,
        property_id=body.property_id,
        uploaded_by=user_id,
        object_key=object_key,
    )
    session.add(image)
    await session.commit()

    upload_url, expires_at = generate_upload_url(object_key, body.content_type)

    return ImageCreateResponse(
        image_id=image_id,
        upload_url=upload_url,
        expires_at=expires_at,
        status=image.status.value,
    )


class ImageConfirmResponse(BaseModel):
    image_id: uuid.UUID
    status: str


@router.post("/{image_id}/confirm", response_model=ImageConfirmResponse)
async def confirm_image(
    image_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ImageConfirmResponse:
    image = await get_accessible_image(session, image_id, user_id)

    if image.status != ImageStatus.PENDING_UPLOAD:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Imagem já confirmada")

    # REVISAR: expires_at não é persistido no model Image (ver ADR/contrato).
    # Recalculado a partir de created_at + config, assumindo que a URL
    # pré-assinada é sempre gerada no mesmo instante da criação do registro
    # (verdade hoje, em POST /images) — decisão confirmada com o usuário.
    expires_at = image.created_at + timedelta(
        seconds=settings.s3_presigned_url_expiration_seconds
    )
    if datetime.now(UTC) > expires_at:
        raise HTTPException(status.HTTP_410_GONE, detail="URL pré-assinada expirou")

    if not object_exists(image.object_key):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Upload não encontrado no bucket")

    image.status = ImageStatus.QUEUED
    await session.commit()

    return ImageConfirmResponse(image_id=image.id, status=image.status.value)

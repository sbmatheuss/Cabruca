import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import ensure_property_access, get_accessible_image
from app.api.deps import get_current_user_id, get_session
from app.core.config import settings
from app.core.s3 import (
    build_object_key,
    delete_object,
    generate_upload_url,
    object_exists,
)
from app.models.detection import Detection
from app.models.image import Image, ImageStatus
from app.models.user_property import UserProperty

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

    # object_exists faz uma chamada de rede síncrona (boto3 não é async) — sem
    # to_thread, ela bloquearia o event loop inteiro enquanto está em
    # andamento, serializando todas as requisições concorrentes do processo.
    # REVISAR: se mais chamadas de rede ao S3 forem adicionadas no futuro,
    # reconsiderar migrar para aiobotocore em vez de espalhar to_thread.
    if not await asyncio.to_thread(object_exists, image.object_key):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Upload não encontrado no bucket")

    image.status = ImageStatus.QUEUED
    await session.commit()

    return ImageConfirmResponse(image_id=image.id, status=image.status.value)


class ImageDetectionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_name: str = Field(alias="class")
    bbox: list[float]
    confidence: float


class ImageStatusResponse(BaseModel):
    image_id: uuid.UUID
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    model_version: str | None = None
    detections: list[ImageDetectionItem] | None = None


@router.get("/{image_id}", response_model=ImageStatusResponse, response_model_exclude_none=True)
async def get_image(
    image_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ImageStatusResponse:
    image = await get_accessible_image(session, image_id, user_id)

    detections = None
    if image.status == ImageStatus.DONE:
        result = await session.execute(select(Detection).where(Detection.image_id == image.id))
        detections = [
            ImageDetectionItem(
                class_name=d.class_name,
                bbox=[d.bbox_x, d.bbox_y, d.bbox_width, d.bbox_height],
                confidence=d.confidence,
            )
            for d in result.scalars().all()
        ]

    return ImageStatusResponse(
        image_id=image.id,
        status=image.status.value,
        created_at=image.created_at,
        completed_at=image.completed_at,
        model_version=image.model_version,
        detections=detections,
    )


class ImageListItem(BaseModel):
    image_id: uuid.UUID
    status: str
    created_at: datetime


class ImageListResponse(BaseModel):
    items: list[ImageListItem]
    page: int
    page_size: int
    total: int


@router.get("", response_model=ImageListResponse)
async def list_images(
    status_filter: ImageStatus | None = Query(None, alias="status"),
    since: datetime | None = None,
    until: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ImageListResponse:
    base_query = (
        select(Image)
        .join(UserProperty, UserProperty.property_id == Image.property_id)
        .where(UserProperty.user_id == user_id)
    )
    if status_filter is not None:
        base_query = base_query.where(Image.status == status_filter)
    if since is not None:
        base_query = base_query.where(Image.created_at >= since)
    if until is not None:
        base_query = base_query.where(Image.created_at <= until)

    total = await session.scalar(select(func.count()).select_from(base_query.subquery()))

    result = await session.execute(
        base_query.order_by(Image.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        ImageListItem(image_id=img.id, status=img.status.value, created_at=img.created_at)
        for img in result.scalars().all()
    ]

    return ImageListResponse(items=items, page=page, page_size=page_size, total=total or 0)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    image = await get_accessible_image(session, image_id, user_id)

    # Apaga o objeto no S3 antes de apagar o registro no banco: se o commit
    # falhar depois, sobra um registro órfão (ruim, mas não viola a LGPD); na
    # ordem inversa, uma falha no S3 deixaria a imagem em si intacta mesmo com
    # o registro já "excluído".
    await asyncio.to_thread(delete_object, image.object_key)

    await session.delete(image)
    await session.commit()

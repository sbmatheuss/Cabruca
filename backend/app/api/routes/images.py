import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import ensure_property_access
from app.api.deps import get_current_user_id, get_session
from app.core.s3 import build_object_key, generate_upload_url
from app.models.image import Image

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

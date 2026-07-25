import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.image import Image, ImageStatus
from app.models.property import Property
from app.models.user import User


async def test_create_image_returns_upload_url(
    client: AsyncClient, seeded_property: Property, s3_bucket
):
    response = await client.post(
        "/images",
        json={"property_id": str(seeded_property.id), "content_type": "image/jpeg"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == ImageStatus.PENDING_UPLOAD.value
    assert body["upload_url"].startswith("https://")
    uuid.UUID(body["image_id"])  # não levanta se for um UUID válido


async def test_create_image_property_not_associated_returns_403(
    client: AsyncClient, db_session: AsyncSession
):
    other_owner_id = uuid.uuid4()
    db_session.add(User(id=other_owner_id))
    await db_session.flush()

    other_property = Property(
        id=uuid.uuid4(),
        name="Fazenda de outro dono",
        property_code=f"T{uuid.uuid4().hex[:10]}",
        created_by=other_owner_id,
    )
    db_session.add(other_property)
    await db_session.flush()

    response = await client.post(
        "/images",
        json={"property_id": str(other_property.id), "content_type": "image/jpeg"},
    )

    assert response.status_code == 403


async def test_create_image_property_not_found_returns_404(client: AsyncClient):
    response = await client.post(
        "/images",
        json={"property_id": str(uuid.uuid4()), "content_type": "image/jpeg"},
    )

    assert response.status_code == 404


async def test_create_image_invalid_content_type_returns_422(
    client: AsyncClient, seeded_property: Property
):
    response = await client.post(
        "/images",
        json={"property_id": str(seeded_property.id), "content_type": "application/pdf"},
    )

    assert response.status_code == 422


async def test_confirm_image_happy_path(
    client: AsyncClient, seeded_property: Property, s3_bucket
):
    create_response = await client.post(
        "/images",
        json={"property_id": str(seeded_property.id), "content_type": "image/jpeg"},
    )
    image_id = create_response.json()["image_id"]
    object_key = f"{seeded_property.id}/{image_id}"
    s3_bucket.put_object(Bucket=settings.s3_bucket_name, Key=object_key, Body=b"fake")

    response = await client.post(f"/images/{image_id}/confirm")

    assert response.status_code == 200
    assert response.json()["status"] == ImageStatus.QUEUED.value


async def test_confirm_image_without_upload_returns_409(
    client: AsyncClient, seeded_property: Property, s3_bucket
):
    create_response = await client.post(
        "/images",
        json={"property_id": str(seeded_property.id), "content_type": "image/jpeg"},
    )
    image_id = create_response.json()["image_id"]

    response = await client.post(f"/images/{image_id}/confirm")

    assert response.status_code == 409


async def test_confirm_image_already_confirmed_returns_409(
    client: AsyncClient, seeded_property: Property, s3_bucket
):
    create_response = await client.post(
        "/images",
        json={"property_id": str(seeded_property.id), "content_type": "image/jpeg"},
    )
    image_id = create_response.json()["image_id"]
    object_key = f"{seeded_property.id}/{image_id}"
    s3_bucket.put_object(Bucket=settings.s3_bucket_name, Key=object_key, Body=b"fake")

    first = await client.post(f"/images/{image_id}/confirm")
    assert first.status_code == 200

    second = await client.post(f"/images/{image_id}/confirm")
    assert second.status_code == 409


async def test_confirm_image_expired_url_returns_410(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_property: Property,
    test_user_id: uuid.UUID,
):
    expired_created_at = datetime.now(UTC) - timedelta(
        seconds=settings.s3_presigned_url_expiration_seconds + 60
    )
    image = Image(
        id=uuid.uuid4(),
        property_id=seeded_property.id,
        uploaded_by=test_user_id,
        object_key="irrelevante-para-este-teste",
        created_at=expired_created_at,
    )
    db_session.add(image)
    await db_session.flush()

    response = await client.post(f"/images/{image.id}/confirm")

    assert response.status_code == 410

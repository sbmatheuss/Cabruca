import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.detection import Detection
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


async def test_get_image_processing_status_omits_detections(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_property: Property,
    test_user_id: uuid.UUID,
):
    image = Image(
        id=uuid.uuid4(),
        property_id=seeded_property.id,
        uploaded_by=test_user_id,
        object_key="irrelevante-para-este-teste",
        status=ImageStatus.PROCESSING,
    )
    db_session.add(image)
    await db_session.flush()

    response = await client.get(f"/images/{image.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ImageStatus.PROCESSING.value
    assert "detections" not in body
    assert "completed_at" not in body


async def test_get_image_done_status_includes_detections(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_property: Property,
    test_user_id: uuid.UUID,
):
    completed_at = datetime.now(UTC)
    image = Image(
        id=uuid.uuid4(),
        property_id=seeded_property.id,
        uploaded_by=test_user_id,
        object_key="irrelevante-para-este-teste",
        status=ImageStatus.DONE,
        model_version="v0.1.0",
        completed_at=completed_at,
    )
    db_session.add(image)
    await db_session.flush()
    db_session.add(
        Detection(
            image_id=image.id,
            class_name="monilíase",
            bbox_x=0.1,
            bbox_y=0.2,
            bbox_width=0.3,
            bbox_height=0.4,
            confidence=0.87,
        )
    )
    await db_session.flush()

    response = await client.get(f"/images/{image.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ImageStatus.DONE.value
    assert body["model_version"] == "v0.1.0"
    assert len(body["detections"]) == 1
    detection = body["detections"][0]
    assert detection["class"] == "monilíase"
    assert detection["bbox"] == [0.1, 0.2, 0.3, 0.4]
    assert detection["confidence"] == 0.87


async def test_get_image_not_found_returns_404(client: AsyncClient):
    response = await client.get(f"/images/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_image_not_associated_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    other_owner_id = uuid.uuid4()
    db_session.add(User(id=other_owner_id))
    await db_session.flush()
    other_property = Property(
        id=uuid.uuid4(),
        name="Fazenda de outro dono",
        property_code=f"G{uuid.uuid4().hex[:7].upper()}",
        created_by=other_owner_id,
    )
    db_session.add(other_property)
    await db_session.flush()
    image = Image(
        id=uuid.uuid4(),
        property_id=other_property.id,
        uploaded_by=other_owner_id,
        object_key="irrelevante-para-este-teste",
    )
    db_session.add(image)
    await db_session.flush()

    response = await client.get(f"/images/{image.id}")

    assert response.status_code == 404


async def test_list_images_only_from_associated_properties(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_property: Property,
    test_user_id: uuid.UUID,
):
    visible_image = Image(
        id=uuid.uuid4(),
        property_id=seeded_property.id,
        uploaded_by=test_user_id,
        object_key="visivel",
    )
    other_owner_id = uuid.uuid4()
    db_session.add(User(id=other_owner_id))
    await db_session.flush()
    other_property = Property(
        id=uuid.uuid4(),
        name="Fazenda de outro dono",
        property_code=f"H{uuid.uuid4().hex[:7].upper()}",
        created_by=other_owner_id,
    )
    db_session.add(other_property)
    await db_session.flush()

    hidden_image = Image(
        id=uuid.uuid4(),
        property_id=other_property.id,
        uploaded_by=other_owner_id,
        object_key="oculta",
    )
    db_session.add_all([visible_image, hidden_image])
    await db_session.flush()

    response = await client.get("/images")

    assert response.status_code == 200
    body = response.json()
    image_ids = {item["image_id"] for item in body["items"]}
    assert str(visible_image.id) in image_ids
    assert str(hidden_image.id) not in image_ids
    assert body["total"] == 1


async def test_list_images_filters_by_status(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_property: Property,
    test_user_id: uuid.UUID,
):
    pending_image = Image(
        id=uuid.uuid4(),
        property_id=seeded_property.id,
        uploaded_by=test_user_id,
        object_key="pendente",
        status=ImageStatus.PENDING_UPLOAD,
    )
    done_image = Image(
        id=uuid.uuid4(),
        property_id=seeded_property.id,
        uploaded_by=test_user_id,
        object_key="concluida",
        status=ImageStatus.DONE,
    )
    db_session.add_all([pending_image, done_image])
    await db_session.flush()

    response = await client.get("/images", params={"status": ImageStatus.DONE.value})

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["image_id"] == str(done_image.id)


async def test_list_images_paginates(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_property: Property,
    test_user_id: uuid.UUID,
):
    for i in range(3):
        db_session.add(
            Image(
                id=uuid.uuid4(),
                property_id=seeded_property.id,
                uploaded_by=test_user_id,
                object_key=f"imagem-{i}",
            )
        )
    await db_session.flush()

    response = await client.get("/images", params={"page": 1, "page_size": 2})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] == 3


async def test_delete_image_removes_record_and_s3_object(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_property: Property,
    test_user_id: uuid.UUID,
    s3_bucket,
):
    object_key = f"{seeded_property.id}/{uuid.uuid4()}"
    s3_bucket.put_object(Bucket=settings.s3_bucket_name, Key=object_key, Body=b"fake")
    image = Image(
        id=uuid.uuid4(),
        property_id=seeded_property.id,
        uploaded_by=test_user_id,
        object_key=object_key,
    )
    db_session.add(image)
    await db_session.flush()

    response = await client.delete(f"/images/{image.id}")

    assert response.status_code == 204
    assert await db_session.get(Image, image.id) is None
    remaining = s3_bucket.list_objects_v2(Bucket=settings.s3_bucket_name).get("Contents", [])
    assert object_key not in [obj["Key"] for obj in remaining]


async def test_delete_image_not_found_returns_404(client: AsyncClient):
    response = await client.delete(f"/images/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_delete_image_not_associated_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    other_owner_id = uuid.uuid4()
    db_session.add(User(id=other_owner_id))
    await db_session.flush()
    other_property = Property(
        id=uuid.uuid4(),
        name="Fazenda de outro dono",
        property_code=f"D{uuid.uuid4().hex[:7].upper()}",
        created_by=other_owner_id,
    )
    db_session.add(other_property)
    await db_session.flush()
    image = Image(
        id=uuid.uuid4(),
        property_id=other_property.id,
        uploaded_by=other_owner_id,
        object_key="irrelevante-para-este-teste",
    )
    db_session.add(image)
    await db_session.flush()

    response = await client.delete(f"/images/{image.id}")

    assert response.status_code == 404

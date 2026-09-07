import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.properties import _PROPERTY_CODE_ALPHABET
from app.models.property import Property
from app.models.user import User
from app.models.user_property import UserProperty


async def test_create_property_returns_code_and_associates_creator(
    client: AsyncClient, db_session: AsyncSession, test_user_id: uuid.UUID
):
    response = await client.post(
        "/properties",
        json={"name": "Fazenda Boa Esperança", "location": {"lat": -14.235, "lng": -39.021}},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Fazenda Boa Esperança"
    assert len(body["property_code"]) == 8
    assert all(c in _PROPERTY_CODE_ALPHABET for c in body["property_code"])

    association = await db_session.get(
        UserProperty, (test_user_id, uuid.UUID(body["property_id"]))
    )
    assert association is not None


async def test_create_property_without_location(client: AsyncClient):
    response = await client.post("/properties", json={"name": "Sítio sem coordenadas"})

    assert response.status_code == 201


async def test_join_property_associates_user(
    client: AsyncClient, db_session: AsyncSession, test_user_id: uuid.UUID
):
    other_owner_id = uuid.uuid4()
    db_session.add(User(id=other_owner_id))
    await db_session.flush()

    other_property = Property(
        id=uuid.uuid4(),
        name="Fazenda de outro dono",
        property_code=f"J{uuid.uuid4().hex[:7].upper()}",
        created_by=other_owner_id,
    )
    db_session.add(other_property)
    await db_session.flush()

    response = await client.post(
        "/properties/join", json={"property_code": other_property.property_code}
    )

    assert response.status_code == 200
    assert response.json()["property_id"] == str(other_property.id)

    association = await db_session.get(UserProperty, (test_user_id, other_property.id))
    assert association is not None


async def test_join_property_invalid_code_returns_404(client: AsyncClient):
    response = await client.post("/properties/join", json={"property_code": "NAOEXIST"})

    assert response.status_code == 404


async def test_join_property_already_associated_is_idempotent(
    client: AsyncClient, seeded_property: Property
):
    response = await client.post(
        "/properties/join", json={"property_code": seeded_property.property_code}
    )

    assert response.status_code == 200
    assert response.json()["property_id"] == str(seeded_property.id)


async def test_list_properties_returns_associated_with_is_creator(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user_id: uuid.UUID,
    seeded_property: Property,
):
    other_owner_id = uuid.uuid4()
    db_session.add(User(id=other_owner_id))
    await db_session.flush()

    joined_property = Property(
        id=uuid.uuid4(),
        name="Propriedade compartilhada",
        property_code=f"L{uuid.uuid4().hex[:7].upper()}",
        created_by=other_owner_id,
    )
    not_associated_property = Property(
        id=uuid.uuid4(),
        name="Propriedade não associada",
        property_code=f"N{uuid.uuid4().hex[:7].upper()}",
        created_by=other_owner_id,
    )
    db_session.add_all([joined_property, not_associated_property])
    await db_session.flush()
    db_session.add(UserProperty(user_id=test_user_id, property_id=joined_property.id))
    await db_session.flush()

    response = await client.get("/properties")

    assert response.status_code == 200
    is_creator_by_id = {
        item["property_id"]: item["is_creator"] for item in response.json()["items"]
    }
    assert is_creator_by_id[str(seeded_property.id)] is True
    assert is_creator_by_id[str(joined_property.id)] is False
    assert str(not_associated_property.id) not in is_creator_by_id


async def test_list_property_members_returns_all_associated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user_id: uuid.UUID,
    seeded_property: Property,
):
    other_user_id = uuid.uuid4()
    db_session.add(User(id=other_user_id))
    await db_session.flush()
    db_session.add(UserProperty(user_id=other_user_id, property_id=seeded_property.id))
    await db_session.flush()

    response = await client.get(f"/properties/{seeded_property.id}/members")

    assert response.status_code == 200
    is_creator_by_id = {item["user_id"]: item["is_creator"] for item in response.json()["items"]}
    assert is_creator_by_id[str(test_user_id)] is True
    assert is_creator_by_id[str(other_user_id)] is False


async def test_list_property_members_not_associated_returns_404(
    client: AsyncClient, db_session: AsyncSession
):
    other_owner_id = uuid.uuid4()
    db_session.add(User(id=other_owner_id))
    await db_session.flush()
    other_property = Property(
        id=uuid.uuid4(),
        name="Fazenda de outro dono",
        property_code=f"M{uuid.uuid4().hex[:7].upper()}",
        created_by=other_owner_id,
    )
    db_session.add(other_property)
    await db_session.flush()

    response = await client.get(f"/properties/{other_property.id}/members")

    assert response.status_code == 404


async def test_list_property_members_nonexistent_property_returns_404(client: AsyncClient):
    response = await client.get(f"/properties/{uuid.uuid4()}/members")

    assert response.status_code == 404


async def test_transfer_property_by_creator_succeeds(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_property: Property,
):
    new_owner_id = uuid.uuid4()
    db_session.add(User(id=new_owner_id))
    await db_session.flush()
    db_session.add(UserProperty(user_id=new_owner_id, property_id=seeded_property.id))
    await db_session.flush()

    response = await client.post(
        f"/properties/{seeded_property.id}/transfer",
        json={"new_owner_user_id": str(new_owner_id)},
    )

    assert response.status_code == 200
    assert response.json()["created_by"] == str(new_owner_id)


async def test_transfer_property_by_non_creator_returns_403(
    client: AsyncClient, db_session: AsyncSession, test_user_id: uuid.UUID
):
    creator_id = uuid.uuid4()
    db_session.add(User(id=creator_id))
    await db_session.flush()
    property_ = Property(
        id=uuid.uuid4(),
        name="Fazenda de outro dono",
        property_code=f"T{uuid.uuid4().hex[:7].upper()}",
        created_by=creator_id,
    )
    db_session.add_all(
        [property_, UserProperty(user_id=test_user_id, property_id=property_.id)]
    )
    await db_session.flush()

    response = await client.post(
        f"/properties/{property_.id}/transfer",
        json={"new_owner_user_id": str(test_user_id)},
    )

    assert response.status_code == 403


async def test_transfer_property_new_owner_not_associated_returns_404(
    client: AsyncClient, seeded_property: Property
):
    response = await client.post(
        f"/properties/{seeded_property.id}/transfer",
        json={"new_owner_user_id": str(uuid.uuid4())},
    )

    assert response.status_code == 404


async def test_remove_member_self_removal_succeeds(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user_id: uuid.UUID,
    seeded_property: Property,
):
    other_user_id = uuid.uuid4()
    db_session.add(User(id=other_user_id))
    await db_session.flush()
    db_session.add(UserProperty(user_id=other_user_id, property_id=seeded_property.id))
    await db_session.flush()

    response = await client.delete(
        f"/properties/{seeded_property.id}/members/{other_user_id}"
    )

    assert response.status_code == 204


async def test_remove_member_creator_cannot_leave_with_other_members_returns_409(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user_id: uuid.UUID,
    seeded_property: Property,
):
    other_user_id = uuid.uuid4()
    db_session.add(User(id=other_user_id))
    await db_session.flush()
    db_session.add(UserProperty(user_id=other_user_id, property_id=seeded_property.id))
    await db_session.flush()

    response = await client.delete(
        f"/properties/{seeded_property.id}/members/{test_user_id}"
    )

    assert response.status_code == 409


async def test_remove_member_creator_sole_member_can_leave(
    client: AsyncClient, test_user_id: uuid.UUID, seeded_property: Property
):
    response = await client.delete(
        f"/properties/{seeded_property.id}/members/{test_user_id}"
    )

    assert response.status_code == 204


async def test_remove_member_non_creator_removing_third_party_returns_403(
    client: AsyncClient, db_session: AsyncSession, test_user_id: uuid.UUID
):
    creator_id = uuid.uuid4()
    third_party_id = uuid.uuid4()
    db_session.add_all([User(id=creator_id), User(id=third_party_id)])
    await db_session.flush()
    property_ = Property(
        id=uuid.uuid4(),
        name="Fazenda com dono diferente",
        property_code=f"R{uuid.uuid4().hex[:7].upper()}",
        created_by=creator_id,
    )
    db_session.add_all(
        [
            property_,
            UserProperty(user_id=test_user_id, property_id=property_.id),
            UserProperty(user_id=creator_id, property_id=property_.id),
            UserProperty(user_id=third_party_id, property_id=property_.id),
        ]
    )
    await db_session.flush()

    response = await client.delete(f"/properties/{property_.id}/members/{third_party_id}")

    assert response.status_code == 403


async def test_create_property_retrain_consent_defaults_to_false(client: AsyncClient):
    response = await client.post("/properties", json={"name": "Fazenda nova"})

    assert response.status_code == 201
    assert response.json()["retrain_consent"] is False


async def test_set_retrain_consent_by_creator_succeeds(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user_id: uuid.UUID,
    seeded_property: Property,
):
    response = await client.patch(
        f"/properties/{seeded_property.id}/retrain-consent",
        json={"retrain_consent": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["property_id"] == str(seeded_property.id)
    assert body["retrain_consent"] is True

    await db_session.refresh(seeded_property)
    assert seeded_property.retrain_consent is True
    assert seeded_property.retrain_consent_updated_at is not None
    assert seeded_property.retrain_consent_updated_by == test_user_id


async def test_set_retrain_consent_by_non_creator_returns_403(
    client: AsyncClient, db_session: AsyncSession, test_user_id: uuid.UUID
):
    other_owner_id = uuid.uuid4()
    db_session.add(User(id=other_owner_id))
    await db_session.flush()
    property_ = Property(
        id=uuid.uuid4(),
        name="Fazenda de outro dono",
        property_code=f"C{uuid.uuid4().hex[:7].upper()}",
        created_by=other_owner_id,
    )
    db_session.add_all(
        [property_, UserProperty(user_id=test_user_id, property_id=property_.id)]
    )
    await db_session.flush()

    response = await client.patch(
        f"/properties/{property_.id}/retrain-consent", json={"retrain_consent": True}
    )

    assert response.status_code == 403


async def test_set_retrain_consent_nonexistent_property_returns_404(client: AsyncClient):
    response = await client.patch(
        f"/properties/{uuid.uuid4()}/retrain-consent", json={"retrain_consent": True}
    )

    assert response.status_code == 404

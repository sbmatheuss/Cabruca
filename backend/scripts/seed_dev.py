"""Seed de dados de teste para desenvolvimento local.

REVISAR: existe só enquanto get_current_user_id (app/api/deps.py) retorna um
usuário fixo em vez de validar JWT do Cognito. Apagar este script quando a
autenticação real for implementada.

Uso: poetry run python scripts/seed_dev.py
"""

import asyncio

from app.core.dev_auth import DEV_PROPERTY_ID, DEV_USER_ID
from app.db.session import async_session
from app.models.property import Property
from app.models.user import User
from app.models.user_property import UserProperty


async def seed() -> None:
    async with async_session() as session:
        if await session.get(User, DEV_USER_ID) is None:
            session.add(User(id=DEV_USER_ID))

        if await session.get(Property, DEV_PROPERTY_ID) is None:
            session.add(
                Property(
                    id=DEV_PROPERTY_ID,
                    name="Fazenda de teste (dev)",
                    property_code="DEVTEST1",
                    created_by=DEV_USER_ID,
                )
            )

        if await session.get(UserProperty, (DEV_USER_ID, DEV_PROPERTY_ID)) is None:
            session.add(UserProperty(user_id=DEV_USER_ID, property_id=DEV_PROPERTY_ID))

        await session.commit()

    print(f"Seed ok: user={DEV_USER_ID} property={DEV_PROPERTY_ID}")


if __name__ == "__main__":
    asyncio.run(seed())

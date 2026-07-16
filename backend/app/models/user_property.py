import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


# REVISAR: TimestampMixin gera a coluna `created_at`, mas a ADR 0008 e o contrato de
# endpoints (docs/api/contrato-endpoints.md) já usam o nome `associated_at` para este
# campo na resposta de "listar membros" — confirmar se é para renomear a coluna ou
# mapear created_at -> associated_at na serialização.
class UserProperty(Base, TimestampMixin):
    __tablename__ = "user_properties"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id"), primary_key=True
    )

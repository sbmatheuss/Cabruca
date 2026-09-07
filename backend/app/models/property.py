import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, false
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Property(Base, TimestampMixin):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    location_lat: Mapped[float | None]
    location_lng: Mapped[float | None]
    property_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    # Consentimento para uso das imagens desta propriedade em retrain do
    # modelo (LGPD) — ver ADR 0015. Default false (opt-in): nenhuma
    # propriedade autoriza retrain até o criador consentir explicitamente;
    # server_default cobre retroativamente as propriedades já existentes.
    retrain_consent: Mapped[bool] = mapped_column(Boolean, server_default=false())
    # Nulos até a primeira alteração explícita — o estado padrão não tem
    # "quem"/"quando", só mudanças reais têm (ver ADR 0015).
    retrain_consent_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    retrain_consent_updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ImageStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    # REVISAR: omite PENDING_UPLOAD de proposito — existe no schema real
    # (backend/app/models/image.py) mas o worker nunca filtra nem escreve esse
    # valor. Seguro enquanto o worker so selecionar linhas com status="queued".


# REVISAR: duplicacao deliberada do schema de backend/app/models/image.py e
# detection.py (decisao do usuario: sem pacote compartilhado entre backend/ e
# este worker, ADR 0005). So as colunas que o worker le/escreve estao aqui —
# se o schema real mudar, este arquivo precisa ser atualizado manualmente.
class Image(Base):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    object_key: Mapped[str] = mapped_column(String(512))
    status: Mapped[ImageStatus] = mapped_column(
        ENUM(
            ImageStatus,
            name="image_status",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
    )
    model_version: Mapped[str | None] = mapped_column(String(32))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE")
    )
    class_name: Mapped[str] = mapped_column(String(64))
    bbox_x: Mapped[float]
    bbox_y: Mapped[float]
    bbox_width: Mapped[float]
    bbox_height: Mapped[float]
    confidence: Mapped[float]

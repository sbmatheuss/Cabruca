import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ImageStatus(str, enum.Enum):
    PENDING_UPLOAD = "pending_upload"
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id")
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    object_key: Mapped[str] = mapped_column(String(512))
    # create_type=False: o tipo "image_status" é criado/dropado só pela migration
    # (fonte de verdade do schema); sem isso, um futuro create_all() colidiria.
    # values_callable: sem isso o SQLAlchemy manda o NOME do membro Python
    # ("PENDING_UPLOAD") em vez do .value ("pending_upload"), que é o que o
    # tipo ENUM do Postgres (criado pela migration) realmente aceita.
    status: Mapped[ImageStatus] = mapped_column(
        ENUM(
            ImageStatus,
            name="image_status",
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ImageStatus.PENDING_UPLOAD,
    )
    model_version: Mapped[str | None] = mapped_column(String(32))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

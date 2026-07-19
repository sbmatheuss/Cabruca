import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# Sem TimestampMixin: todas as detecções de uma imagem são gravadas juntas no
# momento em que a inferência termina, timestamp já coberto por images.completed_at.
# Reavaliar se reprocessamento (nova versão de modelo sobre imagem já processada)
# virar requisito real — nesse caso isso deve virar uma ADR própria.
class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE")
    )
    class_name: Mapped[str] = mapped_column(String(64))
    # Coordenadas normalizadas 0-1 (convenção YOLO), não pixels absolutos —
    # ver ADR 0009. Pipeline de inferência é responsável por normalizar antes
    # de persistir, independente da resolução em que a inferência rodou.
    bbox_x: Mapped[float]
    bbox_y: Mapped[float]
    bbox_width: Mapped[float]
    bbox_height: Mapped[float]
    confidence: Mapped[float]

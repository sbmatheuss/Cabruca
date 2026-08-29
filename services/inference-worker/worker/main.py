import logging
import time
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from worker.config import settings
from worker.db import Session as SessionLocal
from worker.inference import STUB_MODEL_VERSION, infer
from worker.models import Detection, Image, ImageStatus

logger = logging.getLogger(__name__)


def run_once(session: OrmSession) -> bool:
    """Processa uma imagem da fila, se houver. Retorna True se processou algo."""
    image = session.execute(
        select(Image)
        .where(Image.status == ImageStatus.QUEUED)
        .order_by(Image.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    ).scalar_one_or_none()

    if image is None:
        return False

    image.status = ImageStatus.PROCESSING
    session.commit()

    try:
        results = infer(image.object_key)
    except Exception:
        logger.exception("Falha ao processar imagem %s", image.id)
        image.status = ImageStatus.FAILED
        session.commit()
        return True

    for result in results:
        session.add(
            Detection(
                image_id=image.id,
                class_name=result.class_name,
                bbox_x=result.bbox_x,
                bbox_y=result.bbox_y,
                bbox_width=result.bbox_width,
                bbox_height=result.bbox_height,
                confidence=result.confidence,
            )
        )

    image.status = ImageStatus.DONE
    image.model_version = STUB_MODEL_VERSION
    image.completed_at = datetime.now(UTC)
    session.commit()
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info(
        "Worker de inferência iniciado (poll a cada %ss)", settings.poll_interval_seconds
    )
    while True:
        # REVISAR: erro em run_once já é tratado internamente (marca FAILED e
        # segue) — decisão do usuário de não travar o loop por causa de uma
        # imagem problemática. Uma exceção que escapar daqui (ex.: banco fora
        # do ar) ainda derruba o processo; a expectativa é reinício via
        # orquestrador (systemd/docker restart), não retry manual no loop.
        with SessionLocal() as session:
            processed = run_once(session)
        if not processed:
            time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from worker import inference
from worker.main import run_once
from worker.models import Detection, Image, ImageStatus


def test_run_once_returns_false_when_queue_empty(db_session: OrmSession) -> None:
    assert run_once(db_session) is False


def test_run_once_processes_queued_image(
    db_session: OrmSession, queued_image: uuid.UUID
) -> None:
    processed = run_once(db_session)

    assert processed is True
    image = db_session.get(Image, queued_image)
    assert image.status == ImageStatus.DONE
    assert image.model_version == inference.STUB_MODEL_VERSION
    assert image.completed_at is not None

    detections = (
        db_session.execute(select(Detection).where(Detection.image_id == queued_image))
        .scalars()
        .all()
    )
    assert detections == []  # stub nunca inventa deteccao


def test_run_once_marks_failed_on_infer_error(
    db_session: OrmSession, queued_image: uuid.UUID, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(object_key: str) -> list:
        raise RuntimeError("modelo indisponivel")

    monkeypatch.setattr("worker.main.infer", _boom)

    processed = run_once(db_session)

    assert processed is True
    image = db_session.get(Image, queued_image)
    assert image.status == ImageStatus.FAILED

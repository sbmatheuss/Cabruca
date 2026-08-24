from detectron2.data import MetadataCatalog
from detectron2.data.datasets import register_coco_instances

from config import (
    CLASSES,
    DATASET_IMAGES_DIR,
    TRAIN_ANNOTATIONS_JSON,
    VAL_ANNOTATIONS_JSON,
)

TRAIN_DATASET_NAME = "cabruca_train"
VAL_DATASET_NAME = "cabruca_val"


def register_datasets() -> None:
    """Registra os datasets COCO de treino/validacao no catalogo do
    Detectron2 (ADR 0013), sem etapa de conversao de formato.

    REVISAR: assume que TRAIN_ANNOTATIONS_JSON/VAL_ANNOTATIONS_JSON (ver
    config.py) existem de verdade -- hoje nao existem, so ha
    dataset/annotations/placeholder.json (nao confiavel para treino, ver
    dataset/PLACEHOLDER_SOURCES.md). Chamar esta funcao antes de haver export
    real do CVAT vai falhar com arquivo nao encontrado -- comportamento
    correto: falhar alto, nunca fingir que ha dado de treino real.
    """
    register_coco_instances(
        TRAIN_DATASET_NAME, {}, str(TRAIN_ANNOTATIONS_JSON), str(DATASET_IMAGES_DIR)
    )
    register_coco_instances(
        VAL_DATASET_NAME, {}, str(VAL_ANNOTATIONS_JSON), str(DATASET_IMAGES_DIR)
    )

    for name in (TRAIN_DATASET_NAME, VAL_DATASET_NAME):
        MetadataCatalog.get(name).thing_classes = CLASSES

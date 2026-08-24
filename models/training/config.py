from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DATASET_IMAGES_DIR = REPO_ROOT / "dataset" / "images"
DATASET_ANNOTATIONS_DIR = REPO_ROOT / "dataset" / "annotations"
# Pesos treinados saem em models/output/, nao em models/training/output/ --
# models/ e a pasta versionada via DVC (ver models/README.md), training/ e so
# codigo-fonte.
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

# Taxonomia fechada do MVP (ADR 0011) -- a ordem da lista define o id usado
# pelo schema COCO (vassoura-de-bruxa=0, podridao-parda=1, moniliase=2).
CLASSES = ["vassoura-de-bruxa", "podridao-parda", "moniliase"]

# REVISAR: nomes de arquivo de split (train/val) sao um chute de convencao --
# ainda nao existe export real do CVAT dividido em splits. Hoje so ha
# dataset/annotations/placeholder.json, que NAO deve ser usado para treino de
# verdade (5 fotos de teste, bboxes chutadas sem revisao humana -- ver
# dataset/PLACEHOLDER_SOURCES.md). Ajustar estes caminhos quando houver
# export real anotado no CVAT (ADR 0012).
TRAIN_ANNOTATIONS_JSON = DATASET_ANNOTATIONS_DIR / "train.json"
VAL_ANNOTATIONS_JSON = DATASET_ANNOTATIONS_DIR / "val.json"

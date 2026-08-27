"""Divide um export COCO do CVAT (dataset/annotations/<export>.json) em
train.json/val.json, os nomes que models/training/config.py espera.

Split é por imagem, não por annotation: uma imagem inteira (com todas as suas
lesões anotadas) vai pro treino ou pra validação, nunca as duas -- senão o
modelo veria a mesma foto nos dois splits. Random simples com seed fixa, sem
estratificação por classe (dataset ainda pequeno demais pra isso valer a
pena -- REVISAR se as classes ficarem desbalanceadas com mais volume).

Não valida schema/bbox -- rode dataset/scripts/validate_dataset.py depois,
ele varre todo *.json em annotations/ automaticamente.
"""

import argparse
import json
import random
from pathlib import Path


def split_coco(data: dict, train_ratio: float, seed: int) -> tuple[dict, dict]:
    images = data["images"]
    annotations = data["annotations"]
    categories = data["categories"]

    image_ids = [img["id"] for img in images]
    rng = random.Random(seed)
    rng.shuffle(image_ids)

    split_point = round(len(image_ids) * train_ratio)
    train_ids = set(image_ids[:split_point])
    val_ids = set(image_ids[split_point:])

    def build_split(ids: set) -> dict:
        return {
            "images": [img for img in images if img["id"] in ids],
            "annotations": [ann for ann in annotations if ann["image_id"] in ids],
            "categories": categories,
        }

    return build_split(train_ids), build_split(val_ids)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="COCO JSON exportado do CVAT")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "annotations"
    )
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    train_data, val_data = split_coco(data, args.train_ratio, args.seed)

    train_path = args.output_dir / "train.json"
    val_path = args.output_dir / "val.json"
    train_path.write_text(json.dumps(train_data, ensure_ascii=False, indent=2), encoding="utf-8")
    val_path.write_text(json.dumps(val_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{train_path}: {len(train_data['images'])} imagens, {len(train_data['annotations'])} annotations")
    print(f"{val_path}: {len(val_data['images'])} imagens, {len(val_data['annotations'])} annotations")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

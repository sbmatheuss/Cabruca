"""Valida arquivos de anotação COCO em dataset/annotations/ contra o schema
e a taxonomia de classes fechados na ADR 0011. Só biblioteca padrão --
bbox é conferido contra width/height já presentes no próprio JSON, sem
precisar abrir os arquivos de imagem.
"""

import json
from pathlib import Path

# Taxonomia fechada na ADR 0011 (docs/adr/0011-formato-anotacao-dataset.md).
# Mudar esta lista exige atualizar a ADR, não só o script.
EXPECTED_CATEGORIES = [
    {"id": 0, "name": "vassoura-de-bruxa"},
    {"id": 1, "name": "podridao-parda"},
    {"id": 2, "name": "moniliase"},
]


def load_coco_json(path: Path) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{path}: JSON inválido ({exc})"]

    if not isinstance(data, dict):
        return None, [f"{path}: raiz do JSON deveria ser um objeto"]

    for key in ("images", "annotations", "categories"):
        if key not in data:
            errors.append(f"{path}: chave obrigatória '{key}' ausente")
        elif not isinstance(data[key], list):
            errors.append(f"{path}: '{key}' deveria ser uma lista")

    return data, errors


def validate_categories(data: dict, path: Path) -> list[str]:
    errors: list[str] = []
    categories = data.get("categories")
    if not isinstance(categories, list):
        return errors  # já reportado por load_coco_json

    expected_by_id = {c["id"]: c["name"] for c in EXPECTED_CATEGORIES}
    found_by_id = {c.get("id"): c.get("name") for c in categories if isinstance(c, dict)}

    if found_by_id != expected_by_id:
        errors.append(
            f"{path}: 'categories' não bate com a taxonomia da ADR 0011. "
            f"Esperado {expected_by_id}, encontrado {found_by_id}"
        )

    return errors


def validate_bboxes(data: dict, path: Path) -> list[str]:
    errors: list[str] = []
    images = data.get("images")
    annotations = data.get("annotations")
    categories = data.get("categories")
    if not isinstance(images, list) or not isinstance(annotations, list) or not isinstance(categories, list):
        return errors  # já reportado por load_coco_json

    images_by_id = {img.get("id"): img for img in images if isinstance(img, dict)}
    category_ids = {c.get("id") for c in categories if isinstance(c, dict)}

    for ann in annotations:
        if not isinstance(ann, dict):
            errors.append(f"{path}: item de 'annotations' não é um objeto: {ann!r}")
            continue

        image = images_by_id.get(ann.get("image_id"))
        if image is None:
            errors.append(f"{path}: annotation {ann.get('id')} referencia image_id inexistente ({ann.get('image_id')})")
            continue

        if ann.get("category_id") not in category_ids:
            errors.append(f"{path}: annotation {ann.get('id')} tem category_id inválido ({ann.get('category_id')})")

        bbox = ann.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(v, (int, float)) for v in bbox)):
            errors.append(f"{path}: annotation {ann.get('id')} tem bbox inválido (esperado [x, y, w, h] numérico): {bbox!r}")
            continue

        x, y, w, h = bbox
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            errors.append(f"{path}: annotation {ann.get('id')} tem bbox fora do domínio (x,y >= 0, w,h > 0): {bbox!r}")

        img_w, img_h = image.get("width"), image.get("height")
        if isinstance(img_w, (int, float)) and isinstance(img_h, (int, float)) and (x + w > img_w or y + h > img_h):
            errors.append(
                f"{path}: annotation {ann.get('id')} bbox {bbox!r} estoura os limites da imagem "
                f"{image.get('file_name')} ({img_w}x{img_h})"
            )

    return errors


def validate_images_exist(data: dict, path: Path, images_dir: Path) -> list[str]:
    errors: list[str] = []
    images = data.get("images")
    if not isinstance(images, list):
        return errors  # já reportado por load_coco_json

    for img in images:
        if not isinstance(img, dict):
            continue
        file_name = img.get("file_name")
        if not file_name or not (images_dir / file_name).is_file():
            errors.append(f"{path}: imagem referenciada não existe em {images_dir}: {file_name!r}")

    return errors


def main() -> int:
    dataset_dir = Path(__file__).resolve().parent.parent
    annotations_dir = dataset_dir / "annotations"
    images_dir = dataset_dir / "images"

    json_files = sorted(annotations_dir.glob("*.json"))
    if not json_files:
        print(f"Nenhum arquivo de anotação encontrado em {annotations_dir} (esperado nesta fase do projeto).")
        return 0

    all_errors: list[str] = []
    for path in json_files:
        data, errors = load_coco_json(path)
        all_errors.extend(errors)
        if data is None:
            continue
        all_errors.extend(validate_categories(data, path))
        all_errors.extend(validate_bboxes(data, path))
        all_errors.extend(validate_images_exist(data, path, images_dir))

    if all_errors:
        print(f"{len(all_errors)} erro(s) encontrado(s):")
        for error in all_errors:
            print(f"  - {error}")
        return 1

    print(f"OK: {len(json_files)} arquivo(s) de anotação validado(s) sem erros.")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

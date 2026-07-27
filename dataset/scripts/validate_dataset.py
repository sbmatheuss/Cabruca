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

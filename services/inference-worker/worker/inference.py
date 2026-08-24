from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionResult:
    class_name: str
    # Normalizado 0-1 (convencao YOLO), nao pixels absolutos — ver ADR 0009.
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    confidence: float


# Versao do "modelo" usada para rotular as deteccoes gravadas por este stub.
# Nao e uma versao real de modelo treinado (nao existe nenhum ainda).
STUB_MODEL_VERSION = "stub-v0"


def infer(object_key: str) -> list[DetectionResult]:
    """Ponto de integracao do modelo real de deteccao.

    # REVISAR: stub deliberado — nao ha modelo treinado ainda (dataset vazio,
    # ver ADR 0013). Sempre retorna lista vazia (zero deteccoes), nunca
    # inventa classe/bbox/confianca fake. Quando houver um modelo Detectron2
    # treinado (ADR 0013), trocar o corpo desta funcao para: baixar a imagem
    # do S3 via `object_key`, rodar a inferencia, normalizar bbox 0-1 (ADR
    # 0009) e retornar a lista real de DetectionResult.
    """
    return []

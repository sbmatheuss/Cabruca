import uuid
from datetime import datetime, timedelta, timezone

import boto3

from app.core.config import settings

_s3_client = boto3.client("s3", region_name=settings.aws_region)


def build_object_key(property_id: uuid.UUID, image_id: uuid.UUID) -> str:
    # REVISAR: formato de object_key não é coberto por nenhuma ADR. Proposta:
    # agrupar por propriedade e por imagem, sem depender de nome de arquivo
    # enviado pelo cliente (evita colisão/path traversal).
    return f"{property_id}/{image_id}"


def generate_upload_url(object_key: str, content_type: str) -> tuple[str, datetime]:
    expires_in = settings.s3_presigned_url_expiration_seconds
    url = _s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.s3_bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    return url, expires_at

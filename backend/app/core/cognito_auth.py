import uuid

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError, PyJWTError

from app.core.config import settings


class InvalidTokenError(Exception):
    """Token ausente, malformado, expirado ou não emitido para este app client."""


_ISSUER = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}"
_JWKS_URL = f"{_ISSUER}/.well-known/jwks.json"

# PyJWKClient só busca/cacheia o JWKS na primeira chamada a
# get_signing_key_from_jwt — instanciar aqui não faz request de rede.
_jwks_client = PyJWKClient(_JWKS_URL)


def get_user_id_from_token(token: str) -> uuid.UUID:
    """Valida um access token do Cognito e retorna o claim `sub` como UUID.

    A busca da chave de assinatura (PyJWKClient) é uma chamada de rede
    síncrona — quem chamar isto a partir de uma rota async deve envolver em
    asyncio.to_thread (mesmo padrão já usado para as chamadas S3 síncronas
    em app/api/routes/images.py).
    """
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=_ISSUER,
            # Access token do Cognito não tem claim `aud` (só o id token tem)
            # — a audiência é validada abaixo via `client_id`. Exigir
            # `token_use`/`client_id` aqui já rejeita de cara um id_token
            # passado por engano, antes das checagens manuais.
            options={"require": ["exp", "iss", "sub", "token_use", "client_id"]},
        )
    except (PyJWTError, PyJWKClientError) as exc:
        raise InvalidTokenError(str(exc)) from exc

    if payload["token_use"] != "access":
        raise InvalidTokenError("Token não é um access token")
    if payload["client_id"] != settings.cognito_app_client_id:
        raise InvalidTokenError("Token emitido para outro app client")

    try:
        return uuid.UUID(payload["sub"])
    except ValueError as exc:
        raise InvalidTokenError("Claim sub não é um UUID válido") from exc

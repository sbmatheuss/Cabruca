from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    aws_region: str
    s3_bucket_name: str
    # 15 min: curto o bastante pra segurança, longo o bastante pra tolerar
    # rede rural instável (ADR 0006 deixou o valor em aberto; confirmado
    # com o usuário em 2026-07-21).
    s3_presigned_url_expiration_seconds: int = 900

    # User Pool e App Client do Cognito (ADR 0007). Região é a mesma de
    # aws_region — alinhadas de propósito com o bucket de imagens.
    cognito_user_pool_id: str
    cognito_app_client_id: str


settings = Settings()

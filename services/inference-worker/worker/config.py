from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    # Worker de polling simples (ADR 0005) — sem infra de fila dedicada.
    # 5s é um chute inicial razoável para o volume de MVP; revisar se a
    # latência entre "queued" e o worker pegar o item virar perceptível.
    poll_interval_seconds: float = 5.0


settings = Settings()

"""Configurações lidas do arquivo .env (senhas e chaves ficam fora do código)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 120
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"
    timezone: str = "America/Sao_Paulo"
    # Caminho do certificado (CA) do banco na nuvem. Deixe vazio para o MySQL local.
    db_ssl_ca: str | None = None

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
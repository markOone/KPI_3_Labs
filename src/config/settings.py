from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env")

    BASE_DIR: Path = Path(__file__).parent.parent

    DB_SCHEME: str = "postgresql+asyncpg"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"{self.DB_SCHEME}://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = BaseAppSettings()

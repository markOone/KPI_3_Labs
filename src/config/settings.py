from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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


class AuthSettings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int


class AppSettings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db: DatabaseSettings = DatabaseSettings()
    auth: AuthSettings = AuthSettings()


settings = AppSettings()

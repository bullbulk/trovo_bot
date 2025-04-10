import dotenv
from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, AnyUrl, field_validator, model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv.load_dotenv()


class Settings(BaseSettings):
    SECRET_KEY: str = Field(alias="SECRET_KEY")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    SERVER_NAME: str = "localhost"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8080"
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = ("http://localhost:5173", "https://g1deon.bullbulk.ru")

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:  # noqa
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "app"

    DB_SERVER: str = Field(alias="DB_SERVER")
    DB_USER: str = Field(alias="DB_USER")
    DB_PASSWORD: str = Field(alias="DB_PASSWORD")
    DB_NAME: str = Field(alias="DB_NAME")
    DATABASE_URI: str | None = Field(alias="DATABASE_URI")

    @model_validator(mode="before")
    def assemble_db_connection(cls, v):  # noqa
        if v.get("DATABASE_URI"):
            return
        v["DATABASE_URI"] = str(
            PostgresDsn.build(
                scheme="postgresql",
                username=v.get("DB_USER"),
                password=v.get("DB_PASSWORD"),
                host=v.get("DB_SERVER"),
                path=f"{v.get('DB_NAME') or ''}",
            )
        )
        return v

    SMTP_TLS: bool = True
    SMTP_PORT: int | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    @field_validator("EMAILS_FROM_NAME")
    def get_project_name(cls, v: str | None, info) -> str:  # noqa
        return v or info.data.get("PROJECT_NAME")

    EMAIL_TEST_USER: EmailStr = Field(alias="EMAIL_TEST_USER")
    FIRST_SUPERUSER: EmailStr = Field(alias="FIRST_SUPERUSER")
    FIRST_SUPERUSER_PASSWORD: str = Field(alias="FIRST_SUPERUSER_PASSWORD")
    USERS_OPEN_REGISTRATION: bool = False

    TROVO_API_HOST: AnyHttpUrl = "https://open-api.trovo.live/openplatform"
    TROVO_WEBSOCKET_HOST: AnyUrl = "wss://open-chat.trovo.live/chat"
    TROVO_CLIENT_ID: str = Field(alias="TROVO_CLIENT_ID")
    TROVO_CLIENT_SECRET: str = Field(alias="TROVO_CLIENT_SECRET")
    TROVO_OWNER_ID: int = Field(alias="TROVO_OWNER_ID")

    OLLAMA_HOST_URL: AnyUrl = Field(alias="OLLAMA_HOST_URL")
    OLLAMA_MODEL_NAME: str = Field(alias="OLLAMA_MODEL_NAME")


settings = Settings()

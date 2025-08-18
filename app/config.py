from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    EVENT_URL: str = Field('', description="Default event URL to watch")
    EVENT_URLS: str = Field('', description="Comma-separated list of event URLs")
    POLL_SECONDS: int = Field(60, description="Background poll interval in seconds")
    CONCURRENCY: int = Field(4, description="Max concurrent HTTP requests")
    JSON_DIR: str = Field('./json', description="Directory for JSON outputs (must remain ./json)")
    TIMEZONE: str = Field('America/New_York', description="Local timezone for daily run")
    DAILY_RUN: bool = Field(True, description="Enable daily full refresh + snapshot")
    DAILY_RUN_AT: str = Field('09:00', description="Daily run time HH:MM 24h")
    SNAPSHOT_DIR: str = Field('./json/snapshots', description="Directory to store daily snapshots")

    # New storage policy settings
    WRITE_POLICY: str = Field('replace', description="Write policy: replace | snapshot | both")
    SNAPSHOT_ENABLE: bool = Field(False, description="Hard disable snapshots by default")
    SNAPSHOT_RETENTION_DAYS: int = Field(7, description="Days to keep snapshots (only if enabled)")

    # pydantic v2 settings config
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()

def configured_event_urls() -> list[str]:
    urls = []
    if settings.EVENT_URLS:
        urls = [u.strip() for u in settings.EVENT_URLS.split(',') if u.strip()]
    if not urls and settings.EVENT_URL:
        urls = [settings.EVENT_URL]
    return urls

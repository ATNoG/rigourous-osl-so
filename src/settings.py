from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openslice_host: str = "10.255.32.80"
    so_host: str = "155.54.95.79:8002"
    log_level: str = "INFO"

settings = Settings()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openslice_host: str = "10.255.32.80"
    log_level: str = "DEBUG"

settings = Settings()

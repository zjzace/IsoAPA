import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "IsoAPA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    DATABASE_URL: str = "sqlite:///" + os.path.join(os.path.dirname(os.path.dirname(__file__)), "isoapa.db")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

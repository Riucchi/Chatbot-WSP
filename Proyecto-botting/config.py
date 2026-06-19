from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Base de Datos
    database_url: str
    
    # Meta/WhatsApp
    meta_access_token: str
    meta_phone_number_id: str
    meta_business_account_id: str
    webhook_verify_token: str

    # SMTP
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_from: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60

    # Servidor
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

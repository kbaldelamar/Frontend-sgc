"""
Configuración de la aplicación frontend FastAPI
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Configuración básica de la aplicación
    APP_NAME: str = "Sistema de Gestión"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Configuración del servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # URLs de las APIs
    AUTH_API_URL: str = os.getenv("AUTH_API_URL", "http://localhost:9000")
    DATA_API_URL: str = os.getenv("DATA_API_URL", "http://localhost:8000")
    
    # Configuración de seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    
    # Configuración de sesiones
    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = not DEBUG  # HTTPS en producción
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", "86400"))  # 24 horas
    
    # Configuración de CORS
    CORS_ORIGINS: List[str] = []
    
    @property 
    def cors_origins_list(self) -> List[str]:
        origins_str = os.getenv("CORS_ORIGINS", "")
        if not origins_str:
            return ["*"] if self.DEBUG else []
        return [origin.strip() for origin in origins_str.split(",")]
    
    # Hosts permitidos
    ALLOWED_HOSTS: List[str] = []
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        hosts_str = os.getenv("ALLOWED_HOSTS", "")
        if not hosts_str:
            return ["*"] if self.DEBUG else ["localhost", "127.0.0.1"]
        return [host.strip() for host in hosts_str.split(",")]
    
    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Configuración de cache
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hora
    
    # Rutas públicas (no requieren autenticación)
    PUBLIC_PATHS: List[str] = [
        "/",
        "/login",
        "/register",
        "/forgot-password",
        "/reset-password",
        "/health",
        "/favicon.ico"
    ]
    
    # Configuración de rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # segundos
    
    # Configuración de uploads
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "application/pdf"]
    
    # Configuración de timeouts
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))  # segundos
    
    # Configuración de paginación
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    # Configuración de features
    ENABLE_REGISTRATION: bool = os.getenv("ENABLE_REGISTRATION", "True").lower() == "true"
    ENABLE_PASSWORD_RESET: bool = os.getenv("ENABLE_PASSWORD_RESET", "True").lower() == "true"
    ENABLE_ADMIN_PANEL: bool = os.getenv("ENABLE_ADMIN_PANEL", "True").lower() == "true"
    
    # Configuración de roles
    ADMIN_ROLES: List[str] = ["admin", "superuser"]
    USER_ROLES: List[str] = ["user", "member"]
    
    # Configuración de notificaciones
    SHOW_SUCCESS_MESSAGES: bool = True
    SHOW_ERROR_MESSAGES: bool = True
    MESSAGE_TIMEOUT: int = 5000  # milisegundos
    
    # Configuración de UI
    THEME: str = os.getenv("THEME", "light")  # light, dark, auto
    SIDEBAR_COLLAPSED: bool = os.getenv("SIDEBAR_COLLAPSED", "False").lower() == "true"
    
    # URLs externas
    DOCUMENTATION_URL: Optional[str] = os.getenv("DOCUMENTATION_URL")
    SUPPORT_URL: Optional[str] = os.getenv("SUPPORT_URL")
    TERMS_URL: Optional[str] = os.getenv("TERMS_URL")
    PRIVACY_URL: Optional[str] = os.getenv("PRIVACY_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Configurar CORS_ORIGINS después de la inicialización
        self.CORS_ORIGINS = self.cors_origins_list
        self.ALLOWED_HOSTS = self.allowed_hosts_list

# Instancia global de configuración
settings = Settings()
"""
Middleware de sesiones para FastAPI
"""
from fastapi import Request
from starlette.middleware.sessions import SessionMiddleware as BaseSessionMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send
from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime, timedelta

from config.settings import settings

logger = logging.getLogger(__name__)

class CustomSessionMiddleware(BaseSessionMiddleware):
    """
    Middleware personalizado de sesiones que extiende el de Starlette
    """
    
    def __init__(
        self,
        app: ASGIApp,
        secret_key: str,
        session_cookie: str = None,
        max_age: int = None,
        path: str = "/",
        same_site: str = "lax",
        https_only: bool = None,
        domain: str = None
    ):
        """
        Inicializa el middleware de sesiones
        
        Args:
            app: Aplicación ASGI
            secret_key: Clave secreta para firmar cookies
            session_cookie: Nombre de la cookie de sesión
            max_age: Tiempo de vida máximo de la sesión
            path: Path de la cookie
            same_site: Política SameSite
            https_only: Solo HTTPS
            domain: Dominio de la cookie
        """
        # Usar configuración por defecto si no se proporciona
        session_cookie = session_cookie or settings.SESSION_COOKIE_NAME
        max_age = max_age or settings.SESSION_MAX_AGE
        https_only = https_only if https_only is not None else settings.SESSION_COOKIE_SECURE
        same_site = same_site or settings.SESSION_COOKIE_SAMESITE
        
        # El middleware base de Starlette no acepta 'domain'
        super().__init__(
            app=app,
            secret_key=secret_key,
            session_cookie=session_cookie,
            max_age=max_age,
            path=path,
            same_site=same_site,
            https_only=https_only
        )
        
        logger.info(f"CustomSessionMiddleware configurado: cookie={session_cookie}, max_age={max_age}s")
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Procesa cada request añadiendo funcionalidades de sesión personalizadas
        
        Args:
            scope: Información del ámbito de la solicitud
            receive: Canal para recibir mensajes
            send: Canal para enviar mensajes
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Procesar con el middleware base
        await super().__call__(scope, receive, send)
        
        # Aquí puedes añadir lógica adicional si es necesaria

class EnhancedSessionManager:
    """
    Administrador de sesiones mejorado con funcionalidades adicionales
    """
    
    @staticmethod
    def create_session_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea los datos iniciales de sesión
        
        Args:
            user_data: Datos del usuario autenticado
            
        Returns:
            Dict[str, Any]: Datos de sesión estructurados
        """
        now = datetime.now()
        
        session_data = {
            # Información de autenticación
            "authenticated": True,
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "user_roles": user_data.get("roles", []),
            
            # Tokens
            "access_token": user_data.get("access_token"),
            "refresh_token": user_data.get("refresh_token"),
            "token_type": user_data.get("token_type", "bearer"),
            
            # Timestamps
            "login_time": now.isoformat(),
            "last_activity": now.isoformat(),
            
            # Configuración de usuario
            "preferences": {},
            "theme": "light",
            "language": "es",
            
            # Información de sesión
            "session_id": user_data.get("session_id"),
            "ip_address": None,  # Se añadirá por el middleware
            "user_agent": None   # Se añadirá por el middleware
        }
        
        return session_data
    
    @staticmethod
    def update_last_activity(session: Dict[str, Any]):
        """
        Actualiza el timestamp de última actividad
        
        Args:
            session: Diccionario de sesión
        """
        session["last_activity"] = datetime.now().isoformat()
    
    @staticmethod
    def is_session_expired(session: Dict[str, Any], max_age_seconds: int = None) -> bool:
        """
        Verifica si la sesión ha expirado
        
        Args:
            session: Diccionario de sesión
            max_age_seconds: Tiempo máximo de vida en segundos
            
        Returns:
            bool: True si ha expirado
        """
        if not session.get("last_activity"):
            return True
        
        max_age = max_age_seconds or settings.SESSION_MAX_AGE
        last_activity = datetime.fromisoformat(session["last_activity"])
        expiry_time = last_activity + timedelta(seconds=max_age)
        
        return datetime.now() > expiry_time
    
    @staticmethod
    def clean_session_data(session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpia datos sensibles de la sesión antes de logging
        
        Args:
            session: Diccionario de sesión
            
        Returns:
            Dict[str, Any]: Sesión sin datos sensibles
        """
        cleaned = session.copy()
        
        # Remover tokens y datos sensibles
        sensitive_keys = [
            "access_token", 
            "refresh_token", 
            "password", 
            "secret"
        ]
        
        for key in sensitive_keys:
            if key in cleaned:
                cleaned[key] = "[REDACTED]"
        
        return cleaned
    
    @staticmethod
    def get_session_info(session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene información básica de la sesión para mostrar al usuario
        
        Args:
            session: Diccionario de sesión
            
        Returns:
            Dict[str, Any]: Información básica de sesión
        """
        if not session.get("authenticated"):
            return {"authenticated": False}
        
        login_time = None
        last_activity = None
        
        try:
            if session.get("login_time"):
                login_time = datetime.fromisoformat(session["login_time"])
            if session.get("last_activity"):
                last_activity = datetime.fromisoformat(session["last_activity"])
        except ValueError:
            pass
        
        return {
            "authenticated": True,
            "username": session.get("username"),
            "user_roles": session.get("user_roles", []),
            "login_time": login_time,
            "last_activity": last_activity,
            "theme": session.get("theme", "light"),
            "language": session.get("language", "es")
        }

# Middleware personalizado para añadir funcionalidades
class SessionEnhancerMiddleware:
    """
    Middleware adicional para mejorar las sesiones con información de context
    """
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Añade información de contexto a las sesiones
        
        Args:
            scope: Información del ámbito de la solicitud
            receive: Canal para recibir mensajes  
            send: Canal para enviar mensajes
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def enhanced_send(message):
            if message["type"] == "http.response.start":
                # Aquí podrías añadir headers adicionales si es necesario
                pass
            await send(message)
        
        # Crear un request para acceder a la sesión
        request = Request(scope, receive)
        
        # Añadir información de contexto si hay sesión activa
        if hasattr(request, 'session') and request.session.get("authenticated"):
            # Actualizar última actividad
            EnhancedSessionManager.update_last_activity(request.session)
            
            # Añadir información de request si no existe
            if not request.session.get("ip_address"):
                request.session["ip_address"] = request.client.host if request.client else "unknown"
            
            if not request.session.get("user_agent"):
                request.session["user_agent"] = request.headers.get("user-agent", "unknown")
            
            # Verificar expiración de sesión
            if EnhancedSessionManager.is_session_expired(request.session):
                logger.info(f"Sesión expirada para usuario: {request.session.get('username')}")
                request.session.clear()
        
        await self.app(scope, receive, enhanced_send)
"""
Middleware de autenticación para FastAPI
"""
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import List
import logging

from services.auth_service import AuthService

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que verifica la autenticación en rutas protegidas
    """
    
    def __init__(self, app: ASGIApp, excluded_paths: List[str] = None):
        """
        Inicializa el middleware
        
        Args:
            app: Aplicación ASGI
            excluded_paths: Rutas excluidas de la verificación
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or []
        self.auth_service = AuthService()
    
    async def dispatch(self, request: Request, call_next):
        """
        Procesa cada request
        
        Args:
            request: Request de FastAPI
            call_next: Siguiente middleware/handler
        """
        path = request.url.path
        
        # Verificar si la ruta está excluida
        if self._is_excluded_path(path):
            return await call_next(request)
        
        # Verificar autenticación para rutas protegidas
        if not await self.auth_service.is_authenticated(request):
            # Usuario no autenticado
            if self._is_api_request(request):
                # Para requests de API, devolver JSON
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "No autenticado"}
                )
            else:
                # Para requests web, redirigir al login
                next_url = str(request.url)
                login_url = f"/login?next_url={next_url}"
                return RedirectResponse(url=login_url, status_code=302)
        
        # Usuario autenticado, continuar
        response = await call_next(request)
        return response
    
    def _is_excluded_path(self, path: str) -> bool:
        """
        Verifica si una ruta está excluida de la autenticación
        
        Args:
            path: Ruta a verificar
            
        Returns:
            bool: True si está excluida
        """
        # Rutas exactas
        if path in self.excluded_paths:
            return True
        
        # Rutas que empiezan con ciertos prefijos
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return True
        
        return False
    
    def _is_api_request(self, request: Request) -> bool:
        """
        Determina si es una request de API (vs web)
        
        Args:
            request: Request de FastAPI
            
        Returns:
            bool: True si es request de API
        """
        # Verificar por path
        if request.url.path.startswith("/api/"):
            return True
        
        # Verificar por Accept header
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header and "text/html" not in accept_header:
            return True
        
        # Verificar por Content-Type
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            return True
        
        return False
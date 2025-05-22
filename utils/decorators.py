"""
Decoradores para autenticación y autorización
"""
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import List, Callable, Any
import logging

from services.auth_service import AuthService
from config.settings import settings

logger = logging.getLogger(__name__)

def login_required(func: Callable) -> Callable:
    """
    Decorador que requiere que el usuario esté autenticado
    
    Args:
        func: Función a decorar
        
    Returns:
        Callable: Función decorada
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Encontrar el objeto Request en los argumentos
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            # Si no hay Request, buscar en kwargs
            request = kwargs.get('request')
        
        if not request:
            raise HTTPException(
                status_code=500,
                detail="Request object not found"
            )
        
        auth_service = AuthService()
        
        if not await auth_service.is_authenticated(request):
            # Verificar si es una petición API o web
            if _is_api_request(request):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No autenticado"
                )
            else:
                # Redirigir al login
                next_url = str(request.url)
                login_url = f"/login?next_url={next_url}"
                return RedirectResponse(url=login_url, status_code=302)
        
        return await func(*args, **kwargs)
    
    return wrapper

def guest_required(func: Callable) -> Callable:
    """
    Decorador que requiere que el usuario NO esté autenticado
    
    Args:
        func: Función a decorar
        
    Returns:
        Callable: Función decorada
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Encontrar el objeto Request
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            request = kwargs.get('request')
        
        if not request:
            raise HTTPException(
                status_code=500,
                detail="Request object not found"
            )
        
        auth_service = AuthService()
        
        if await auth_service.is_authenticated(request):
            # Usuario ya autenticado, redirigir al dashboard
            return RedirectResponse(url="/dashboard", status_code=302)
        
        return await func(*args, **kwargs)
    
    return wrapper

def role_required(roles: List[str]) -> Callable:
    """
    Decorador que requiere que el usuario tenga alguno de los roles especificados
    
    Args:
        roles: Lista de roles requeridos
        
    Returns:
        Callable: Decorador
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Encontrar el objeto Request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="Request object not found"
                )
            
            auth_service = AuthService()
            
            # Verificar autenticación
            if not await auth_service.is_authenticated(request):
                if _is_api_request(request):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="No autenticado"
                    )
                else:
                    next_url = str(request.url)
                    login_url = f"/login?next_url={next_url}"
                    return RedirectResponse(url=login_url, status_code=302)
            
            # Verificar roles
            if not auth_service.has_any_role(request, roles):
                if _is_api_request(request):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="No tienes permisos para acceder a este recurso"
                    )
                else:
                    # Redirigir a página de acceso denegado
                    return RedirectResponse(url="/403", status_code=302)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def admin_required(func: Callable) -> Callable:
    """
    Decorador que requiere que el usuario sea administrador
    
    Args:
        func: Función a decorar
        
    Returns:
        Callable: Función decorada
    """
    return role_required(settings.ADMIN_ROLES)(func)

def api_auth_required(func: Callable) -> Callable:
    """
    Decorador específico para endpoints de API que requieren autenticación
    
    Args:
        func: Función a decorar
        
    Returns:
        Callable: Función decorada
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Encontrar el objeto Request
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            request = kwargs.get('request')
        
        if not request:
            raise HTTPException(
                status_code=500,
                detail="Request object not found"
            )
        
        auth_service = AuthService()
        
        if not await auth_service.is_authenticated(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticación requerido",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return await func(*args, **kwargs)
    
    return wrapper

def rate_limit(max_requests: int = 60, window_seconds: int = 60) -> Callable:
    """
    Decorador para rate limiting (simplificado)
    
    Args:
        max_requests: Máximo número de peticiones
        window_seconds: Ventana de tiempo en segundos
        
    Returns:
        Callable: Decorador
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Implementación básica de rate limiting
            # En producción usar Redis o similar
            
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                client_ip = request.client.host if request.client else "unknown"
                
                # Aquí implementarías la lógica de rate limiting
                # Por simplicidad, continuamos sin verificar
                logger.debug(f"Rate limit check for {client_ip}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def _is_api_request(request: Request) -> bool:
    """
    Determina si es una request de API
    
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
"""
Middleware de seguridad para FastAPI
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Dict, Any, Set, Optional
import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
import hashlib
import secrets

from config.settings import settings

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware de seguridad que añade headers de seguridad y protecciones
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.csrf_tokens: Dict[str, datetime] = {}
        
        logger.info("SecurityMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        """
        Procesa cada request añadiendo medidas de seguridad
        
        Args:
            request: Request de FastAPI
            call_next: Siguiente middleware/handler
        """
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)
        
        # Rate limiting
        if settings.RATE_LIMIT_ENABLED:
            if not self.rate_limiter.is_allowed(client_ip):
                logger.warning(f"Rate limit excedido para IP: {client_ip}")
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={"Retry-After": "60"}
                )
        
        # Verificar CSRF para requests POST/PUT/DELETE
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if not await self._verify_csrf(request):
                logger.warning(f"CSRF token inválido desde IP: {client_ip}")
                return Response(
                    content="CSRF token invalid",
                    status_code=403
                )
        
        # Procesar request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Añadir headers de seguridad
        self._add_security_headers(response)
        
        # Añadir header de tiempo de procesamiento
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Log de request (sin datos sensibles)
        self._log_request(request, response, process_time, client_ip)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Obtiene la IP real del cliente considerando proxies
        
        Args:
            request: Request de FastAPI
            
        Returns:
            str: IP del cliente
        """
        # Verificar headers de proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Tomar la primera IP (la del cliente original)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # IP directa
        return request.client.host if request.client else "unknown"
    
    async def _verify_csrf(self, request: Request) -> bool:
        """
        Verifica el token CSRF para requests que modifican datos
        
        Args:
            request: Request de FastAPI
            
        Returns:
            bool: True si el token es válido
        """
        # Excluir API endpoints (usan Bearer tokens)
        if request.url.path.startswith("/api/"):
            return True
        
        # Excluir login y rutas públicas
        public_paths = ["/login", "/register", "/forgot-password", "/reset-password"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return True
        
        # Verificar token CSRF
        csrf_token = None
        
        # Buscar en headers
        csrf_token = request.headers.get("X-CSRF-Token")
        
        # Si no está en headers, buscar en form data
        if not csrf_token:
            try:
                if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
                    form_data = await request.form()
                    csrf_token = form_data.get("csrf_token")
            except:
                pass
        
        # Si no hay token, permitir por ahora (en desarrollo)
        if not csrf_token:
            if settings.DEBUG:
                return True
            return False
        
        # Verificar token
        return self._is_valid_csrf_token(csrf_token)
    
    def _is_valid_csrf_token(self, token: str) -> bool:
        """
        Verifica si un token CSRF es válido y no ha expirado
        
        Args:
            token: Token a verificar
            
        Returns:
            bool: True si es válido
        """
        if token not in self.csrf_tokens:
            return False
        
        # Verificar expiración (24 horas)
        created_at = self.csrf_tokens[token]
        if datetime.now() - created_at > timedelta(hours=24):
            del self.csrf_tokens[token]
            return False
        
        return True
    
    def generate_csrf_token(self) -> str:
        """
        Genera un nuevo token CSRF
        
        Returns:
            str: Token CSRF
        """
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[token] = datetime.now()
        
        # Limpiar tokens expirados
        self._cleanup_csrf_tokens()
        
        return token
    
    def _cleanup_csrf_tokens(self):
        """Limpia tokens CSRF expirados"""
        now = datetime.now()
        expired_tokens = [
            token for token, created_at in self.csrf_tokens.items()
            if now - created_at > timedelta(hours=24)
        ]
        
        for token in expired_tokens:
            del self.csrf_tokens[token]
    
    def _add_security_headers(self, response: Response):
        """
        Añade headers de seguridad a la respuesta
        
        Args:
            response: Response de FastAPI
        """
        # Headers de seguridad básicos
        security_headers = {
            # Prevenir XSS
            "X-XSS-Protection": "1; mode=block",
            
            # Prevenir MIME sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevenir clickjacking
            "X-Frame-Options": "DENY",
            
            # Política de referrer
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Política de permisos
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # Cache control para páginas sensibles
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        # CSP (Content Security Policy)
        if not settings.DEBUG:
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' cdnjs.cloudflare.com; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            security_headers["Content-Security-Policy"] = csp_policy
        
        # HSTS solo en HTTPS
        if not settings.DEBUG:
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Añadir headers a la respuesta
        for header, value in security_headers.items():
            response.headers[header] = value
    
    def _log_request(self, request: Request, response: Response, process_time: float, client_ip: str):
        """
        Log de requests sin información sensible
        
        Args:
            request: Request de FastAPI
            response: Response de FastAPI
            process_time: Tiempo de procesamiento
            client_ip: IP del cliente
        """
        # Datos básicos del request
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown")[:100]  # Truncar
        }
        
        # Añadir usuario si está autenticado
        if hasattr(request, 'session') and request.session.get("authenticated"):
            log_data["username"] = request.session.get("username")
        
        # Log según el nivel de severidad
        if response.status_code >= 500:
            logger.error(f"Server error: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"Client error: {log_data}")
        else:
            logger.info(f"Request: {log_data}")

class RateLimiter:
    """
    Rate limiter simple basado en memoria
    """
    
    def __init__(self):
        self.clients: Dict[str, deque] = defaultdict(deque)
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Verifica si un cliente puede hacer una request
        
        Args:
            client_id: Identificador del cliente (IP)
            
        Returns:
            bool: True si está permitido
        """
        now = time.time()
        client_requests = self.clients[client_id]
        
        # Limpiar requests antiguos
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        # Verificar límite
        if len(client_requests) >= self.max_requests:
            return False
        
        # Añadir request actual
        client_requests.append(now)
        return True
    
    def cleanup_old_entries(self):
        """Limpia entradas antiguas para liberar memoria"""
        now = time.time()
        cutoff = now - self.window_seconds * 2  # Mantener un poco más para evitar limpiezas frecuentes
        
        clients_to_remove = []
        for client_id, requests in self.clients.items():
            # Limpiar requests antiguos
            while requests and requests[0] <= cutoff:
                requests.popleft()
            
            # Si no hay requests recientes, marcar para eliminación
            if not requests:
                clients_to_remove.append(client_id)
        
        # Eliminar clientes sin actividad reciente
        for client_id in clients_to_remove:
            del self.clients[client_id]
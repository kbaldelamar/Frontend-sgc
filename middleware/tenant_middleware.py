"""
Middleware para detectar y configurar tenants automáticamente
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import time
from typing import Optional, Callable, List

from config.tenant_config import tenant_config

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que detecta el tenant basado en el dominio/subdominio
    y configura la aplicación accordingly
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.detection_strategies: List[Callable] = [
            self._detect_from_query_param,
            self._detect_from_header,
            self._detect_from_subdomain,
            self._detect_from_domain,
            self._detect_from_environment
        ]
        logger.info("TenantMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        """
        Detecta el tenant y añade la configuración al request
        
        Args:
            request: Request de FastAPI
            call_next: Siguiente middleware/handler
        """
        start_time = time.time()
        
        # Obtener información del host
        host = request.headers.get("host", "localhost")
        user_agent = request.headers.get("user-agent", "")
        
        # Detectar tenant usando múltiples estrategias
        tenant_id = self._detect_tenant(request, host)
        
        # Obtener configuración del tenant
        tenant_branding = tenant_config.get_tenant_config(tenant_id)
        
        # Añadir información al request state
        request.state.tenant_id = tenant_id
        request.state.tenant_config = tenant_branding
        request.state.tenant_detection_time = time.time() - start_time
        
        # Log de detección de tenant
        logger.info(
            f"Tenant detectado: {tenant_id} para host: {host} "
            f"(tiempo: {request.state.tenant_detection_time:.3f}s)"
        )
        
        # Procesar request
        try:
            response = await call_next(request)
            
            # Añadir headers personalizados del tenant
            self._add_tenant_headers(response, tenant_id, tenant_branding, request)
            
            return response
            
        except Exception as e:
            logger.error(f"Error procesando request para tenant {tenant_id}: {str(e)}")
            raise
    
    def _detect_tenant(self, request: Request, host: str) -> str:
        """
        Detecta el tenant usando múltiples estrategias en orden de prioridad
        
        Args:
            request: Request de FastAPI
            host: Host header del request
            
        Returns:
            str: ID del tenant detectado
        """
        for strategy in self.detection_strategies:
            try:
                tenant_id = strategy(request, host)
                if tenant_id and tenant_config.is_valid_tenant(tenant_id):
                    logger.debug(f"Tenant detectado con estrategia {strategy.__name__}: {tenant_id}")
                    return tenant_id
            except Exception as e:
                logger.warning(f"Error en estrategia {strategy.__name__}: {e}")
                continue
        
        # Si ninguna estrategia funciona, usar default
        logger.debug("Usando tenant por defecto")
        return "default"
    
    def _detect_from_query_param(self, request: Request, host: str) -> Optional[str]:
        """Estrategia 1: Query parameter (para testing/debugging)"""
        tenant_param = request.query_params.get("tenant")
        if tenant_param:
            logger.debug(f"Tenant detectado por query param: {tenant_param}")
            return tenant_param.lower()
        return None
    
    def _detect_from_header(self, request: Request, host: str) -> Optional[str]:
        """Estrategia 2: Header personalizado X-Tenant-ID"""
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            logger.debug(f"Tenant detectado por header: {tenant_header}")
            return tenant_header.lower()
        return None
    
    def _detect_from_subdomain(self, request: Request, host: str) -> Optional[str]:
        """Estrategia 3: Subdominio"""
        tenant_id = tenant_config.get_tenant_from_subdomain(host)
        if tenant_id != "default":
            logger.debug(f"Tenant detectado por subdominio: {tenant_id}")
            return tenant_id
        return None
    
    def _detect_from_domain(self, request: Request, host: str) -> Optional[str]:
        """Estrategia 4: Dominio completo"""
        tenant_id = tenant_config.get_tenant_from_domain(host)
        if tenant_id != "default":
            logger.debug(f"Tenant detectado por dominio: {tenant_id}")
            return tenant_id
        return None
    
    def _detect_from_environment(self, request: Request, host: str) -> Optional[str]:
        """Estrategia 5: Variable de entorno por defecto"""
        import os
        default_tenant = os.getenv("DEFAULT_TENANT", "default")
        logger.debug(f"Usando tenant de variable de entorno: {default_tenant}")
        return default_tenant
    
    def _add_tenant_headers(self, response: Response, tenant_id: str, tenant_config_obj, request: Request):
        """
        Añade headers específicos del tenant a la respuesta
        
        Args:
            response: Response de FastAPI
            tenant_id: ID del tenant
            tenant_config_obj: Configuración del tenant
            request: Request de FastAPI
        """
        # Headers informativos (solo en desarrollo)
        import os
        if os.getenv("DEBUG", "False").lower() == "true":
            response.headers["X-Tenant-ID"] = tenant_id
            response.headers["X-Tenant-Name"] = tenant_config_obj.company_name
            response.headers["X-Tenant-Version"] = "1.0"
        
        # Header de CSP personalizado por tenant si existe
        if hasattr(tenant_config_obj, 'custom_csp') and tenant_config_obj.custom_csp:
            response.headers["Content-Security-Policy"] = tenant_config_obj.custom_csp
        
        # Headers de cache personalizados según el tipo de recurso
        if request.url.path.startswith("/static/"):
            # Cache más agresivo para recursos estáticos
            response.headers["Cache-Control"] = "public, max-age=31536000"
        elif request.url.path in ["/tenant.css", "/tenant/config.js"]:
            # Cache moderado para recursos dinámicos del tenant
            response.headers["Cache-Control"] = "public, max-age=3600"

class TenantContextManager:
    """
    Manejador de contexto para operaciones específicas del tenant
    """
    
    @staticmethod
    def get_tenant_from_request(request: Request) -> str:
        """Obtiene el tenant ID del request state"""
        return getattr(request.state, 'tenant_id', 'default')
    
    @staticmethod
    def get_tenant_config_from_request(request: Request):
        """Obtiene la configuración del tenant del request state"""
        return getattr(request.state, 'tenant_config', None)
    
    @staticmethod
    def is_tenant_feature_enabled(request: Request, feature: str) -> bool:
        """
        Verifica si una feature está habilitada para el tenant actual
        
        Args:
            request: Request de FastAPI
            feature: Nombre de la feature (registration, 2fa, etc.)
            
        Returns:
            bool: True si la feature está habilitada
        """
        tenant_config_obj = TenantContextManager.get_tenant_config_from_request(request)
        if not tenant_config_obj:
            return False
        
        feature_mapping = {
            'registration': 'enable_registration',
            'password_reset': 'enable_password_reset',
            'remember_me': 'enable_remember_me',
            '2fa': 'enable_2fa',
            'two_factor': 'enable_2fa'
        }
        
        config_key = feature_mapping.get(feature, f'enable_{feature}')
        return getattr(tenant_config_obj, config_key, False)
    
    @staticmethod
    def get_tenant_api_config(request: Request) -> dict:
        """
        Obtiene configuración de API específica del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            dict: Configuración de API del tenant
        """
        tenant_config_obj = TenantContextManager.get_tenant_config_from_request(request)
        if not tenant_config_obj:
            return {}
        
        return {
            'base_url': getattr(tenant_config_obj, 'api_base_url', ''),
            'timeout': getattr(tenant_config_obj, 'api_timeout', 30),
            'tenant_id': TenantContextManager.get_tenant_from_request(request)
        }
    
    @staticmethod
    def get_tenant_session_config(request: Request) -> dict:
        """
        Obtiene configuración de sesión específica del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            dict: Configuración de sesión del tenant
        """
        tenant_config_obj = TenantContextManager.get_tenant_config_from_request(request)
        if not tenant_config_obj:
            return {'timeout': 86400, 'max_attempts': 5}
        
        return {
            'timeout': getattr(tenant_config_obj, 'session_timeout', 86400),
            'max_attempts': getattr(tenant_config_obj, 'max_login_attempts', 5)
        }
    
    @staticmethod
    def log_tenant_activity(request: Request, activity: str, details: Optional[dict] = None):
        """
        Log específico para actividades del tenant
        
        Args:
            request: Request de FastAPI
            activity: Descripción de la actividad
            details: Detalles adicionales opcionales
        """
        tenant_id = TenantContextManager.get_tenant_from_request(request)
        client_ip = request.client.host if request.client else "unknown"
        
        log_data = {
            "tenant_id": tenant_id,
            "activity": activity,
            "client_ip": client_ip,
            "path": request.url.path,
            "method": request.method
        }
        
        if details:
            log_data.update(details)
        
        logger.info(f"Tenant activity: {log_data}")
    
    @staticmethod
    def validate_tenant_access(request: Request, required_features: List[str] = None) -> bool:
        """
        Valida si el tenant actual tiene acceso a ciertas características
        
        Args:
            request: Request de FastAPI
            required_features: Lista de características requeridas
            
        Returns:
            bool: True si tiene acceso a todas las características
        """
        if not required_features:
            return True
        
        for feature in required_features:
            if not TenantContextManager.is_tenant_feature_enabled(request, feature):
                logger.warning(f"Feature '{feature}' no habilitada para tenant: {TenantContextManager.get_tenant_from_request(request)}")
                return False
        
        return True
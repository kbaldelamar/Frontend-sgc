"""
Middleware para detectar y configurar tenants automáticamente - Versión simple con Settings
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import time
from typing import Optional, Callable, List

from config.tenant_config import tenant_config
from config.settings import settings  # ✅ Importar settings

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que detecta el tenant - Versión SIMPLE que usa Settings
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # ✅ Estrategias simples: query param tiene prioridad, luego Settings
        self.detection_strategies: List[Callable] = [
            self._detect_from_query_param,    # Para testing: ?tenant=biomed
            self._detect_from_settings        # Desde Settings (DEFAULT_TENANT)
        ]
        
        logger.info(f"🏢 TenantMiddleware inicializado")
        logger.info(f"🎯 Tenant configurado en Settings: {settings.DEFAULT_TENANT}")
        logger.info(f"💡 Para cambiar tenant, modifica DEFAULT_TENANT en Settings o usa ?tenant=nombre")
    
    async def dispatch(self, request: Request, call_next):
        """
        Detecta el tenant y añade la configuración al request
        """
        start_time = time.time()
        
        # Obtener información del host
        host = request.headers.get("host", "localhost")
        
        # ✅ Detectar tenant (súper simple)
        tenant_id = self._detect_tenant(request, host)
        
        # Obtener configuración del tenant
        tenant_branding = tenant_config.get_tenant_config(tenant_id)
        
        # Añadir información al request state
        request.state.tenant_id = tenant_id
        request.state.tenant_config = tenant_branding
        request.state.tenant_detection_time = time.time() - start_time
        
        # Log simple
        logger.info(f"🏢 Usando tenant: {tenant_id} para {host}")
        
        # Procesar request
        try:
            response = await call_next(request)
            
            # Añadir headers básicos del tenant (solo en debug)
            if settings.DEBUG:
                response.headers["X-Tenant-ID"] = tenant_id
                response.headers["X-Tenant-Name"] = tenant_branding.company_name
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error procesando request para tenant {tenant_id}: {str(e)}")
            raise
    
    def _detect_tenant(self, request: Request, host: str) -> str:
        """
        Detecta el tenant de forma SIMPLE
        """
        # 1. Verificar query parameter (para testing)
        tenant_param = request.query_params.get("tenant")
        if tenant_param and tenant_config.is_valid_tenant(tenant_param):
            logger.debug(f"✅ Usando tenant desde query param: {tenant_param}")
            return tenant_param
        
        # 2. Usar el configurado en Settings
        tenant_from_settings = settings.DEFAULT_TENANT
        if tenant_config.is_valid_tenant(tenant_from_settings):
            logger.debug(f"✅ Usando tenant desde Settings: {tenant_from_settings}")
            return tenant_from_settings
        
        # 3. Fallback a default si el configurado no existe
        logger.warning(f"⚠️ Tenant configurado no existe: {tenant_from_settings}, usando 'default'")
        return "default"
    
    def _detect_from_query_param(self, request: Request, host: str) -> Optional[str]:
        """Detectar desde query parameter (?tenant=biomed)"""
        return request.query_params.get("tenant")
    
    def _detect_from_settings(self, request: Request, host: str) -> Optional[str]:
        """Detectar desde Settings (DEFAULT_TENANT)"""
        return settings.DEFAULT_TENANT

class TenantContextManager:
    """
    Manejador de contexto simple para operaciones del tenant
    """
    
    @staticmethod
    def get_tenant_from_request(request: Request) -> str:
        """Obtiene el tenant ID del request state"""
        return getattr(request.state, 'tenant_id', settings.DEFAULT_TENANT)
    
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
            feature: Nombre de la feature (registration, password_reset, remember_me, 2fa)
            
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
                tenant_id = TenantContextManager.get_tenant_from_request(request)
                logger.warning(f"Feature '{feature}' no habilitada para tenant: {tenant_id}")
                return False
        
        return True
    
    @staticmethod
    def get_tenant_colors(request: Request) -> dict:
        """
        Obtiene los colores del tenant actual
        
        Args:
            request: Request de FastAPI
            
        Returns:
            dict: Colores del tenant
        """
        tenant_config_obj = TenantContextManager.get_tenant_config_from_request(request)
        if not tenant_config_obj:
            return {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'accent': '#0056b3',
                'success': '#28a745',
                'danger': '#dc3545',
                'warning': '#ffc107',
                'info': '#17a2b8'
            }
        
        return {
            'primary': getattr(tenant_config_obj, 'primary_color', '#007bff'),
            'secondary': getattr(tenant_config_obj, 'secondary_color', '#6c757d'),
            'accent': getattr(tenant_config_obj, 'accent_color', '#0056b3'),
            'success': getattr(tenant_config_obj, 'success_color', '#28a745'),
            'danger': getattr(tenant_config_obj, 'danger_color', '#dc3545'),
            'warning': getattr(tenant_config_obj, 'warning_color', '#ffc107'),
            'info': getattr(tenant_config_obj, 'info_color', '#17a2b8')
        }
    
    @staticmethod
    def get_tenant_contact_info(request: Request) -> dict:
        """
        Obtiene información de contacto del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            dict: Información de contacto
        """
        tenant_config_obj = TenantContextManager.get_tenant_config_from_request(request)
        if not tenant_config_obj:
            return {
                'support_email': '',
                'support_phone': '',
                'website_url': ''
            }
        
        return {
            'support_email': getattr(tenant_config_obj, 'support_email', ''),
            'support_phone': getattr(tenant_config_obj, 'support_phone', ''),
            'website_url': getattr(tenant_config_obj, 'website_url', '')
        }
    
    @staticmethod
    def get_tenant_urls(request: Request) -> dict:
        """
        Obtiene URLs importantes del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            dict: URLs del tenant
        """
        tenant_config_obj = TenantContextManager.get_tenant_config_from_request(request)
        if not tenant_config_obj:
            return {
                'terms': '',
                'privacy': '',
                'help': '',
                'videos': ''
            }
        
        return {
            'terms': getattr(tenant_config_obj, 'terms_url', ''),
            'privacy': getattr(tenant_config_obj, 'privacy_url', ''),
            'help': getattr(tenant_config_obj, 'help_url', ''),
            'videos': getattr(tenant_config_obj, 'video_tutorials_url', '')
        }
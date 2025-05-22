"""
Servicio para manejo de configuración de tenants en templates y vistas
"""
from fastapi import Request
from typing import Dict, Any, Optional, List
import logging

from config.tenant_config import TenantBranding, tenant_config
from middleware.tenant_middleware import TenantContextManager

logger = logging.getLogger(__name__)

class TenantService:
    """Servicio principal para obtener configuración de tenant en las vistas"""
    
    @staticmethod
    def get_tenant_context(request: Request) -> Dict[str, Any]:
        """
        Obtiene el contexto completo del tenant para usar en templates
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Dict[str, Any]: Contexto del tenant para templates
        """
        # Obtener configuración del tenant desde el middleware
        tenant_config_obj: TenantBranding = getattr(request.state, 'tenant_config', None)
        tenant_id: str = getattr(request.state, 'tenant_id', 'default')
        
        if not tenant_config_obj:
            # Fallback si no hay middleware configurado
            logger.warning("No se encontró configuración de tenant en request.state, usando fallback")
            tenant_config_obj = tenant_config.get_tenant_config('default')
        
        # Crear contexto completo
        context = {
            'tenant': {
                'id': tenant_id,
                'company_name': tenant_config_obj.company_name,
                'company_slogan': tenant_config_obj.company_slogan,
                'portal_name': tenant_config_obj.portal_name,
                'portal_subtitle': tenant_config_obj.portal_subtitle,
                'logo_url': tenant_config_obj.logo_url,
                'hero_image_url': tenant_config_obj.hero_image_url,
                'favicon_url': tenant_config_obj.favicon_url,
                'background_image_url': tenant_config_obj.background_image_url,
                
                # Colores y estilos
                'colors': {
                    'primary': tenant_config_obj.primary_color,
                    'secondary': tenant_config_obj.secondary_color,
                    'accent': tenant_config_obj.accent_color,
                    'success': tenant_config_obj.success_color,
                    'danger': tenant_config_obj.danger_color,
                    'warning': tenant_config_obj.warning_color,
                    'info': tenant_config_obj.info_color,
                },
                
                'gradients': {
                    'primary': tenant_config_obj.primary_gradient,
                    'background': tenant_config_obj.background_gradient,
                },
                
                # Contacto y soporte
                'contact': {
                    'support_email': tenant_config_obj.support_email,
                    'support_phone': tenant_config_obj.support_phone,
                    'website_url': tenant_config_obj.website_url,
                },
                
                # URLs importantes
                'urls': {
                    'terms': tenant_config_obj.terms_url,
                    'privacy': tenant_config_obj.privacy_url,
                    'help': tenant_config_obj.help_url,
                    'videos': tenant_config_obj.video_tutorials_url,
                },
                
                # Configuración de features
                'features': {
                    'registration': tenant_config_obj.enable_registration,
                    'password_reset': tenant_config_obj.enable_password_reset,
                    'remember_me': tenant_config_obj.enable_remember_me,
                    'two_factor': tenant_config_obj.enable_2fa,
                },
                
                # Configuración de login
                'login': {
                    'title': tenant_config_obj.login_title,
                    'subtitle': tenant_config_obj.login_subtitle,
                    'username_placeholder': tenant_config_obj.username_placeholder,
                    'password_placeholder': tenant_config_obj.password_placeholder,
                },
                
                # Información de la empresa
                'company_info': {
                    'description': tenant_config_obj.company_description,
                    'address': tenant_config_obj.company_address,
                    'nit': tenant_config_obj.company_nit,
                },
                
                # Configuración técnica
                'technical': {
                    'api_base_url': tenant_config_obj.api_base_url,
                    'api_timeout': tenant_config_obj.api_timeout,
                    'session_timeout': tenant_config_obj.session_timeout,
                    'max_login_attempts': tenant_config_obj.max_login_attempts,
                }
            }
        }
        
        return context
    
    @staticmethod
    def get_tenant_css_variables(request: Request) -> str:
        """
        Genera CSS variables dinámicas basadas en la configuración del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            str: CSS con variables personalizadas
        """
        tenant_config_obj: TenantBranding = getattr(request.state, 'tenant_config', None)
        
        if not tenant_config_obj:
            return ""
        
        css_vars = f"""
        :root {{
            --tenant-primary-color: {tenant_config_obj.primary_color};
            --tenant-secondary-color: {tenant_config_obj.secondary_color};
            --tenant-accent-color: {tenant_config_obj.accent_color};
            --tenant-success-color: {tenant_config_obj.success_color};
            --tenant-danger-color: {tenant_config_obj.danger_color};
            --tenant-warning-color: {tenant_config_obj.warning_color};
            --tenant-info-color: {tenant_config_obj.info_color};
            --tenant-primary-gradient: {tenant_config_obj.primary_gradient};
            --tenant-background-gradient: {tenant_config_obj.background_gradient};
        }}
        
        /* Aplicar variables del tenant */
        body.login-page {{
            background: var(--tenant-background-gradient) !important;
        }}
        
        .logo {{
            background: var(--tenant-primary-gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
        }}
        
        .portal-subtitle {{
            color: var(--tenant-secondary-color) !important;
        }}
        
        .video-link {{
            background: linear-gradient(135deg, var(--tenant-secondary-color), var(--tenant-accent-color)) !important;
        }}
        
        .video-link:hover {{
            box-shadow: 0 5px 15px var(--tenant-secondary-color)33 !important;
        }}
        
        .login-btn {{
            background: var(--tenant-primary-gradient) !important;
        }}
        
        .login-btn:hover {{
            box-shadow: 0 5px 15px var(--tenant-primary-color)33 !important;
        }}
        
        .form-control:focus {{
            border-color: var(--tenant-secondary-color) !important;
            box-shadow: 0 0 0 3px var(--tenant-secondary-color)1a !important;
        }}
        
        .form-control.is-valid {{
            border-color: var(--tenant-success-color) !important;
            box-shadow: 0 0 0 3px var(--tenant-success-color)1a !important;
        }}
        
        .form-control.is-invalid {{
            border-color: var(--tenant-danger-color) !important;
            box-shadow: 0 0 0 3px var(--tenant-danger-color)1a !important;
        }}
        
        .alert-success {{
            border-left-color: var(--tenant-success-color) !important;
        }}
        
        .alert-danger {{
            border-left-color: var(--tenant-danger-color) !important;
        }}
        
        .forgot-password a {{
            color: var(--tenant-secondary-color) !important;
        }}
        
        .register-link a {{
            color: var(--tenant-secondary-color) !important;
        }}
        
        /* Navegación */
        .navbar-brand {{
            color: var(--tenant-primary-color) !important;
        }}
        
        .nav-link:hover {{
            color: var(--tenant-secondary-color) !important;
        }}
        
        /* Botones secundarios */
        .btn-outline-primary {{
            border-color: var(--tenant-primary-color) !important;
            color: var(--tenant-primary-color) !important;
        }}
        
        .btn-outline-primary:hover {{
            background-color: var(--tenant-primary-color) !important;
            border-color: var(--tenant-primary-color) !important;
        }}
        """
        
        return css_vars
    
    @staticmethod
    def get_tenant_meta_tags(request: Request) -> Dict[str, str]:
        """
        Genera meta tags específicos del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Dict[str, str]: Meta tags para el HTML head
        """
        tenant_config_obj: TenantBranding = getattr(request.state, 'tenant_config', None)
        
        if not tenant_config_obj:
            return {}
        
        return {
            'title': f"{tenant_config_obj.portal_name} {tenant_config_obj.portal_subtitle} - {tenant_config_obj.company_name}",
            'description': tenant_config_obj.company_description,
            'keywords': f"{tenant_config_obj.company_name}, {tenant_config_obj.portal_name}, IPS, salud, portal médico",
            'author': tenant_config_obj.company_name,
            'theme-color': tenant_config_obj.primary_color,
            'favicon': tenant_config_obj.favicon_url,
            'og:title': f"{tenant_config_obj.company_name} - {tenant_config_obj.portal_name}",
            'og:description': tenant_config_obj.company_description,
            'og:type': 'website',
            'og:image': tenant_config_obj.logo_url,
            'twitter:card': 'summary',
            'twitter:title': f"{tenant_config_obj.company_name} - {tenant_config_obj.portal_name}",
            'twitter:description': tenant_config_obj.company_description,
        }
    
    @staticmethod
    def get_tenant_javascript_config(request: Request) -> str:
        """
        Genera configuración JavaScript específica del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            str: JavaScript con configuración del tenant
        """
        tenant_context = TenantService.get_tenant_context(request)
        tenant_id = getattr(request.state, 'tenant_id', 'default')
        
        js_config = f"""
        // Configuración del tenant
        window.TENANT_CONFIG = {{
            id: '{tenant_id}',
            name: '{tenant_context['tenant']['company_name']}',
            colors: {{
                primary: '{tenant_context['tenant']['colors']['primary']}',
                secondary: '{tenant_context['tenant']['colors']['secondary']}',
                accent: '{tenant_context['tenant']['colors']['accent']}',
                success: '{tenant_context['tenant']['colors']['success']}',
                danger: '{tenant_context['tenant']['colors']['danger']}',
                warning: '{tenant_context['tenant']['colors']['warning']}',
                info: '{tenant_context['tenant']['colors']['info']}'
            }},
            features: {{
                registration: {str(tenant_context['tenant']['features']['registration']).lower()},
                passwordReset: {str(tenant_context['tenant']['features']['password_reset']).lower()},
                rememberMe: {str(tenant_context['tenant']['features']['remember_me']).lower()},
                twoFactor: {str(tenant_context['tenant']['features']['two_factor']).lower()}
            }},
            urls: {{
                support: '{tenant_context['tenant']['contact']['support_email']}',
                help: '{tenant_context['tenant']['urls']['help']}',
                videos: '{tenant_context['tenant']['urls']['videos']}'
            }},
            api: {{
                timeout: {tenant_context['tenant']['technical']['api_timeout']},
                maxLoginAttempts: {tenant_context['tenant']['technical']['max_login_attempts']}
            }}
        }};
        
        // Funciones de utilidad del tenant
        window.TenantUtils = {{
            getColor: function(colorName) {{
                return window.TENANT_CONFIG.colors[colorName] || '#000000';
            }},
            
            isFeatureEnabled: function(featureName) {{
                return window.TENANT_CONFIG.features[featureName] || false;
            }},
            
            getSupportContact: function() {{
                return window.TENANT_CONFIG.urls.support;
            }},
            
            getHelpUrl: function() {{
                return window.TENANT_CONFIG.urls.help;
            }}
        }};
        """
        
        return js_config
    
    @staticmethod
    def get_tenant_favicon(request: Request) -> str:
        """
        Obtiene la URL del favicon específico del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            str: URL del favicon
        """
        tenant_config_obj: TenantBranding = getattr(request.state, 'tenant_config', None)
        
        if not tenant_config_obj or not tenant_config_obj.favicon_url:
            return "/static/images/favicon/default.ico"
        
        return tenant_config_obj.favicon_url
    
    @staticmethod
    def is_feature_enabled(request: Request, feature_name: str) -> bool:
        """
        Verifica si una característica está habilitada para el tenant actual
        
        Args:
            request: Request de FastAPI
            feature_name: Nombre de la característica
            
        Returns:
            bool: True si está habilitada
        """
        return TenantContextManager.is_tenant_feature_enabled(request, feature_name)
    
    @staticmethod
    def get_tenant_logo_url(request: Request) -> str:
        """
        Obtiene la URL del logo específico del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            str: URL del logo
        """
        tenant_config_obj: TenantBranding = getattr(request.state, 'tenant_config', None)
        
        if not tenant_config_obj or not tenant_config_obj.logo_url:
            return "/static/images/logos/default.png"
        
        return tenant_config_obj.logo_url
    
    @staticmethod
    def get_tenant_hero_image_url(request: Request) -> str:
        """
        Obtiene la URL de la imagen hero específica del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            str: URL de la imagen hero
        """
        tenant_config_obj: TenantBranding = getattr(request.state, 'tenant_config', None)
        
        if not tenant_config_obj or not tenant_config_obj.hero_image_url:
            return "/static/images/hero/default-doctor.jpg"
        
        return tenant_config_obj.hero_image_url
    
    @staticmethod
    def get_tenant_support_info(request: Request) -> Dict[str, str]:
        """
        Obtiene información de soporte específica del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Dict[str, str]: Información de soporte
        """
        tenant_config_obj: TenantBranding = getattr(request.state, 'tenant_config', None)
        
        if not tenant_config_obj:
            return {
                'email': 'soporte@portal-ips.com',
                'phone': '',
                'website': ''
            }
        
        return {
            'email': tenant_config_obj.support_email,
            'phone': tenant_config_obj.support_phone,
            'website': tenant_config_obj.website_url
        }
    
    @staticmethod
    def get_available_tenants() -> List[Dict[str, Any]]:
        """
        Obtiene lista de tenants disponibles (para administración)
        
        Returns:
            List[Dict[str, Any]]: Lista de tenants con información básica
        """
        tenants = []
        
        for tenant_id in tenant_config.get_available_tenants():
            config = tenant_config.get_tenant_config(tenant_id)
            tenants.append({
                'id': tenant_id,
                'name': config.company_name,
                'slogan': config.company_slogan,
                'portal_name': config.portal_name,
                'logo_url': config.logo_url,
                'primary_color': config.primary_color
            })
        
        return tenants
    
    @staticmethod
    def validate_tenant_config(tenant_id: str) -> Dict[str, Any]:
        """
        Valida la configuración de un tenant específico
        
        Args:
            tenant_id: ID del tenant a validar
            
        Returns:
            Dict[str, Any]: Resultado de la validación
        """
        if not tenant_config.is_valid_tenant(tenant_id):
            return {
                'valid': False,
                'errors': [f'Tenant {tenant_id} no existe']
            }
        
        config = tenant_config.get_tenant_config(tenant_id)
        errors = []
        warnings = []
        
        # Validaciones básicas
        if not config.company_name:
            errors.append('company_name es requerido')
        
        if not config.logo_url:
            warnings.append('logo_url no está configurado')
        
        if not config.hero_image_url:
            warnings.append('hero_image_url no está configurado')
        
        if not config.primary_color or not config.primary_color.startswith('#'):
            errors.append('primary_color debe ser un color hexadecimal válido')
        
        if not config.support_email:
            warnings.append('support_email no está configurado')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'tenant_id': tenant_id,
            'company_name': config.company_name
        }
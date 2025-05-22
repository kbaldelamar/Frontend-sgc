"""
Sistema de configuración para múltiples empresas/tenants
"""
import os
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TenantTheme(str, Enum):
    """Temas disponibles para tenants"""
    COOSALUD = "coosalud"
    BIOMED = "biomed"
    MEDICORP = "medicorp"
    DEFAULT = "default"

class TenantBranding(BaseModel):
    """Configuración de marca para cada tenant"""
    # Información básica
    company_name: str = Field(..., description="Nombre de la empresa")
    company_slogan: str = Field(default="", description="Slogan de la empresa")
    portal_name: str = Field(..., description="Nombre del portal")
    portal_subtitle: str = Field(..., description="Subtítulo del portal")
    
    # URLs de imágenes
    logo_url: str = Field(..., description="URL del logo principal")
    hero_image_url: str = Field(..., description="URL de la imagen hero/grande")
    favicon_url: str = Field(default="", description="URL del favicon")
    background_image_url: str = Field(default="", description="URL imagen de fondo")
    
    # Colores (paleta principal)
    primary_color: str = Field(..., description="Color primario (#hex)")
    secondary_color: str = Field(..., description="Color secundario (#hex)")
    accent_color: str = Field(..., description="Color de acento (#hex)")
    success_color: str = Field(default="#27ae60", description="Color de éxito")
    danger_color: str = Field(default="#e74c3c", description="Color de error")
    warning_color: str = Field(default="#f39c12", description="Color de advertencia")
    info_color: str = Field(default="#3498db", description="Color de información")
    
    # Gradientes
    primary_gradient: str = Field(..., description="Gradiente primario CSS")
    background_gradient: str = Field(..., description="Gradiente de fondo CSS")
    
    # Configuración de contacto
    support_email: str = Field(default="", description="Email de soporte")
    support_phone: str = Field(default="", description="Teléfono de soporte")
    website_url: str = Field(default="", description="Sitio web corporativo")
    
    # URLs de documentación
    terms_url: str = Field(default="", description="URL términos y condiciones")
    privacy_url: str = Field(default="", description="URL política de privacidad")
    help_url: str = Field(default="", description="URL centro de ayuda")
    video_tutorials_url: str = Field(default="", description="URL videos instructivos")
    
    # Configuración de features
    enable_registration: bool = Field(default=True, description="Permitir registro")
    enable_password_reset: bool = Field(default=True, description="Permitir reset password")
    enable_remember_me: bool = Field(default=True, description="Permitir recordar sesión")
    enable_2fa: bool = Field(default=False, description="Habilitar 2FA")
    
    # Configuración de login
    login_title: str = Field(default="Iniciar sesión", description="Título del formulario")
    login_subtitle: str = Field(default="", description="Subtítulo del formulario")
    username_placeholder: str = Field(default="Correo electrónico", description="Placeholder username")
    password_placeholder: str = Field(default="Contraseña", description="Placeholder password")
    
    # Información adicional
    company_description: str = Field(default="", description="Descripción de la empresa")
    company_address: str = Field(default="", description="Dirección de la empresa")
    company_nit: str = Field(default="", description="NIT/ID fiscal")
    
    # Configuración de API
    api_base_url: str = Field(default="", description="URL base de la API específica del tenant")
    api_timeout: int = Field(default=30, description="Timeout para API calls")
    
    # Configuración de sesión
    session_timeout: int = Field(default=86400, description="Timeout de sesión en segundos")
    max_login_attempts: int = Field(default=5, description="Máximo intentos de login")
    
    class Config:
        extra = "forbid"
        validate_assignment = True

class TenantConfig:
    """Manejador de configuración de tenants"""
    
    def __init__(self):
        self.configs: Dict[str, TenantBranding] = {}
        self.domain_mapping: Dict[str, str] = {}
        self.subdomain_mapping: Dict[str, str] = {}
        self.load_tenant_configs()
        self._setup_domain_mappings()
    
    def load_tenant_configs(self):
        """Carga las configuraciones de todos los tenants"""
        config_dir = "config/tenants"
        
        # Configuración por defecto
        self.configs["default"] = self._get_default_config()
        
        # Cargar configuraciones específicas
        if os.path.exists(config_dir):
            for filename in os.listdir(config_dir):
                if filename.endswith('.json'):
                    tenant_id = filename.replace('.json', '')
                    config_path = os.path.join(config_dir, filename)
                    
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                            self.configs[tenant_id] = TenantBranding(**config_data)
                            logger.info(f"Configuración cargada para tenant: {tenant_id}")
                    except Exception as e:
                        logger.error(f"Error cargando config para {tenant_id}: {e}")
        else:
            logger.warning(f"Directorio de configuraciones no encontrado: {config_dir}")
            # Crear directorio y archivos por defecto
            self._create_default_configs(config_dir)
    
    def _create_default_configs(self, config_dir: str):
        """Crea configuraciones por defecto si no existen"""
        try:
            os.makedirs(config_dir, exist_ok=True)
            
            # Configuraciones por defecto
            default_configs = {
                "coosalud": self._get_coosalud_config(),
                "biomed": self._get_biomed_config(),
                "medicorp": self._get_medicorp_config()
            }
            
            for tenant_id, config in default_configs.items():
                config_path = os.path.join(config_dir, f"{tenant_id}.json")
                if not os.path.exists(config_path):
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config.dict(), f, indent=2, ensure_ascii=False)
                    logger.info(f"Configuración por defecto creada para: {tenant_id}")
                    
        except Exception as e:
            logger.error(f"Error creando configuraciones por defecto: {e}")
    
    def _setup_domain_mappings(self):
        """Configura mapeos de dominios y subdominios"""
        self.domain_mapping = {
            "coosalud.com": "coosalud",
            "portal-coosalud.com": "coosalud",
            "www.coosalud.com": "coosalud",
            "biomed.com": "biomed",
            "portal-biomed.com": "biomed",
            "www.biomed.com": "biomed",
            "medicorp.com": "medicorp",
            "portal-medicorp.com": "medicorp",
            "www.medicorp.com": "medicorp",
            "localhost": os.getenv("DEFAULT_TENANT", "default"),
            "127.0.0.1": os.getenv("DEFAULT_TENANT", "default"),
        }
        
        # Mapeos de subdominio
        self.subdomain_mapping = {
            "coosalud": "coosalud",
            "biomed": "biomed",
            "medicorp": "medicorp",
            "demo": "default",
            "test": "default"
        }
    
    def get_tenant_config(self, tenant_id: str) -> TenantBranding:
        """Obtiene la configuración de un tenant específico"""
        config = self.configs.get(tenant_id, self.configs["default"])
        logger.debug(f"Obteniendo configuración para tenant: {tenant_id}")
        return config
    
    def get_tenant_from_domain(self, domain: str) -> str:
        """Determina el tenant basado en el dominio"""
        domain_lower = domain.lower()
        
        # Búsqueda exacta
        if domain_lower in self.domain_mapping:
            return self.domain_mapping[domain_lower]
        
        # Búsqueda parcial
        for domain_key, tenant_id in self.domain_mapping.items():
            if domain_key in domain_lower:
                return tenant_id
        
        return "default"
    
    def get_tenant_from_subdomain(self, host: str) -> str:
        """Determina el tenant basado en el subdominio"""
        if "." in host:
            subdomain = host.split(".")[0].lower()
            if subdomain in self.subdomain_mapping:
                return self.subdomain_mapping[subdomain]
        
        return "default"
    
    def get_tenant_from_header(self, tenant_header: str) -> str:
        """Determina el tenant basado en header personalizado"""
        if tenant_header and tenant_header.lower() in self.configs:
            return tenant_header.lower()
        return "default"
    
    def get_available_tenants(self) -> List[str]:
        """Obtiene lista de tenants disponibles"""
        return list(self.configs.keys())
    
    def is_valid_tenant(self, tenant_id: str) -> bool:
        """Verifica si un tenant es válido"""
        return tenant_id in self.configs
    
    def _get_default_config(self) -> TenantBranding:
        """Configuración por defecto"""
        return TenantBranding(
            company_name="Portal IPS",
            company_slogan="Salud y Bienestar",
            portal_name="portal",
            portal_subtitle="IPS",
            logo_url="/static/images/logos/default.png",
            hero_image_url="/static/images/hero/default-doctor.jpg",
            favicon_url="/static/images/favicon/default.ico",
            primary_color="#4CAF50",
            secondary_color="#00BCD4",
            accent_color="#2E8B57",
            primary_gradient="linear-gradient(135deg, #4CAF50, #2E8B57)",
            background_gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            support_email="soporte@portal-ips.com",
            website_url="https://portal-ips.com",
            video_tutorials_url="/tutorials",
            login_title="Iniciar sesión",
            username_placeholder="correo@ejemplo.com",
            password_placeholder="••••••••",
            company_description="Sistema de gestión médica integral"
        )
    
    def _get_coosalud_config(self) -> TenantBranding:
        """Configuración específica de COOSALUD"""
        return TenantBranding(
            company_name="COOSALUD",
            company_slogan="Por Ti y Tu Bienestar",
            portal_name="portal",
            portal_subtitle="IPS",
            logo_url="/static/images/logos/coosalud.png",
            hero_image_url="/static/images/hero/coosalud-doctor.jpg",
            favicon_url="/static/images/favicon/coosalud.ico",
            primary_color="#4CAF50",
            secondary_color="#00BCD4",
            accent_color="#2E8B57",
            primary_gradient="linear-gradient(135deg, #4CAF50, #45a049)",
            background_gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            support_email="soporte@coosalud.com",
            support_phone="+57 300 123 4567",
            website_url="https://coosalud.com",
            video_tutorials_url="https://tutorials.coosalud.com",
            terms_url="https://coosalud.com/terminos",
            privacy_url="https://coosalud.com/privacidad",
            help_url="https://ayuda.coosalud.com",
            username_placeholder="biomedips@gmail.com",
            company_description="Cooperativa de Salud comprometida con tu bienestar",
            company_address="Calle 123 #45-67, Bogotá, Colombia",
            company_nit="800.123.456-7"
        )
    
    def _get_biomed_config(self) -> TenantBranding:
        """Configuración específica de BIOMED"""
        return TenantBranding(
            company_name="BIOMED",
            company_slogan="Innovación en Salud",
            portal_name="sistema",
            portal_subtitle="MÉDICO",
            logo_url="/static/images/logos/biomed.png",
            hero_image_url="/static/images/hero/biomed-technology.jpg",
            favicon_url="/static/images/favicon/biomed.ico",
            primary_color="#2196F3",
            secondary_color="#FF5722",
            accent_color="#1976D2",
            primary_gradient="linear-gradient(135deg, #2196F3, #1976D2)",
            background_gradient="linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
            support_email="soporte@biomed.com",
            support_phone="+57 301 987 6543",
            website_url="https://biomed.com",
            video_tutorials_url="https://capacitacion.biomed.com",
            terms_url="https://biomed.com/terminos-uso",
            privacy_url="https://biomed.com/politica-privacidad",
            help_url="https://soporte.biomed.com",
            username_placeholder="medico@biomed.com",
            login_title="Acceso al Sistema",
            company_description="Tecnología médica de vanguardia para profesionales de la salud",
            company_address="Carrera 7 #32-16, Medellín, Colombia",
            company_nit="900.987.654-3",
            enable_2fa=True
        )
    
    def _get_medicorp_config(self) -> TenantBranding:
        """Configuración específica de MEDICORP"""
        return TenantBranding(
            company_name="MEDICORP",
            company_slogan="Excelencia Médica",
            portal_name="plataforma",
            portal_subtitle="CORPORATIVA",
            logo_url="/static/images/logos/medicorp.png",
            hero_image_url="/static/images/hero/medicorp-team.jpg",
            favicon_url="/static/images/favicon/medicorp.ico",
            primary_color="#9C27B0",
            secondary_color="#FFC107",
            accent_color="#7B1FA2",
            primary_gradient="linear-gradient(135deg, #9C27B0, #7B1FA2)",
            background_gradient="linear-gradient(135deg, #8360c3 0%, #2ebf91 100%)",
            support_email="ayuda@medicorp.com",
            support_phone="+57 302 555 7890",
            website_url="https://medicorp.com",
            video_tutorials_url="https://academy.medicorp.com",
            terms_url="https://medicorp.com/legal/terminos",
            privacy_url="https://medicorp.com/legal/privacidad",
            help_url="https://centro-ayuda.medicorp.com",
            username_placeholder="usuario@medicorp.com",
            login_title="Acceso Corporativo",
            company_description="Corporación médica líder en servicios de salud especializados",
            company_address="Avenida El Dorado #68-90, Bogotá, Colombia",
            company_nit="830.456.789-2",
            enable_2fa=True,
            enable_registration=False
        )

# Instancia global del configurador
tenant_config = TenantConfig()
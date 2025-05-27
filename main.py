"""
Aplicación principal FastAPI para el frontend - Con soporte multi-tenant completo
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.exceptions import HTTPException
import logging
from contextlib import asynccontextmanager
import os
from datetime import datetime

# Configuraciones
from config.settings import settings
from config.tenant_config import tenant_config

# Middlewares
from middleware.auth_middleware import AuthMiddleware
from middleware.session_middleware import CustomSessionMiddleware, SessionEnhancerMiddleware
from middleware.security_middleware import SecurityMiddleware
from middleware.tenant_middleware import TenantMiddleware

# Servicios
from services.tenant_service import TenantService
from services.auth_service import AuthService

# Routers
from routers import auth, dashboard, profile, admin, api_proxy

# Configuración de logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Lifespan para inicialización y limpieza
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Inicializar configuración de tenants
    logger.info("📊 Cargando configuraciones de tenants...")
    try:
        tenant_config.load_tenant_configs()
        
        # Log de tenants disponibles
        available_tenants = list(tenant_config.configs.keys())
        logger.info(f"🏢 Tenants disponibles: {available_tenants}")
        
        # Validar configuraciones de tenants
        for tenant_id in available_tenants:
            validation = TenantService.validate_tenant_config(tenant_id)
            if not validation['valid']:
                logger.warning(f"⚠️ Tenant {tenant_id} tiene errores: {validation['errors']}")
            elif validation.get('warnings'):
                logger.info(f"ℹ️ Tenant {tenant_id} tiene advertencias: {validation['warnings']}")
            else:
                logger.info(f"✅ Tenant {tenant_id} configurado correctamente")
    
    except Exception as e:
        logger.error(f"❌ Error cargando configuraciones de tenants: {e}")
        # Continuar con configuración por defecto
    
    # Verificar directorios de recursos estáticos
    static_dirs = [
        "static/images/logos",
        "static/images/hero", 
        "static/images/favicon",
        "static/css",
        "static/js"
    ]
    
    for static_dir in static_dirs:
        if not os.path.exists(static_dir):
            logger.warning(f"📁 Directorio estático no encontrado: {static_dir}")
            try:
                os.makedirs(static_dir, exist_ok=True)
                logger.info(f"📁 Directorio creado: {static_dir}")
            except Exception as e:
                logger.error(f"❌ Error creando directorio {static_dir}: {e}")
    
    logger.info("🎯 Aplicación iniciada correctamente")
    
    yield
    
    # Limpieza al cerrar
    logger.info("🔄 Cerrando aplicación...")
    logger.info("✅ Aplicación cerrada")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Frontend de aplicación con autenticación multi-tenant",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None
)

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# ================================
# CONFIGURACIÓN DE MIDDLEWARES
# ================================
# ⚠️ ORDEN IMPORTANTE: Los middlewares se ejecutan en orden inverso al que se registran

# 1. Middleware de seguridad (debe ir primero)
app.add_middleware(SecurityMiddleware)

# 2. Middleware de CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"🌐 CORS habilitado para: {settings.CORS_ORIGINS}")

# 3. Middleware de hosts confiables
if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    logger.info(f"🔒 Hosts confiables: {settings.ALLOWED_HOSTS}")

# 4. ✅ NUEVO: Middleware de tenant (DEBE ir ANTES de sesiones)
app.add_middleware(TenantMiddleware)
logger.info("🏢 Middleware de tenant configurado")

# 5. Middleware de sesiones personalizado
app.add_middleware(
    CustomSessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE,
    https_only=settings.SESSION_COOKIE_SECURE,
    same_site=settings.SESSION_COOKIE_SAMESITE
)
logger.info(f"🍪 Sesiones configuradas: cookie={settings.SESSION_COOKIE_NAME}")

# 6. Middleware de autenticación (debe ir después de sesiones y tenant)
app.add_middleware(
    AuthMiddleware,
    excluded_paths=settings.PUBLIC_PATHS + ["/static", "/docs", "/redoc", "/openapi.json", "/tenant"]
)
logger.info(f"🔐 Autenticación configurada, rutas públicas: {len(settings.PUBLIC_PATHS)}")

# 7. Middleware para mejorar sesiones con información de contexto (último)
app.add_middleware(SessionEnhancerMiddleware)

# ================================
# ENDPOINTS ESPECÍFICOS DE TENANT
# ================================

@app.get("/tenant.css")
async def tenant_css(request: Request):
    """Endpoint que sirve CSS dinámico basado en el tenant"""
    css_content = TenantService.get_tenant_css_variables(request)
    tenant_id = getattr(request.state, 'tenant_id', 'default')
    
    return Response(
        content=css_content,
        media_type="text/css",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache por 1 hora
            "Content-Type": "text/css; charset=utf-8",
            "X-Tenant-ID": tenant_id if settings.DEBUG else "",
            "X-Generated": "dynamic-css"
        }
    )

@app.get("/tenant/config.js")
async def tenant_js_config(request: Request):
    """Endpoint que sirve configuración JavaScript del tenant"""
    js_content = TenantService.get_tenant_javascript_config(request)
    tenant_id = getattr(request.state, 'tenant_id', 'default')
    
    return Response(
        content=js_content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache por 1 hora
            "Content-Type": "application/javascript; charset=utf-8",
            "X-Tenant-ID": tenant_id if settings.DEBUG else "",
            "X-Generated": "dynamic-js"
        }
    )

@app.get("/tenant/info")
async def tenant_info(request: Request):
    """Endpoint para obtener información del tenant actual (solo debug)"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = getattr(request.state, 'tenant_id', 'default')
    detection_time = getattr(request.state, 'tenant_detection_time', 0)
    
    return {
        "tenant_id": tenant_id,
        "detection_time_ms": round(detection_time * 1000, 2),
        "host": request.headers.get("host", "unknown"),
        "user_agent": request.headers.get("user-agent", "unknown")[:100],
        "request_info": {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown"
        },
        "tenant_config": tenant_context,
        "available_tenants": TenantService.get_available_tenants(),
        "validation": TenantService.validate_tenant_config(tenant_id)
    }

@app.get("/tenant/list")
async def tenant_list(request: Request):
    """Lista de tenants disponibles (solo debug)"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "tenants": TenantService.get_available_tenants(),
        "current": getattr(request.state, 'tenant_id', 'default'),
        "total": len(tenant_config.get_available_tenants())
    }

# ================================
# REGISTRAR ROUTERS
# ================================

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(api_proxy.router)

# Debug: Log de rutas registradas
if settings.DEBUG:
    logger.info("📍 Rutas registradas:")
    route_count = 0
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            logger.info(f"  {route.methods} {route.path}")
            route_count += 1
        elif hasattr(route, 'path'):
            logger.info(f"  Mount: {route.path}")
        else:
            logger.info(f"  Other: {type(route).__name__}")
    logger.info(f"📍 Total de rutas: {route_count}")

# ================================
# RUTAS PRINCIPALES
# ================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página principal - redirige según autenticación"""
    auth_service = AuthService()
    tenant_id = getattr(request.state, 'tenant_id', 'default')
    
    # Log de acceso a la raíz
    logger.info(f"Acceso a raíz desde tenant: {tenant_id}")
    
    if await auth_service.is_authenticated(request):
        # Usuario autenticado, redirigir al dashboard
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        # Usuario no autenticado, redirigir al login
        return RedirectResponse(url="/login", status_code=302)

@app.get("/health")
async def health_check(request: Request):
    """Endpoint de salud para monitoreo con información del tenant"""
    # Obtener información del tenant actual
    tenant_id = getattr(request.state, 'tenant_id', 'unknown')
    tenant_config_obj = getattr(request.state, 'tenant_config', None)
    detection_time = getattr(request.state, 'tenant_detection_time', 0)
    
    health_info = {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": "2024-12-19T10:30:00Z",  # En producción usar datetime.now().isoformat()
        "environment": "development" if settings.DEBUG else "production"
    }
    
    # Información del tenant (solo en debug)
    if settings.DEBUG:
        health_info["tenant"] = {
            "id": tenant_id,
            "name": tenant_config_obj.company_name if tenant_config_obj else "Unknown",
            "detection_time_ms": round(detection_time * 1000, 2),
            "features": {
                "registration": TenantService.is_feature_enabled(request, "registration"),
                "password_reset": TenantService.is_feature_enabled(request, "password_reset"),
                "2fa": TenantService.is_feature_enabled(request, "2fa")
            }
        }
        
        health_info["system"] = {
            "available_tenants": len(tenant_config.get_available_tenants()),
            "static_files": os.path.exists("static"),
            "templates": os.path.exists("templates")
        }
    
    return health_info

@app.get("/favicon.ico")
async def favicon(request: Request):
    """Favicon dinámico basado en el tenant"""
    favicon_url = TenantService.get_tenant_favicon(request)
    
    # Si es una URL relativa, servir el archivo estático
    if favicon_url.startswith("/static/"):
        # Quitar el prefijo /static/ y buscar el archivo
        file_path = favicon_url.replace("/static/", "")
        full_path = os.path.join("static", file_path)
        
        if os.path.exists(full_path):
            # En producción usarías FileResponse
            return RedirectResponse(url=favicon_url, status_code=302)
    
    # Fallback al favicon por defecto
    return RedirectResponse(url="/static/images/favicon/default.ico", status_code=302)

# ================================
# MANEJADORES DE ERRORES
# ================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Manejador para páginas no encontradas con branding del tenant"""
    tenant_context = TenantService.get_tenant_context(request)
    tenant_css = TenantService.get_tenant_css_variables(request)
    
    context = {
        "request": request,
        "title": "Página no encontrada",
        "message": "La página que buscas no existe",
        "error_code": 404,
        "tenant_css": tenant_css,
        **tenant_context
    }
    
    return templates.TemplateResponse(
        "errors/404.html",
        context,
        status_code=404
    )

@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """Manejador para acceso prohibido con branding del tenant"""
    tenant_context = TenantService.get_tenant_context(request)
    tenant_css = TenantService.get_tenant_css_variables(request)
    
    context = {
        "request": request,
        "title": "Acceso prohibido",
        "message": "No tienes permisos para acceder a esta página",
        "error_code": 403,
        "tenant_css": tenant_css,
        **tenant_context
    }
    
    return templates.TemplateResponse(
        "errors/403.html",
        context,
        status_code=403
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Manejador para errores internos con branding del tenant"""
    tenant_id = getattr(request.state, 'tenant_id', 'unknown')
    logger.error(f"Error interno en tenant {tenant_id}: {str(exc)}", exc_info=True)
    
    tenant_context = TenantService.get_tenant_context(request)
    tenant_css = TenantService.get_tenant_css_variables(request)
    
    context = {
        "request": request,
        "title": "Error interno",
        "message": "Ocurrió un error inesperado" if not settings.DEBUG else str(exc),
        "error_code": 500,
        "tenant_css": tenant_css,
        **tenant_context
    }
    
    return templates.TemplateResponse(
        "errors/500.html",
        context,
        status_code=500
    )

@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc: HTTPException):
    """Manejador para rate limiting"""
    tenant_context = TenantService.get_tenant_context(request)
    tenant_css = TenantService.get_tenant_css_variables(request)
    
    context = {
        "request": request,
        "title": "Demasiadas solicitudes",
        "message": "Has excedido el límite de solicitudes. Intenta más tarde.",
        "error_code": 429,
        "tenant_css": tenant_css,
        **tenant_context
    }
    
    return templates.TemplateResponse(
        "errors/429.html",
        context,
        status_code=429
    )

# ================================
# MIDDLEWARE ADICIONAL PARA TEMPLATES
# ================================

@app.middleware("http")
async def add_tenant_context_to_responses(request: Request, call_next):
    """Middleware para añadir contexto global y headers de seguridad"""
    
    # Ejecutar la petición
    response = await call_next(request)
    
    # Añadir headers de seguridad adicionales
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Headers informativos del tenant (solo en debug)
    if settings.DEBUG:
        tenant_id = getattr(request.state, 'tenant_id', 'unknown')
        response.headers["X-Debug-Tenant"] = tenant_id
        response.headers["X-Debug-App"] = f"{settings.APP_NAME}-{settings.APP_VERSION}"
    
    return response

# ================================
# FILTROS PERSONALIZADOS PARA JINJA2
# ================================

def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Filtro para formatear fechas"""
    if value is None:
        return ""
    return value.strftime(format)

def format_currency(value, tenant_context=None):
    """Filtro para formatear moneda según el tenant"""
    if value is None:
        return "$0.00"
    
    # Aquí podrías personalizar el formato según el tenant
    # Por ejemplo, diferentes monedas por región
    return f"${value:,.2f}"

def has_role(user_roles, required_role):
    """Filtro para verificar roles en templates"""
    if not user_roles:
        return False
    return required_role in user_roles

def tenant_color(color_name, tenant_context=None):
    """Filtro para obtener colores del tenant"""
    if not tenant_context or 'tenant' not in tenant_context:
        return "#000000"
    
    colors = tenant_context['tenant'].get('colors', {})
    return colors.get(color_name, "#000000")

def tenant_feature(feature_name, tenant_context=None):
    """Filtro para verificar si una feature está habilitada"""
    if not tenant_context or 'tenant' not in tenant_context:
        return False
    
    features = tenant_context['tenant'].get('features', {})
    return features.get(feature_name, False)

def format_file_size(bytes_value):
    """Filtro para formatear tamaños de archivo"""
    if bytes_value is None:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

# Registrar filtros personalizados
templates.env.filters["datetime"] = format_datetime
templates.env.filters["currency"] = format_currency
templates.env.filters["has_role"] = has_role
templates.env.filters["tenant_color"] = tenant_color
templates.env.filters["tenant_feature"] = tenant_feature
templates.env.filters["file_size"] = format_file_size

# ================================
# FUNCIONES GLOBALES PARA TEMPLATES
# ================================

def get_current_year():
    """Función global para obtener el año actual"""
    from datetime import datetime
    return datetime.now().year

def get_app_version():
    """Función global para obtener la versión de la app"""
    return settings.APP_VERSION

# Registrar funciones globales
templates.env.globals["current_year"] = get_current_year
templates.env.globals["app_version"] = get_app_version
templates.env.globals["debug_mode"] = settings.DEBUG

# ================================
# FUNCIÓN PARA EJECUTAR LA APLICACIÓN
# ================================

def run_app():
    """Función para ejecutar la aplicación"""
    import uvicorn
    
    logger.info(f"🌟 Iniciando servidor en {settings.HOST}:{settings.PORT}")
    logger.info(f"🔧 Modo debug: {settings.DEBUG}")
    logger.info(f"🏢 Tenants disponibles: {len(tenant_config.get_available_tenants())}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
        reload_dirs=["templates", "static"] if settings.DEBUG else None
    )

    @app.get("/debug/tenant")
    async def debug_tenant_info(request: Request):
        """Endpoint para ver qué tenant está activo"""
        if not settings.DEBUG:
            raise HTTPException(status_code=404, detail="Not found")

        tenant_id = getattr(request.state, 'tenant_id', 'unknown')
        tenant_config_obj = getattr(request.state, 'tenant_config', None)

        # Lista de archivos JSON disponibles
        import os, glob
        available_files = []
        if os.path.exists("config/tenants"):
            json_files = glob.glob("config/tenants/*.json") 
            available_files = [os.path.basename(f).replace('.json', '') for f in json_files]

        return {
            "tenant_activo": tenant_id,
            "configurado_en_settings": settings.DEFAULT_TENANT,
            "company_name": tenant_config_obj.company_name if tenant_config_obj else "N/A",
            "archivo_json_usado": f"config/tenants/{tenant_id}.json",
            "archivos_json_disponibles": sorted(available_files),
            "como_cambiar": {
                "opcion_1": "Cambiar DEFAULT_TENANT en .env",
                "opcion_2": "Cambiar DEFAULT_TENANT en config/settings.py",
                "opcion_3": "Usar query parameter: ?tenant=nombre"
            }
        }

if __name__ == "__main__":
    run_app()
"""
Aplicación principal FastAPI para el frontend
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
import logging
from contextlib import asynccontextmanager

from config.settings import settings
from middleware.auth_middleware import AuthMiddleware
from middleware.session_middleware import CustomSessionMiddleware, SessionEnhancerMiddleware
from middleware.security_middleware import SecurityMiddleware
from routers import auth, dashboard, profile, admin, api_proxy
from services.auth_service import AuthService

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
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Inicialización (si es necesaria)
    # Aquí puedes inicializar conexiones, cache, etc.
    
    yield
    
    # Limpieza al cerrar
    logger.info("Cerrando aplicación")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Frontend de aplicación con autenticación",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Middleware de seguridad (debe ir primero)
app.add_middleware(SecurityMiddleware)

# Middleware de CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middleware de hosts confiables
if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Middleware de sesiones personalizado
app.add_middleware(
    CustomSessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE,
    https_only=settings.SESSION_COOKIE_SECURE,
    same_site=settings.SESSION_COOKIE_SAMESITE
)

# Middleware para mejorar sesiones con información de contexto
app.add_middleware(SessionEnhancerMiddleware)

# Middleware de autenticación personalizado
app.add_middleware(
    AuthMiddleware,
    excluded_paths=settings.PUBLIC_PATHS + ["/static", "/docs", "/redoc", "/openapi.json"]
)

# Registrar routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(api_proxy.router)

# Ruta principal (redirect a dashboard o login)
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página principal - redirige según autenticación"""
    auth_service = AuthService()
    
    if await auth_service.is_authenticated(request):
        # Usuario autenticado, redirigir al dashboard
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        # Usuario no autenticado, redirigir al login
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

# Ruta de salud del sistema
@app.get("/health")
async def health_check():
    """Endpoint de salud para monitoreo"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Manejadores de errores personalizados
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Manejador para páginas no encontradas"""
    return templates.TemplateResponse(
        "errors/404.html",
        {
            "request": request,
            "title": "Página no encontrada",
            "message": "La página que buscas no existe"
        },
        status_code=404
    )

@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: HTTPException):
    """Manejador para acceso prohibido"""
    return templates.TemplateResponse(
        "errors/403.html",
        {
            "request": request,
            "title": "Acceso prohibido",
            "message": "No tienes permisos para acceder a esta página"
        },
        status_code=403
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Manejador para errores internos"""
    logger.error(f"Error interno: {str(exc)}", exc_info=True)
    
    return templates.TemplateResponse(
        "errors/500.html",
        {
            "request": request,
            "title": "Error interno",
            "message": "Ocurrió un error inesperado"
        },
        status_code=500
    )

# Función para añadir variables globales a templates
@app.middleware("http")
async def add_template_globals(request: Request, call_next):
    """Middleware para añadir variables globales a todos los templates"""
    
    # Ejecutar la petición
    response = await call_next(request)
    
    # Añadir headers de seguridad adicionales
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Filtros personalizados para Jinja2
def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Filtro para formatear fechas"""
    if value is None:
        return ""
    return value.strftime(format)

def format_currency(value):
    """Filtro para formatear moneda"""
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

def has_role(user_roles, required_role):
    """Filtro para verificar roles en templates"""
    if not user_roles:
        return False
    return required_role in user_roles

# Registrar filtros personalizados
templates.env.filters["datetime"] = format_datetime
templates.env.filters["currency"] = format_currency
templates.env.filters["has_role"] = has_role

# Función para ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
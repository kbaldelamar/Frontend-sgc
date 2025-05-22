"""
Router de autenticación - Con soporte multi-tenant completo
"""
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging

from services.auth_service import AuthService
from services.tenant_service import TenantService
from utils.decorators import guest_required
from config.settings import settings

router = APIRouter(prefix="", tags=["auth"])
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

@router.get("/login", response_class=HTMLResponse)
@guest_required
async def login_page(request: Request, error: Optional[str] = None, 
                    message: Optional[str] = None, next_url: Optional[str] = None):
    """
    Página de login con configuración multi-tenant
    
    Args:
        request: Request de FastAPI
        error: Mensaje de error opcional
        message: Mensaje de éxito opcional
        next_url: URL a la que redirigir después del login
    """
    # Obtener configuración del tenant
    tenant_context = TenantService.get_tenant_context(request)
    tenant_meta = TenantService.get_tenant_meta_tags(request)
    tenant_css = TenantService.get_tenant_css_variables(request)
    tenant_js = TenantService.get_tenant_javascript_config(request)
    
    # Log del tenant actual
    tenant_id = getattr(request.state, 'tenant_id', 'unknown')
    logger.info(f"Renderizando página de login para tenant: {tenant_id}")
    
    # Contexto base
    context = {
        "request": request,
        "title": tenant_meta.get('title', 'Iniciar Sesión'),
        "description": tenant_meta.get('description', ''),
        "error": error,
        "message": message,
        "next_url": next_url or "/dashboard",
        "tenant_css": tenant_css,
        "tenant_js": tenant_js,
        "tenant_meta": tenant_meta,
        "settings": settings,  # Para acceder a configuraciones globales
        
        # Configuración específica del tenant
        **tenant_context,
        
        # Configuración de features desde el tenant
        "enable_registration": tenant_context['tenant']['features']['registration'],
        "enable_password_reset": tenant_context['tenant']['features']['password_reset'],
        "enable_remember_me": tenant_context['tenant']['features']['remember_me'],
        "enable_2fa": tenant_context['tenant']['features']['two_factor'],
    }
    
    return templates.TemplateResponse("auth/login.html", context)

@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    next_url: str = Form("/dashboard")
):
    """
    Procesa el formulario de login con validación específica del tenant
    """
    # Obtener configuración del tenant
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = tenant_context['tenant']['id']
    
    # Obtener configuración de seguridad del tenant
    max_attempts = tenant_context['tenant']['technical']['max_login_attempts']
    
    # Validaciones básicas
    if not username or not password:
        logger.warning(f"Login fallido - campos vacíos - tenant: {tenant_id} - IP: {request.client.host if request.client else 'unknown'}")
        return RedirectResponse(
            url=f"/login?error=Por favor completa todos los campos",
            status_code=302
        )
    
    # Verificar si remember_me está habilitado para este tenant
    if remember_me and not tenant_context['tenant']['features']['remember_me']:
        remember_me = False
        logger.info(f"Remember me deshabilitado para tenant: {tenant_id}")
    
    auth_service = AuthService()
    
    try:
        # Intentar login con información del tenant
        success, login_data, error_msg = await auth_service.login(
            username=username, 
            password=password, 
            remember_me=remember_me,
            tenant_id=tenant_id,
            max_attempts=max_attempts
        )
        
        if success:
            # Crear sesión con información del tenant
            await auth_service.create_session(request, login_data, tenant_id)
            
            # Log con información del tenant
            logger.info(f"Login exitoso para usuario: {username} en tenant: {tenant_id}")
            
            # Redirigir a la URL solicitada
            return RedirectResponse(url=next_url, status_code=302)
        else:
            # Error en el login
            logger.warning(f"Login fallido para usuario: {username} en tenant: {tenant_id} - {error_msg}")
            return RedirectResponse(
                url=f"/login?error={error_msg}&next_url={next_url}",
                status_code=302
            )
    
    except Exception as e:
        logger.error(f"Error en login para tenant {tenant_id}: {str(e)}")
        return RedirectResponse(
            url="/login?error=Error interno del servidor",
            status_code=302
        )

@router.get("/logout")
async def logout(request: Request):
    """
    Cierra la sesión del usuario con logging específico del tenant
    """
    auth_service = AuthService()
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = tenant_context['tenant']['id']
    
    try:
        # Obtener username antes de cerrar sesión
        username = request.session.get("username", "usuario desconocido")
        
        # Cerrar sesión
        await auth_service.logout(request)
        
        logger.info(f"Logout exitoso para usuario: {username} en tenant: {tenant_id}")
        
        # Redirigir al login con mensaje de éxito
        return RedirectResponse(
            url="/login?message=Sesión cerrada correctamente", 
            status_code=302
        )
    
    except Exception as e:
        logger.error(f"Error en logout para tenant {tenant_id}: {str(e)}")
        return RedirectResponse(url="/login", status_code=302)

@router.get("/register", response_class=HTMLResponse)
@guest_required
async def register_page(request: Request, error: Optional[str] = None, 
                       success: Optional[str] = None):
    """
    Página de registro con configuración del tenant
    """
    # Obtener configuración del tenant
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = tenant_context['tenant']['id']
    
    # Verificar si el registro está habilitado para este tenant
    if not tenant_context['tenant']['features']['registration']:
        logger.warning(f"Intento de acceso a registro deshabilitado para tenant: {tenant_id}")
        raise HTTPException(status_code=404, detail="Registro no disponible")
    
    # Obtener configuración adicional del tenant
    tenant_meta = TenantService.get_tenant_meta_tags(request)
    tenant_css = TenantService.get_tenant_css_variables(request)
    tenant_js = TenantService.get_tenant_javascript_config(request)
    
    context = {
        "request": request,
        "title": f"Crear Cuenta - {tenant_context['tenant']['company_name']}",
        "error": error,
        "success": success,
        "tenant_css": tenant_css,
        "tenant_js": tenant_js,
        "tenant_meta": tenant_meta,
        "settings": settings,
        **tenant_context
    }
    
    return templates.TemplateResponse("auth/register.html", context)

@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    terms_accepted: bool = Form(False)
):
    """
    Procesa el formulario de registro con validación del tenant
    """
    # Obtener configuración del tenant
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = tenant_context['tenant']['id']
    
    # Verificar si el registro está habilitado
    if not tenant_context['tenant']['features']['registration']:
        raise HTTPException(status_code=404, detail="Registro no disponible")
    
    # Validaciones
    errors = []
    
    if not all([username, email, password, confirm_password, first_name, last_name]):
        errors.append("Todos los campos son obligatorios")
    
    if password != confirm_password:
        errors.append("Las contraseñas no coinciden")
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not terms_accepted:
        errors.append("Debes aceptar los términos y condiciones")
    
    # Validaciones adicionales específicas del tenant
    if '@' not in email:
        errors.append("El correo electrónico no es válido")
    
    if len(username) < 3:
        errors.append("El nombre de usuario debe tener al menos 3 caracteres")
    
    if errors:
        error_msg = "; ".join(errors)
        logger.warning(f"Registro fallido - validación - tenant: {tenant_id} - {error_msg}")
        return RedirectResponse(
            url=f"/register?error={error_msg}",
            status_code=302
        )
    
    try:
        # Preparar datos de registro con información del tenant
        register_data = {
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
            "first_name": first_name,
            "last_name": last_name,
            "tenant_id": tenant_id,  # Incluir tenant en el registro
            "terms_accepted": terms_accepted,
            "registration_source": "web_portal",
            "client_info": {
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        }
        
        # Llamar a la API de registro
        auth_service = AuthService()
        success, response_data, error_msg = await auth_service.register(register_data)
        
        if success:
            logger.info(f"Registro exitoso para usuario: {username} en tenant: {tenant_id}")
            return RedirectResponse(
                url="/register?success=Cuenta creada exitosamente. Por favor verifica tu correo electrónico.",
                status_code=302
            )
        else:
            logger.warning(f"Registro fallido para usuario: {username} en tenant: {tenant_id} - {error_msg}")
            return RedirectResponse(
                url=f"/register?error={error_msg}",
                status_code=302
            )
    
    except Exception as e:
        logger.error(f"Error en registro para tenant {tenant_id}: {str(e)}")
        return RedirectResponse(
            url="/register?error=Error interno del servidor",
            status_code=302
        )

@router.get("/forgot-password", response_class=HTMLResponse)
@guest_required
async def forgot_password_page(request: Request, error: Optional[str] = None, 
                              success: Optional[str] = None):
    """
    Página de recuperación de contraseña con configuración del tenant
    """
    # Obtener configuración del tenant
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = tenant_context['tenant']['id']
    
    # Verificar si el reset de contraseña está habilitado
    if not tenant_context['tenant']['features']['password_reset']:
        logger.warning(f"Intento de acceso a reset password deshabilitado para tenant: {tenant_id}")
        raise HTTPException(status_code=404, detail="Recuperación de contraseña no disponible")
    
    tenant_css = TenantService.get_tenant_css_variables(request)
    tenant_js = TenantService.get_tenant_javascript_config(request)
    tenant_meta = TenantService.get_tenant_meta_tags(request)
    
    context = {
        "request": request,
        "title": f"Recuperar Contraseña - {tenant_context['tenant']['company_name']}",
        "error": error,
        "success": success,
        "tenant_css": tenant_css,
        "tenant_js": tenant_js,
        "tenant_meta": tenant_meta,
        "settings": settings,
        **tenant_context
    }
    
    return templates.TemplateResponse("auth/forgot_password.html", context)

@router.post("/forgot-password")
async def forgot_password_submit(
    request: Request,
    email: str = Form(...)
):
    """
    Procesa el formulario de recuperación de contraseña
    """
    # Obtener configuración del tenant
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = tenant_context['tenant']['id']
    
    # Verificar si el reset está habilitado
    if not tenant_context['tenant']['features']['password_reset']:
        raise HTTPException(status_code=404, detail="Recuperación de contraseña no disponible")
    
    if not email:
        return RedirectResponse(
            url="/forgot-password?error=El correo electrónico es obligatorio",
            status_code=302
        )
    
    # Validación básica de email
    if '@' not in email or '.' not in email:
        return RedirectResponse(
            url="/forgot-password?error=El correo electrónico no es válido",
            status_code=302
        )
    
    try:
        # Llamar a la API de recuperación con información del tenant
        auth_service = AuthService()
        success, response_data, error_msg = await auth_service.forgot_password(email, tenant_id)
        
        # Log del intento
        logger.info(f"Solicitud de reset password para email: {email} en tenant: {tenant_id}")
        
        # Siempre mostrar mensaje de éxito por seguridad
        return RedirectResponse(
            url="/forgot-password?success=Si el correo existe, recibirás instrucciones para restablecer tu contraseña",
            status_code=302
        )
    
    except Exception as e:
        logger.error(f"Error en forgot password para tenant {tenant_id}: {str(e)}")
        return RedirectResponse(
            url="/forgot-password?success=Si el correo existe, recibirás instrucciones para restablecer tu contraseña",
            status_code=302
        )

@router.get("/reset-password", response_class=HTMLResponse)
@guest_required
async def reset_password_page(request: Request, token: Optional[str] = None, 
                             error: Optional[str] = None):
    """
    Página de restablecimiento de contraseña con configuración del tenant
    """
    # Obtener configuración del tenant
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = tenant_context['tenant']['id']
    
    # Verificar si el reset está habilitado
    if not tenant_context['tenant']['features']['password_reset']:
        raise HTTPException(status_code=404, detail="Restablecimiento de contraseña no disponible")
    
    if not token:
        return RedirectResponse(url="/forgot-password", status_code=302)
    
    tenant_css = TenantService.get_tenant_css_variables(request)
    tenant_js = TenantService.get_tenant_javascript_config(request)
    tenant_meta = TenantService.get_tenant_meta_tags(request)
    
    context = {
        "request": request,
        "title": f"Restablecer Contraseña - {tenant_context['tenant']['company_name']}",
        "token": token,
        "error": error,
        "tenant_css": tenant_css,
        "tenant_js": tenant_js,
        "tenant_meta": tenant_meta,
        "settings": settings,
        **tenant_context
    }
    
    return templates.TemplateResponse("auth/reset_password.html", context)

@router.post("/reset-password")
async def reset_password_submit(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """
    Procesa el formulario de restablecimiento de contraseña
    """
    # Obtener configuración del tenant
    tenant_context = TenantService.get_tenant_context(request)
    tenant_id = tenant_context['tenant']['id']
    
    # Verificar si el reset está habilitado
    if not tenant_context['tenant']['features']['password_reset']:
        raise HTTPException(status_code=404, detail="Restablecimiento de contraseña no disponible")
    
    # Validaciones
    if not all([token, password, confirm_password]):
        return RedirectResponse(
            url=f"/reset-password?token={token}&error=Todos los campos son obligatorios",
            status_code=302
        )
    
    if password != confirm_password:
        return RedirectResponse(
            url=f"/reset-password?token={token}&error=Las contraseñas no coinciden",
            status_code=302
        )
    
    if len(password) < 8:
        return RedirectResponse(
            url=f"/reset-password?token={token}&error=La contraseña debe tener al menos 8 caracteres",
            status_code=302
        )
    
    # Validaciones adicionales de seguridad
    if password.lower() in ['password', '12345678', 'qwerty123']:
        return RedirectResponse(
            url=f"/reset-password?token={token}&error=La contraseña es demasiado común",
            status_code=302
        )
    
    try:
        # Llamar a la API de restablecimiento con información del tenant
        reset_data = {
            "token": token,
            "new_password": password,
            "confirm_password": confirm_password,
            "tenant_id": tenant_id,
            "client_info": {
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        }
        
        auth_service = AuthService()
        success, response_data, error_msg = await auth_service.reset_password(reset_data)
        
        if success:
            logger.info(f"Reset password exitoso para token en tenant: {tenant_id}")
            return RedirectResponse(
                url="/login?message=Contraseña restablecida exitosamente",
                status_code=302
            )
        else:
            logger.warning(f"Reset password fallido para token en tenant: {tenant_id} - {error_msg}")
            return RedirectResponse(
                url=f"/reset-password?token={token}&error={error_msg}",
                status_code=302
            )
    
    except Exception as e:
        logger.error(f"Error en reset password para tenant {tenant_id}: {str(e)}")
        return RedirectResponse(
            url=f"/reset-password?token={token}&error=Error interno del servidor",
            status_code=302
        )

# ================================
# ENDPOINTS ADICIONALES DE TENANT
# ================================

@router.get("/tenant/switch")
async def switch_tenant_page(request: Request):
    """
    Página para cambiar de tenant (solo en modo debug)
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Obtener tenants disponibles
    available_tenants = TenantService.get_available_tenants()
    current_tenant = getattr(request.state, 'tenant_id', 'default')
    tenant_context = TenantService.get_tenant_context(request)
    
    context = {
        "request": request,
        "title": "Cambiar Tenant - Debug",
        "current_tenant": current_tenant,
        "available_tenants": available_tenants,
        **tenant_context
    }
    
    return templates.TemplateResponse("auth/switch_tenant.html", context)

@router.get("/tenant/css")
async def tenant_css_endpoint(request: Request):
    """
    Endpoint que sirve CSS dinámico basado en el tenant
    """
    css_content = TenantService.get_tenant_css_variables(request)
    
    return Response(
        content=css_content,
        media_type="text/css",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache por 1 hora
            "Content-Type": "text/css; charset=utf-8",
            "X-Tenant-CSS": "dynamic"
        }
    )

@router.get("/tenant/config.js")
async def tenant_js_config_endpoint(request: Request):
    """
    Endpoint que sirve configuración JavaScript del tenant
    """
    js_content = TenantService.get_tenant_javascript_config(request)
    
    return Response(
        content=js_content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache por 1 hora
            "Content-Type": "application/javascript; charset=utf-8",
            "X-Tenant-JS": "dynamic"
        }
    )

@router.get("/tenant/validate")
async def validate_tenant_endpoint(request: Request):
    """
    Endpoint para validar configuración del tenant (solo debug)
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    tenant_id = getattr(request.state, 'tenant_id', 'default')
    validation_result = TenantService.validate_tenant_config(tenant_id)
    
    return validation_result

@router.get("/tenant/info")
async def tenant_info_endpoint(request: Request):
    """
    Endpoint para obtener información completa del tenant (solo debug)
    """
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
        "tenant_config": tenant_context,
        "available_tenants": TenantService.get_available_tenants()
    }

# ================================
# VERIFICACIÓN DE SALUD POR TENANT
# ================================

@router.get("/auth/health")
async def auth_health_check(request: Request):
    """
    Health check específico del módulo de autenticación
    """
    tenant_id = getattr(request.state, 'tenant_id', 'default')
    tenant_config = getattr(request.state, 'tenant_config', None)
    
    health_info = {
        "status": "ok",
        "module": "auth",
        "tenant_id": tenant_id,
        "features": {
            "login": True,
            "logout": True,
            "registration": TenantService.is_feature_enabled(request, "registration"),
            "password_reset": TenantService.is_feature_enabled(request, "password_reset"),
            "remember_me": TenantService.is_feature_enabled(request, "remember_me"),
            "two_factor": TenantService.is_feature_enabled(request, "2fa")
        },
        "endpoints": {
            "login": "/login",
            "logout": "/logout",
            "register": "/register" if TenantService.is_feature_enabled(request, "registration") else None,
            "forgot_password": "/forgot-password" if TenantService.is_feature_enabled(request, "password_reset") else None,
            "reset_password": "/reset-password" if TenantService.is_feature_enabled(request, "password_reset") else None
        }
    }
    
    # Información adicional solo en debug
    if settings.DEBUG:
        health_info["debug_info"] = {
            "tenant_name": tenant_config.company_name if tenant_config else "Unknown",
            "api_timeout": tenant_config.api_timeout if tenant_config else settings.API_TIMEOUT,
            "session_timeout": tenant_config.session_timeout if tenant_config else settings.SESSION_MAX_AGE
        }
    
    return health_info
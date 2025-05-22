"""
Router de autenticación - Maneja login, logout, registro
"""
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging

from services.auth_service import AuthService
from utils.decorators import guest_required
from config.settings import settings

router = APIRouter(prefix="", tags=["auth"])
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

@router.get("/login", response_class=HTMLResponse)
@guest_required
async def login_page(request: Request, error: Optional[str] = None, next_url: Optional[str] = None):
    """
    Página de login
    
    Args:
        request: Request de FastAPI
        error: Mensaje de error opcional
        next_url: URL a la que redirigir después del login
    """
    context = {
        "request": request,
        "title": "Iniciar Sesión",
        "error": error,
        "next_url": next_url or "/dashboard",
        "enable_registration": settings.ENABLE_REGISTRATION,
        "enable_password_reset": settings.ENABLE_PASSWORD_RESET
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
    Procesa el formulario de login
    
    Args:
        request: Request de FastAPI
        username: Nombre de usuario
        password: Contraseña
        remember_me: Recordar sesión
        next_url: URL de redirección
    """
    # Validaciones básicas
    if not username or not password:
        return RedirectResponse(
            url=f"/login?error=Por favor completa todos los campos",
            status_code=302
        )
    
    auth_service = AuthService()
    
    try:
        # Intentar login
        success, login_data, error_msg = await auth_service.login(username, password, remember_me)
        
        if success:
            # Crear sesión
            await auth_service.create_session(request, login_data)
            
            # Registrar evento de login
            logger.info(f"Login exitoso para usuario: {username}")
            
            # Redirigir a la URL solicitada
            return RedirectResponse(url=next_url, status_code=302)
        else:
            # Error en el login
            return RedirectResponse(
                url=f"/login?error={error_msg}&next_url={next_url}",
                status_code=302
            )
    
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return RedirectResponse(
            url="/login?error=Error interno del servidor",
            status_code=302
        )

@router.get("/logout")
async def logout(request: Request):
    """
    Cierra la sesión del usuario
    
    Args:
        request: Request de FastAPI
    """
    auth_service = AuthService()
    
    try:
        # Obtener username antes de cerrar sesión (para logging)
        username = request.session.get("username", "usuario desconocido")
        
        # Cerrar sesión
        await auth_service.logout(request)
        
        logger.info(f"Logout exitoso para usuario: {username}")
        
        # Redirigir al login con mensaje de éxito
        return RedirectResponse(url="/login?message=Sesión cerrada correctamente", status_code=302)
    
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        return RedirectResponse(url="/login", status_code=302)

@router.get("/register", response_class=HTMLResponse)
@guest_required
async def register_page(request: Request, error: Optional[str] = None, success: Optional[str] = None):
    """
    Página de registro
    
    Args:
        request: Request de FastAPI
        error: Mensaje de error opcional
        success: Mensaje de éxito opcional
    """
    if not settings.ENABLE_REGISTRATION:
        raise HTTPException(status_code=404, detail="Registro deshabilitado")
    
    context = {
        "request": request,
        "title": "Crear Cuenta",
        "error": error,
        "success": success
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
    Procesa el formulario de registro
    
    Args:
        request: Request de FastAPI
        username: Nombre de usuario
        email: Correo electrónico
        password: Contraseña
        confirm_password: Confirmación de contraseña
        first_name: Nombre
        last_name: Apellido
        terms_accepted: Términos aceptados
    """
    if not settings.ENABLE_REGISTRATION:
        raise HTTPException(status_code=404, detail="Registro deshabilitado")
    
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
    
    if errors:
        error_msg = "; ".join(errors)
        return RedirectResponse(
            url=f"/register?error={error_msg}",
            status_code=302
        )
    
    try:
        # Preparar datos de registro
        register_data = {
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
            "first_name": first_name,
            "last_name": last_name
        }
        
        # Llamar a la API de registro
        auth_service = AuthService()
        async with auth_service.client as client:
            response = await client.post(
                f"{settings.AUTH_API_URL}/auth/register",
                json=register_data
            )
        
        if response.status_code == 201:
            logger.info(f"Registro exitoso para usuario: {username}")
            return RedirectResponse(
                url="/register?success=Cuenta creada exitosamente. Por favor verifica tu correo electrónico.",
                status_code=302
            )
        else:
            error_data = response.json()
            error_msg = error_data.get("detail", "Error en el registro")
            return RedirectResponse(
                url=f"/register?error={error_msg}",
                status_code=302
            )
    
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return RedirectResponse(
            url="/register?error=Error interno del servidor",
            status_code=302
        )

@router.get("/forgot-password", response_class=HTMLResponse)
@guest_required
async def forgot_password_page(request: Request, error: Optional[str] = None, success: Optional[str] = None):
    """
    Página de recuperación de contraseña
    
    Args:
        request: Request de FastAPI
        error: Mensaje de error opcional
        success: Mensaje de éxito opcional
    """
    if not settings.ENABLE_PASSWORD_RESET:
        raise HTTPException(status_code=404, detail="Recuperación de contraseña deshabilitada")
    
    context = {
        "request": request,
        "title": "Recuperar Contraseña",
        "error": error,
        "success": success
    }
    
    return templates.TemplateResponse("auth/forgot_password.html", context)

@router.post("/forgot-password")
async def forgot_password_submit(
    request: Request,
    email: str = Form(...)
):
    """
    Procesa el formulario de recuperación de contraseña
    
    Args:
        request: Request de FastAPI
        email: Correo electrónico
    """
    if not settings.ENABLE_PASSWORD_RESET:
        raise HTTPException(status_code=404, detail="Recuperación de contraseña deshabilitada")
    
    if not email:
        return RedirectResponse(
            url="/forgot-password?error=El correo electrónico es obligatorio",
            status_code=302
        )
    
    try:
        # Llamar a la API de recuperación (la implementarías en tu API de auth)
        auth_service = AuthService()
        async with auth_service.client as client:
            response = await client.post(
                f"{settings.AUTH_API_URL}/auth/forgot-password",
                json={"email": email}
            )
        
        # Siempre mostrar mensaje de éxito por seguridad
        return RedirectResponse(
            url="/forgot-password?success=Si el correo existe, recibirás instrucciones para restablecer tu contraseña",
            status_code=302
        )
    
    except Exception as e:
        logger.error(f"Error en forgot password: {str(e)}")
        return RedirectResponse(
            url="/forgot-password?success=Si el correo existe, recibirás instrucciones para restablecer tu contraseña",
            status_code=302
        )

@router.get("/reset-password", response_class=HTMLResponse)
@guest_required
async def reset_password_page(request: Request, token: Optional[str] = None, error: Optional[str] = None):
    """
    Página de restablecimiento de contraseña
    
    Args:
        request: Request de FastAPI
        token: Token de restablecimiento
        error: Mensaje de error opcional
    """
    if not settings.ENABLE_PASSWORD_RESET:
        raise HTTPException(status_code=404, detail="Restablecimiento de contraseña deshabilitado")
    
    if not token:
        return RedirectResponse(url="/forgot-password", status_code=302)
    
    context = {
        "request": request,
        "title": "Restablecer Contraseña",
        "token": token,
        "error": error
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
    
    Args:
        request: Request de FastAPI
        token: Token de restablecimiento
        password: Nueva contraseña
        confirm_password: Confirmación de contraseña
    """
    if not settings.ENABLE_PASSWORD_RESET:
        raise HTTPException(status_code=404, detail="Restablecimiento de contraseña deshabilitado")
    
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
    
    try:
        # Llamar a la API de restablecimiento
        reset_data = {
            "token": token,
            "new_password": password,
            "confirm_password": confirm_password
        }
        
        auth_service = AuthService()
        async with auth_service.client as client:
            response = await client.post(
                f"{settings.AUTH_API_URL}/auth/reset-password",
                json=reset_data
            )
        
        if response.status_code == 200:
            return RedirectResponse(
                url="/login?success=Contraseña restablecida exitosamente",
                status_code=302
            )
        else:
            error_data = response.json()
            error_msg = error_data.get("detail", "Error al restablecer contraseña")
            return RedirectResponse(
                url=f"/reset-password?token={token}&error={error_msg}",
                status_code=302
            )
    
    except Exception as e:
        logger.error(f"Error en reset password: {str(e)}")
        return RedirectResponse(
            url=f"/reset-password?token={token}&error=Error interno del servidor",
            status_code=302
        )
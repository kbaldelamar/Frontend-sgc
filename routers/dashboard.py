"""
Router del dashboard - Usando templates correctamente
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Dashboard principal usando templates"""
    
    # Obtener datos del usuario desde la sesión
    user_data = {
        "username": request.session.get("username", "Usuario"),
        "user_id": request.session.get("user_id", "1"),
        "roles": request.session.get("user_roles", ["user"])
    }
    
    # Datos del dashboard
    dashboard_data = {
        "user": user_data,
        "stats": {
            "total_users": 150,
            "active_sessions": 23,
            "total_requests": 1247,
            "system_uptime": "7 días, 12 horas"
        },
        "recent_activity": [
            {"action": "Login exitoso", "user": user_data.get("username"), "time": "Hace 2 minutos"},
            {"action": "Nuevo usuario registrado", "user": "juan.perez", "time": "Hace 15 minutos"},
            {"action": "Actualización de perfil", "user": "maria.garcia", "time": "Hace 1 hora"},
        ]
    }
    
    context = {
        "request": request,
        "title": "Dashboard - Sistema de Gestión",
        "user": user_data,
        "dashboard_data": dashboard_data
    }
    
    # Usar el template
    return templates.TemplateResponse("dashboard/index.html", context)

@router.get("/test", response_class=HTMLResponse)
async def test_route():
    """Ruta de prueba simple"""
    return HTMLResponse(content="<h1>Dashboard Router Test - Funcionando!</h1>")
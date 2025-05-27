"""
Router del dashboard - Usando datos reales de la API de autenticación
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.api_service import ApiService

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Dashboard principal usando datos reales de la sesión y API"""
    
    # Obtener datos REALES del usuario desde la sesión
    user_data = {
        "username": request.session.get("username", "Usuario"),
        "user_id": request.session.get("user_id", ""),
        "roles": request.session.get("user_roles", []),
        "access_token": request.session.get("access_token", ""),
        "token_type": request.session.get("token_type", "bearer"),
        "authenticated": request.session.get("authenticated", False),
        "login_time": request.session.get("login_time", "")
    }
    
    # Inicializar el servicio de API para obtener datos reales
    api_service = ApiService()
    
    # Intentar obtener estadísticas reales de la API de datos
    try:
        # Estas llamadas dependerán de los endpoints que tengas en tu API de datos
        statistics = await api_service.get_statistics() or {}
        dashboard_stats = await api_service.get_dashboard_data() or {}
        
        # Si no hay datos de la API, usar valores por defecto
        stats = {
            "total_users": statistics.get("total_users", 0),
            "active_sessions": statistics.get("active_sessions", 1),  # Al menos la sesión actual
            "total_requests": statistics.get("total_requests", 0),
            "system_uptime": statistics.get("system_uptime", "Desconocido")
        }
        
    except Exception as e:
        # Si la API de datos no está disponible, usar valores por defecto
        print(f"⚠️ API de datos no disponible: {e}")
        stats = {
            "total_users": "N/A",
            "active_sessions": 1,  # Al menos la sesión actual
            "total_requests": "N/A",
            "system_uptime": "N/A - API no disponible"
        }
    
    # Datos del dashboard con información REAL
    dashboard_data = {
        "user": user_data,
        "stats": stats,
        "recent_activity": [
            {
                "action": "Login exitoso", 
                "user": user_data.get("username"), 
                "time": "Hace unos momentos",
                "details": f"Token tipo: {user_data.get('token_type')}"
            },
            {
                "action": "Sesión iniciada", 
                "user": user_data.get("username"), 
                "time": user_data.get("login_time", "Hora desconocida"),
                "details": f"ID de usuario: {user_data.get('user_id')}"
            },
            {
                "action": "Roles asignados", 
                "user": user_data.get("username"), 
                "time": "Al iniciar sesión",
                "details": f"Roles: {', '.join(user_data.get('roles', ['Sin roles']))}"
            }
        ],
        "session_info": {
            "token_type": user_data.get("token_type"),
            "authenticated": user_data.get("authenticated"),
            "login_time": user_data.get("login_time"),
            "has_access_token": bool(user_data.get("access_token")),
            "token_preview": f"{user_data.get('access_token', '')[:20]}..." if user_data.get('access_token') else "No disponible"
        }
    }
    
    context = {
        "request": request,
        "title": f"Dashboard - {user_data.get('username')}",
        "user": user_data,
        "dashboard_data": dashboard_data
    }
    
    # Usar el template
    return templates.TemplateResponse("dashboard/index.html", context)

@router.get("/test", response_class=HTMLResponse)
async def test_route():
    """Ruta de prueba simple"""
    return HTMLResponse(content="<h1>Dashboard Router Test - Funcionando!</h1>")

@router.get("/test", response_class=HTMLResponse)
async def test_route():
    """Ruta de prueba simple"""
    return HTMLResponse(content="<h1>Dashboard Router Test - Funcionando!</h1>")
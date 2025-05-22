"""
Test dashboard simple para verificar rutas
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["test"])

@router.get("/dashboard", response_class=HTMLResponse)
async def simple_dashboard(request: Request):
    """Dashboard simple para test"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>🎉 Dashboard Funcionando!</h1>
            <div class="alert alert-success">
                <p>El usuario está autenticado correctamente.</p>
                <p><strong>Sesión:</strong> {{ request.session }}</p>
            </div>
            <a href="/logout" class="btn btn-danger">Cerrar Sesión</a>
        </div>
    </body>
    </html>
    """
    return html_content

@router.get("/test", response_class=HTMLResponse)
async def test_route():
    """Ruta de prueba simple"""
    return "<h1>Test Route Works!</h1>"
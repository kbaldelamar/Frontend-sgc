# Frontend-sgc

# Estructura del Proyecto Frontend - FastAPI + Jinja2

```
frontend_app/
├── main.py                     # Aplicación principal FastAPI
├── requirements.txt            # Dependencias
├── .env                        # Variables de entorno
├── config/
│   ├── __init__.py
│   └── settings.py            # Configuración de la aplicación
├── routers/
│   ├── __init__.py
│   ├── auth.py                # Rutas de autenticación
│   ├── dashboard.py           # Rutas del dashboard
│   ├── profile.py             # Rutas del perfil
│   ├── admin.py               # Rutas de administración
│   └── api_proxy.py           # Proxy a la API de datos
├── services/
│   ├── __init__.py
│   ├── auth_service.py        # Servicio de autenticación
│   ├── api_service.py         # Servicio para API de datos
│   ├── session_service.py     # Manejo de sesiones
│   └── cache_service.py       # Cache y almacenamiento temporal
├── middleware/
│   ├── __init__.py
│   ├── auth_middleware.py     # Middleware de autenticación
│   ├── session_middleware.py  # Middleware de sesiones
│   └── security_middleware.py # Middleware de seguridad
├── templates/
│   ├── base.html              # Template base
│   ├── layouts/
│   │   ├── auth.html          # Layout para páginas de auth
│   │   └── app.html           # Layout para páginas de la app
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── forgot_password.html
│   ├── dashboard/
│   │   ├── index.html
│   │   ├── analytics.html
│   │   └── reports.html
│   ├── profile/
│   │   ├── index.html
│   │   └── settings.html
│   ├── admin/
│   │   ├── users.html
│   │   └── system.html
│   ├── components/
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   ├── alerts.html
│   │   ├── modals.html
│   │   └── forms/
│   │       ├── input.html
│   │       ├── select.html
│   │       └── button.html
│   └── errors/
│       ├── 404.html
│       ├── 403.html
│       └── 500.html
├── static/
│   ├── css/
│   │   ├── app.css            # Estilos principales
│   │   ├── auth.css           # Estilos de autenticación
│   │   ├── dashboard.css      # Estilos del dashboard
│   │   └── components.css     # Estilos de componentes
│   ├── js/
│   │   ├── app.js             # JavaScript principal
│   │   ├── auth.js            # JS de autenticación
│   │   ├── dashboard.js       # JS del dashboard
│   │   ├── api.js             # Cliente API JavaScript
│   │   └── components/
│   │       ├── modal.js
│   │       ├── toast.js
│   │       └── form-validation.js
│   ├── images/
│   │   ├── logo.png
│   │   ├── favicon.ico
│   │   └── avatars/
│   └── libs/
│   |   ├── bootstrap/         # Bootstrap CSS/JS
│   |   ├── jquery/
│   |   ├── chart.js/
│   |   └── datatables/
|   ├── logos/
│   ├── coosalud.png
│   ├── biomed.png  
│   ├── medicorp.png
│   └── default.png
├── hero/
│   ├── coosalud-doctor.jpg
│   ├── biomed-technology.jpg
│   ├── medicorp-team.jpg
│   └── default-doctor.jpg
└── favicon/
|    ├── coosalud.ico
|    ├── biomed.ico
|    ├── medicorp.ico
|    └── default.ico
├── utils/
│   ├── __init__.py
│   ├── decorators.py          # Decoradores de autenticación
│   ├── helpers.py             # Funciones auxiliares
│   ├── validators.py          # Validadores personalizados
│   └── constants.py           # Constantes de la aplicación
├── models/
│   ├── __init__.py
│   ├── user.py                # Modelos de usuario (Pydantic)
│   ├── auth.py                # Modelos de autenticación
│   └── responses.py           # Modelos de respuesta
└── tests/
    ├── __init__.py
    ├── test_auth.py
    ├── test_routes.py
    └── test_services.py
```

## Dependencias (requirements.txt)

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.25.1
pydantic==2.4.2
pydantic-settings==2.0.3
python-dotenv==1.0.0
itsdangerous==2.1.2
redis==5.0.1
aiofiles==23.2.1
```

## Características Principales

### 1. **Rutas Reales y Navegación**
- URLs semánticas: `/login`, `/dashboard`, `/profile`
- Redirects automáticos según autenticación
- Breadcrumbs y navegación contextual

### 2. **Sistema de Sesiones Robusto**
- Cookies HTTPOnly y Secure
- Almacenamiento en Redis (opcional)
- Expiración automática de sesiones
- CSRF Protection

### 3. **Middleware Personalizado**
- Autenticación automática en rutas protegidas
- Manejo de roles y permisos
- Logging de actividad de usuario
- Rate limiting

### 4. **Templates Dinámicos**
- Herencia de templates con Jinja2
- Componentes reutilizables
- Renderizado condicional según roles
- Formularios con validación

### 5. **Frontend Interactivo**
- JavaScript modular
- AJAX para operaciones sin recarga
- Componentes UI (modales, toasts, formularios)
- Integración con librerías (Bootstrap, Chart.js)

### 6. **Proxy a API de Datos**
- Rutas `/api/*` que conectan con tu API de datos
- Inyección automática de tokens de auth
- Manejo de errores y timeouts
- Cache de respuestas frecuentes

### 7. **Seguridad Integrada**
- Headers de seguridad automáticos
- Validación CSRF
- Sanitización de inputs
- Rate limiting por usuario/IP
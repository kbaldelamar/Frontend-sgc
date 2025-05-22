"""
Servicio de autenticación para FastAPI frontend - Con soporte multi-tenant
"""
import httpx
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
from jose import jwt, JWTError

from config.settings import settings
from middleware.tenant_middleware import TenantContextManager

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.auth_api_url = settings.AUTH_API_URL
        self.client = httpx.AsyncClient(timeout=settings.API_TIMEOUT)
    
    async def login(self, username: str, password: str, remember_me: bool = False, 
                   tenant_id: str = "default", max_attempts: int = 5) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Realiza el login del usuario contra la API de auth con información del tenant
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            remember_me: Recordar sesión
            tenant_id: ID del tenant
            max_attempts: Máximo número de intentos permitidos
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (éxito, datos_usuario, mensaje_error)
        """
        try:
            login_data = {
                "username": username,
                "password": password,
                "remember_me": remember_me,
                "tenant_id": tenant_id,  # ✅ NUEVO: Incluir tenant
                "client_info": {
                    "platform": "web_frontend",
                    "version": settings.APP_VERSION
                }
            }
            
            # Headers específicos del tenant
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-ID": tenant_id,
                "X-Client-Platform": "web"
            }
            
            response = await self.client.post(
                f"{self.auth_api_url}/auth/login",
                json=login_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # ✅ NUEVO: Validar que el usuario pertenece al tenant
                user_tenant = data.get("user", {}).get("tenant_id")
                if user_tenant and user_tenant != tenant_id:
                    logger.warning(f"Usuario {username} intentó login en tenant incorrecto: {tenant_id} vs {user_tenant}")
                    return False, None, "Usuario no autorizado para este portal"
                
                logger.info(f"Usuario {username} autenticado correctamente en tenant {tenant_id}")
                return True, data, None
            elif response.status_code == 429:
                # Rate limiting
                return False, None, f"Demasiados intentos. Máximo {max_attempts} permitidos."
            else:
                error_data = response.json()
                error_msg = error_data.get("detail", "Error de autenticación")
                logger.warning(f"Error de login para {username} en tenant {tenant_id}: {error_msg}")
                return False, None, error_msg
                
        except httpx.RequestError as e:
            error_msg = f"Error de conexión: {str(e)}"
            logger.error(f"Error de conexión en login para tenant {tenant_id}: {error_msg}")
            return False, None, "Error de conexión con el servidor"
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"Error inesperado en login para tenant {tenant_id}: {error_msg}")
            return False, None, "Error inesperado"
    
    async def register(self, register_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Registra un nuevo usuario con información del tenant
        
        Args:
            register_data: Datos del registro incluyendo tenant_id
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (éxito, datos_respuesta, mensaje_error)
        """
        try:
            tenant_id = register_data.get("tenant_id", "default")
            
            # Headers específicos del tenant
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-ID": tenant_id,
                "X-Client-Platform": "web"
            }
            
            response = await self.client.post(
                f"{self.auth_api_url}/auth/register",
                json=register_data,
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Registro exitoso para usuario: {register_data.get('username')} en tenant: {tenant_id}")
                return True, data, None
            else:
                error_data = response.json()
                error_msg = error_data.get("detail", "Error en el registro")
                logger.warning(f"Error en registro para tenant {tenant_id}: {error_msg}")
                return False, None, error_msg
                
        except Exception as e:
            logger.error(f"Error en registro: {str(e)}")
            return False, None, "Error interno del servidor"
    
    async def forgot_password(self, email: str, tenant_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Solicita recuperación de contraseña con información del tenant
        
        Args:
            email: Correo electrónico
            tenant_id: ID del tenant
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (éxito, datos_respuesta, mensaje_error)
        """
        try:
            forgot_data = {
                "email": email,
                "tenant_id": tenant_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-ID": tenant_id
            }
            
            response = await self.client.post(
                f"{self.auth_api_url}/auth/forgot-password",
                json=forgot_data,
                headers=headers
            )
            
            # Siempre devolver éxito por seguridad
            return True, {}, None
            
        except Exception as e:
            logger.error(f"Error en forgot password para tenant {tenant_id}: {str(e)}")
            return True, {}, None  # Siempre éxito por seguridad
    
    async def reset_password(self, reset_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Restablece contraseña con información del tenant
        
        Args:
            reset_data: Datos del reset incluyendo tenant_id
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (éxito, datos_respuesta, mensaje_error)
        """
        try:
            tenant_id = reset_data.get("tenant_id", "default")
            
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-ID": tenant_id
            }
            
            response = await self.client.post(
                f"{self.auth_api_url}/auth/reset-password",
                json=reset_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, data, None
            else:
                error_data = response.json()
                error_msg = error_data.get("detail", "Error al restablecer contraseña")
                return False, None, error_msg
                
        except Exception as e:
            logger.error(f"Error en reset password: {str(e)}")
            return False, None, "Error interno del servidor"
    
    async def logout(self, request: Request) -> bool:
        """
        Cierra la sesión del usuario con información del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            bool: True si el logout fue exitoso
        """
        try:
            # Obtener información del tenant y sesión
            tenant_id = TenantContextManager.get_tenant_from_request(request)
            refresh_token = request.session.get("refresh_token")
            username = request.session.get("username", "unknown")
            
            if refresh_token:
                # Revocar el token en el servidor con información del tenant
                logout_data = {
                    "refresh_token": refresh_token,
                    "tenant_id": tenant_id
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "X-Tenant-ID": tenant_id
                }
                
                await self.client.post(
                    f"{self.auth_api_url}/auth/logout",
                    json=logout_data,
                    headers=headers
                )
            
            # Limpiar sesión
            request.session.clear()
            logger.info(f"Usuario {username} desconectado del tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error durante logout: {str(e)}")
            # Limpiar sesión aunque haya error
            request.session.clear()
            return True
    
    async def refresh_token(self, request: Request) -> bool:
        """
        Refresca el token de acceso con información del tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            bool: True si el refresh fue exitoso
        """
        try:
            tenant_id = TenantContextManager.get_tenant_from_request(request)
            refresh_token = request.session.get("refresh_token")
            
            if not refresh_token:
                return False
            
            refresh_data = {
                "refresh_token": refresh_token,
                "tenant_id": tenant_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Tenant-ID": tenant_id
            }
            
            response = await self.client.post(
                f"{self.auth_api_url}/auth/refresh-token",
                json=refresh_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Actualizar tokens en la sesión
                request.session["access_token"] = data["access_token"]
                request.session["refresh_token"] = data["refresh_token"]
                
                # Actualizar información del usuario
                user_info = self._decode_token(data["access_token"])
                if user_info:
                    request.session["user_data"] = user_info
                    # ✅ NUEVO: Verificar que el tenant coincide
                    token_tenant = user_info.get("tenant_id")
                    if token_tenant and token_tenant != tenant_id:
                        logger.warning(f"Token refresh: tenant mismatch {tenant_id} vs {token_tenant}")
                        request.session.clear()
                        return False
                
                logger.debug(f"Token refrescado correctamente para tenant {tenant_id}")
                return True
            else:
                logger.warning(f"Error al refrescar token para tenant {tenant_id}")
                request.session.clear()
                return False
                
        except Exception as e:
            logger.error(f"Error al refrescar token para tenant {tenant_id}: {str(e)}")
            request.session.clear()
            return False
    
    async def is_authenticated(self, request: Request) -> bool:
        """
        Verifica si el usuario está autenticado y pertenece al tenant actual
        
        Args:
            request: Request de FastAPI
            
        Returns:
            bool: True si está autenticado
        """
        # Verificar si hay sesión activa
        if not request.session.get("authenticated", False):
            return False
        
        access_token = request.session.get("access_token")
        if not access_token:
            return False
        
        # ✅ NUEVO: Verificar tenant del usuario vs tenant actual
        current_tenant = TenantContextManager.get_tenant_from_request(request)
        session_tenant = request.session.get("tenant_id")
        
        if session_tenant and session_tenant != current_tenant:
            logger.warning(f"Tenant mismatch en sesión: {session_tenant} vs {current_tenant}")
            request.session.clear()
            return False
        
        # Verificar si el token ha expirado
        if self._is_token_expired(access_token):
            # Intentar refrescar el token
            if await self.refresh_token(request):
                return True
            else:
                return False
        
        return True
    
    async def get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Obtiene el usuario actual de la sesión con validación de tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Optional[Dict[str, Any]]: Datos del usuario actual
        """
        if not await self.is_authenticated(request):
            return None
        
        user_data = request.session.get("user_data")
        
        # ✅ NUEVO: Agregar información del tenant actual
        if user_data:
            current_tenant = TenantContextManager.get_tenant_from_request(request)
            user_data["current_tenant"] = current_tenant
        
        return user_data
    
    async def create_session(self, request: Request, login_data: Dict[str, Any], tenant_id: str):
        """
        Crea una nueva sesión de usuario con información del tenant
        
        Args:
            request: Request de FastAPI
            login_data: Datos del login exitoso
            tenant_id: ID del tenant
        """
        # Guardar tokens
        request.session["access_token"] = login_data["access_token"]
        request.session["refresh_token"] = login_data["refresh_token"]
        request.session["token_type"] = login_data["token_type"]
        
        # ✅ NUEVO: Guardar información del tenant
        request.session["tenant_id"] = tenant_id
        
        # Decodificar y guardar información del usuario
        user_info = self._decode_token(login_data["access_token"])
        if user_info:
            request.session["user_data"] = user_info
            request.session["user_id"] = user_info.get("sub")
            request.session["username"] = user_info.get("username")
            request.session["user_roles"] = user_info.get("roles", [])
            
            # ✅ NUEVO: Validar tenant del usuario
            user_tenant = user_info.get("tenant_id")
            if user_tenant and user_tenant != tenant_id:
                logger.error(f"Token tenant mismatch: {user_tenant} vs {tenant_id}")
                request.session.clear()
                raise ValueError("Tenant mismatch en token")
        
        # Marcar como autenticado
        request.session["authenticated"] = True
        request.session["login_time"] = datetime.now().isoformat()
        
        # ✅ NUEVO: Información adicional de la sesión
        request.session["login_tenant"] = tenant_id
        request.session["session_id"] = login_data.get("session_id", "")
    
    def get_auth_headers(self, request: Request) -> Dict[str, str]:
        """
        Obtiene los headers de autorización para peticiones a la API incluyendo tenant
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Dict[str, str]: Headers de autorización
        """
        access_token = request.session.get("access_token")
        tenant_id = TenantContextManager.get_tenant_from_request(request)
        
        headers = {"Content-Type": "application/json"}
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        # ✅ NUEVO: Siempre incluir tenant en headers
        headers["X-Tenant-ID"] = tenant_id
        
        return headers
    
    def has_role(self, request: Request, role: str) -> bool:
        """
        Verifica si el usuario tiene un rol específico
        
        Args:
            request: Request de FastAPI
            role: Nombre del rol
            
        Returns:
            bool: True si tiene el rol
        """
        user_roles = request.session.get("user_roles", [])
        return role in user_roles
    
    def has_any_role(self, request: Request, roles: list) -> bool:
        """
        Verifica si el usuario tiene alguno de los roles especificados
        
        Args:
            request: Request de FastAPI
            roles: Lista de roles
            
        Returns:
            bool: True si tiene algún rol
        """
        user_roles = request.session.get("user_roles", [])
        return any(role in user_roles for role in roles)
    
    def is_admin(self, request: Request) -> bool:
        """
        Verifica si el usuario es administrador
        
        Args:
            request: Request de FastAPI
            
        Returns:
            bool: True si es administrador
        """
        return self.has_any_role(request, settings.ADMIN_ROLES)
    
    def get_session_tenant(self, request: Request) -> str:
        """
        Obtiene el tenant de la sesión actual
        
        Args:
            request: Request de FastAPI
            
        Returns:
            str: ID del tenant de la sesión
        """
        return request.session.get("tenant_id", "default")
    
    def _decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodifica un token JWT sin verificar la firma
        
        Args:
            token: Token a decodificar
            
        Returns:
            Optional[Dict[str, Any]]: Payload del token o None
        """
        try:
            # Decodificar sin verificar (solo para obtener información)
            payload = jwt.get_unverified_claims(token)
            return payload
        except JWTError:
            return None
    
    def _is_token_expired(self, token: str) -> bool:
        """
        Verifica si el token ha expirado
        
        Args:
            token: Token a verificar
            
        Returns:
            bool: True si ha expirado
        """
        try:
            payload = self._decode_token(token)
            if not payload:
                return True
            
            exp_timestamp = payload.get("exp")
            if not exp_timestamp:
                return True
            
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            return datetime.now() >= exp_datetime
            
        except Exception:
            return True
"""
Servicio de autenticación para FastAPI frontend
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

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.auth_api_url = settings.AUTH_API_URL
        self.client = httpx.AsyncClient(timeout=settings.API_TIMEOUT)
    
    async def login(self, username: str, password: str, remember_me: bool = False) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Realiza el login del usuario contra la API de auth
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            remember_me: Recordar sesión
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (éxito, datos_usuario, mensaje_error)
        """
        try:
            login_data = {
                "username": username,
                "password": password,
                "remember_me": remember_me
            }
            
            response = await self.client.post(
                f"{self.auth_api_url}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Usuario {username} autenticado correctamente")
                return True, data, None
            else:
                error_data = response.json()
                error_msg = error_data.get("detail", "Error de autenticación")
                logger.warning(f"Error de login para {username}: {error_msg}")
                return False, None, error_msg
                
        except httpx.RequestError as e:
            error_msg = f"Error de conexión: {str(e)}"
            logger.error(error_msg)
            return False, None, "Error de conexión con el servidor"
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg)
            return False, None, "Error inesperado"
    
    async def logout(self, request: Request) -> bool:
        """
        Cierra la sesión del usuario
        
        Args:
            request: Request de FastAPI
            
        Returns:
            bool: True si el logout fue exitoso
        """
        try:
            # Obtener refresh token de la sesión
            refresh_token = request.session.get("refresh_token")
            
            if refresh_token:
                # Revocar el token en el servidor
                logout_data = {"refresh_token": refresh_token}
                await self.client.post(
                    f"{self.auth_api_url}/auth/logout",
                    json=logout_data
                )
            
            # Limpiar sesión
            request.session.clear()
            logger.info("Usuario desconectado")
            return True
            
        except Exception as e:
            logger.error(f"Error durante logout: {str(e)}")
            # Limpiar sesión aunque haya error
            request.session.clear()
            return True
    
    async def refresh_token(self, request: Request) -> bool:
        """
        Refresca el token de acceso
        
        Args:
            request: Request de FastAPI
            
        Returns:
            bool: True si el refresh fue exitoso
        """
        try:
            refresh_token = request.session.get("refresh_token")
            if not refresh_token:
                return False
            
            refresh_data = {"refresh_token": refresh_token}
            response = await self.client.post(
                f"{self.auth_api_url}/auth/refresh-token",
                json=refresh_data
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
                
                logger.debug("Token refrescado correctamente")
                return True
            else:
                logger.warning("Error al refrescar token")
                request.session.clear()
                return False
                
        except Exception as e:
            logger.error(f"Error al refrescar token: {str(e)}")
            request.session.clear()
            return False
    
    async def is_authenticated(self, request: Request) -> bool:
        """
        Verifica si el usuario está autenticado
        
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
        Obtiene el usuario actual de la sesión
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Optional[Dict[str, Any]]: Datos del usuario actual
        """
        if not await self.is_authenticated(request):
            return None
        
        return request.session.get("user_data")
    
    async def create_session(self, request: Request, login_data: Dict[str, Any]):
        """
        Crea una nueva sesión de usuario
        
        Args:
            request: Request de FastAPI
            login_data: Datos del login exitoso
        """
        # Guardar tokens
        request.session["access_token"] = login_data["access_token"]
        request.session["refresh_token"] = login_data["refresh_token"]
        request.session["token_type"] = login_data["token_type"]
        
        # Decodificar y guardar información del usuario
        user_info = self._decode_token(login_data["access_token"])
        if user_info:
            request.session["user_data"] = user_info
            request.session["user_id"] = user_info.get("sub")
            request.session["username"] = user_info.get("username")
            request.session["user_roles"] = user_info.get("roles", [])
        
        # Marcar como autenticado
        request.session["authenticated"] = True
        request.session["login_time"] = datetime.now().isoformat()
    
    def get_auth_headers(self, request: Request) -> Dict[str, str]:
        """
        Obtiene los headers de autorización para peticiones a la API
        
        Args:
            request: Request de FastAPI
            
        Returns:
            Dict[str, str]: Headers de autorización
        """
        access_token = request.session.get("access_token")
        if access_token:
            return {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        return {"Content-Type": "application/json"}
    
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
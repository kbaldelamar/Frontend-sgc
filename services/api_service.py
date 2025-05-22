"""
Servicio para comunicarse con la API de datos (aplicación principal)
"""
import httpx
from typing import Dict, Any, Optional, List
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

class ApiService:
    def __init__(self):
        self.data_api_url = settings.DATA_API_URL
        self.client = httpx.AsyncClient(timeout=settings.API_TIMEOUT)
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                           params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Realiza una petición HTTP a la API de datos
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de la API
            data: Datos para el body de la petición
            params: Parámetros de query
            headers: Headers adicionales
            
        Returns:
            Optional[Dict[str, Any]]: Respuesta de la API o None si hay error
        """
        try:
            url = f"{self.data_api_url}/{endpoint.lstrip('/')}"
            
            # Headers por defecto
            default_headers = {"Content-Type": "application/json"}
            if headers:
                default_headers.update(headers)
            
            # Realizar petición según el método
            if method.upper() == "GET":
                response = await self.client.get(url, headers=default_headers, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, headers=default_headers, params=params)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, headers=default_headers, params=params)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=default_headers, params=params)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            # Manejar respuesta
            if response.status_code >= 200 and response.status_code < 300:
                if response.text:
                    return response.json()
                else:
                    return {"success": True}
            else:
                logger.warning(f"Error {response.status_code} en API de datos: {response.text}")
                return None
                
        except httpx.RequestError as e:
            logger.error(f"Error de conexión con la API de datos: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en API de datos: {str(e)}")
            return None
    
    # Métodos específicos para obtener datos del dashboard
    
    async def get_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas generales del sistema
        
        Returns:
            Optional[Dict[str, Any]]: Estadísticas del sistema
        """
        return await self._make_request("GET", "/statistics")
    
    async def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos específicos para el dashboard
        
        Returns:
            Optional[Dict[str, Any]]: Datos del dashboard
        """
        return await self._make_request("GET", "/dashboard")
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el perfil de un usuario específico
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Optional[Dict[str, Any]]: Datos del perfil del usuario
        """
        return await self._make_request("GET", f"/users/{user_id}")
    
    async def get_system_health(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de salud del sistema
        
        Returns:
            Optional[Dict[str, Any]]: Estado del sistema
        """
        return await self._make_request("GET", "/health")
    
    # Métodos para obtener datos con autenticación (cuando la implementes)
    
    async def get_authenticated_data(self, endpoint: str, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos que requieren autenticación
        
        Args:
            endpoint: Endpoint a consultar
            access_token: Token de acceso del usuario
            
        Returns:
            Optional[Dict[str, Any]]: Datos autenticados
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"  
        }
        
        return await self._make_request("GET", endpoint, headers=headers)
    
    async def get_user_data(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos específicos del usuario autenticado
        
        Args:
            access_token: Token de acceso del usuario
            
        Returns:
            Optional[Dict[str, Any]]: Datos del usuario
        """
        return await self.get_authenticated_data("/user/profile", access_token)
    
    async def get_user_statistics(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas específicas del usuario
        
        Args:
            access_token: Token de acceso del usuario
            
        Returns:
            Optional[Dict[str, Any]]: Estadísticas del usuario
        """
        return await self.get_authenticated_data("/user/statistics", access_token)
    
    # Método para cerrar el cliente HTTP
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
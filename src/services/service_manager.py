import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ServiceManagerError(Exception):
    """Exception raised for service manager errors."""
    pass


class ServiceManager:
    """Manages the lifecycle of all services in the application."""
    
    def __init__(self):
        """Initialize the service manager."""
        self._services: Dict[str, Any] = {}
        self._started: bool = False
    
    async def register_service(self, name: str, service: Any) -> None:
        """Register a service with the manager."""
        if name in self._services:
            raise ServiceManagerError(f"Service already registered: {name}")
        
        self._services[name] = service
        logger.info(f"Service registered: {name}")
    
    def get_service(self, name: str) -> Any:
        """Get a registered service by name."""
        if name not in self._services:
            raise ServiceManagerError(f"Service not found: {name}")
        
        return self._services[name]
    
    async def start_all_services(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Start all registered services."""
        if self._started:
            logger.warning("Services already started")
            return
        
        config = config or {}
        
        for name, service in self._services.items():
            try:
                logger.info(f"Starting service: {name}")
                
                # Check if service has initialize method
                if hasattr(service, 'initialize') and callable(service.initialize):
                    service_config = config.get(name, {})
                    await service.initialize(service_config)
                
                logger.info(f"Service started successfully: {name}")
                
            except Exception as e:
                logger.error(f"Failed to start service {name}: {str(e)}")
                raise ServiceManagerError(f"Failed to start service {name}: {str(e)}")
        
        self._started = True
        logger.info("All services started successfully")
    
    async def stop_all_services(self) -> None:
        """Stop all registered services."""
        if not self._started:
            logger.warning("Services not started")
            return
        
        for name, service in self._services.items():
            try:
                logger.info(f"Stopping service: {name}")
                
                # Check if service has shutdown method
                if hasattr(service, 'shutdown') and callable(service.shutdown):
                    await service.shutdown()
                
                logger.info(f"Service stopped successfully: {name}")
                
            except Exception as e:
                logger.error(f"Failed to stop service {name}: {str(e)}")
                # Continue stopping other services even if one fails
        
        self._started = False
        logger.info("All services stopped")
    
    async def health_check_all_services(self) -> Dict[str, Any]:
        """Check health of all registered services."""
        health_status = {}
        
        for name, service in self._services.items():
            try:
                if hasattr(service, 'health_check') and callable(service.health_check):
                    health_status[name] = await service.health_check()
                else:
                    health_status[name] = {"status": "unknown", "message": "No health check method"}
                    
            except Exception as e:
                health_status[name] = {"status": "error", "message": str(e)}
        
        return health_status
    
    async def health_check_service(self, name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        if name not in self._services:
            raise ServiceManagerError(f"Service not found: {name}")
        
        service = self._services[name]
        
        if hasattr(service, 'health_check') and callable(service.health_check):
            return await service.health_check()
        else:
            return {"status": "unknown", "message": "No health check method"}
    
    def list_services(self) -> list:
        """List all registered service names."""
        return list(self._services.keys())
    
    async def remove_service(self, name: str) -> None:
        """Remove a service from the manager."""
        if name not in self._services:
            raise ServiceManagerError(f"Service not found: {name}")
        
        service = self._services[name]
        
        # Try to shutdown the service if it has a shutdown method
        if hasattr(service, 'shutdown') and callable(service.shutdown):
            try:
                await service.shutdown()
            except Exception as e:
                logger.warning(f"Failed to shutdown service {name}: {str(e)}")
        
        del self._services[name]
        logger.info(f"Service removed: {name}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service manager."""
        return {
            "service_count": len(self._services),
            "services": list(self._services.keys()),
            "started": self._started
        } 
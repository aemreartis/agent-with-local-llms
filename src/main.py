import asyncio
import time
import logging
from typing import Dict, Any, Optional

from src.config.config_loader import ConfigLoader
from src.services.application_assembler import ApplicationAssembler

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Exception raised for application errors."""
    pass


class Application:
    """Main application class that orchestrates the entire system."""
    
    def __init__(self):
        """Initialize the application."""
        self._config_loader = ConfigLoader()
        self._assembler = ApplicationAssembler()
        self._service_manager = None
        self._providers = {}
        self._orchestrators = {}
        self._started_at = None
        self._status = "stopped"
    
    async def start(self, config_path: str) -> None:
        """Start the application with the given configuration."""
        try:
            logger.info(f"Starting application with config: {config_path}")
            
            # Load configuration
            config = await self._load_configuration(config_path)
            
            # Assemble application
            assembly_result = await self._assemble_application(config)
            
            # Store components
            self._providers = assembly_result['providers']
            self._orchestrators = assembly_result['orchestrators']
            self._service_manager = assembly_result['service_manager']
            
            # Start services
            await self._start_services()
            
            self._started_at = time.time()
            self._status = "running"
            
            logger.info("Application started successfully")
            
        except Exception as e:
            self._status = "failed"
            logger.error(f"Failed to start application: {str(e)}")
            if isinstance(e, ApplicationError):
                raise
            raise ApplicationError(f"Failed to start application: {str(e)}")
    
    async def stop(self) -> None:
        """Stop the application."""
        try:
            logger.info("Stopping application")
            
            if self._service_manager:
                await self._service_manager.stop_all_services()
            
            self._status = "stopped"
            logger.info("Application stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping application: {str(e)}")
            # Don't raise exception during shutdown
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the application."""
        health_status = {
            "overall_health": False,
            "services": {},
            "status": self._status,
            "uptime_seconds": 0
        }
        
        if self._started_at:
            health_status["uptime_seconds"] = time.time() - self._started_at
        
        if self._service_manager:
            try:
                services_health = await self._service_manager.health_check_all_services()
                health_status["services"] = services_health
                
                # Determine overall health
                all_healthy = True
                for service_name, service_health in services_health.items():
                    if isinstance(service_health, dict):
                        if service_health.get("status") != "healthy":
                            all_healthy = False
                    elif not service_health:  # Boolean health check
                        all_healthy = False
                
                health_status["overall_health"] = all_healthy
                
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                health_status["overall_health"] = False
                health_status["error"] = str(e)
        else:
            health_status["overall_health"] = False
        
        return health_status
    
    async def _load_configuration(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            return self._config_loader.load_config(config_path)
        except Exception as e:
            if "not found" in str(e).lower():
                raise ApplicationError(f"Configuration file not found: {config_path}")
            raise ApplicationError(f"Failed to load configuration: {str(e)}")
    
    async def _assemble_application(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble the application from configuration."""
        try:
            return await self._assembler.assemble_application(config)
        except Exception as e:
            raise ApplicationError(f"Failed to assemble application: {str(e)}")
    
    async def _start_services(self) -> None:
        """Start all services."""
        try:
            if self._service_manager:
                await self._service_manager.start_all_services()
        except Exception as e:
            raise ApplicationError(f"Failed to start services: {str(e)}")
    
    def get_application_info(self) -> Dict[str, Any]:
        """Get information about the application."""
        info = {
            "app_name": "Agentic RAG System",
            "version": "1.0.0",
            "status": self._status,
            "started_at": self._started_at,
            "uptime_seconds": 0
        }
        
        if self._started_at:
            info["uptime_seconds"] = time.time() - self._started_at
        
        if self._providers:
            info["providers"] = list(self._providers.keys())
        
        if self._orchestrators:
            info["orchestrators"] = list(self._orchestrators.keys())
        
        return info
    
    def get_service(self, service_name: str) -> Any:
        """Get a specific service by name."""
        if service_name in self._orchestrators:
            return self._orchestrators[service_name]
        elif service_name in self._providers:
            return self._providers[service_name]
        else:
            raise ApplicationError(f"Service not found: {service_name}")


# Main entry point for running the application
async def main():
    """Main entry point for the application."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python -m src.main <config_file>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    app = Application()
    
    try:
        await app.start(config_path)
        print("Application started successfully")
        
        # Keep the application running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        await app.stop()
        print("Application stopped")
    except Exception as e:
        print(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 
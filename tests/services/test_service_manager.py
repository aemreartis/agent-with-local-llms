import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.services.service_manager import ServiceManager, ServiceManagerError


class TestServiceManager:
    """Test cases for the service manager."""

    def test_service_manager_initialization(self):
        """Test ServiceManager can be initialized."""
        manager = ServiceManager()
        assert manager is not None
        assert hasattr(manager, 'register_service')
        assert hasattr(manager, 'get_service')
        assert hasattr(manager, 'start_all_services')
        assert hasattr(manager, 'stop_all_services')

    @pytest.mark.asyncio
    async def test_register_service_success(self):
        """Test successful service registration."""
        manager = ServiceManager()
        mock_service = Mock()
        mock_service.name = "test-service"
        
        await manager.register_service("test-service", mock_service)
        
        assert "test-service" in manager._services
        assert manager._services["test-service"] == mock_service

    @pytest.mark.asyncio
    async def test_register_service_duplicate(self):
        """Test handling of duplicate service registration."""
        manager = ServiceManager()
        mock_service1 = Mock()
        mock_service1.name = "test-service"
        mock_service2 = Mock()
        mock_service2.name = "test-service"
        
        await manager.register_service("test-service", mock_service1)
        
        with pytest.raises(ServiceManagerError, match="Service already registered"):
            await manager.register_service("test-service", mock_service2)

    @pytest.mark.asyncio
    async def test_get_service_success(self):
        """Test successful service retrieval."""
        manager = ServiceManager()
        mock_service = Mock()
        mock_service.name = "test-service"
        
        await manager.register_service("test-service", mock_service)
        retrieved_service = manager.get_service("test-service")
        
        assert retrieved_service == mock_service

    @pytest.mark.asyncio
    async def test_get_service_not_found(self):
        """Test handling of service not found."""
        manager = ServiceManager()
        
        with pytest.raises(ServiceManagerError, match="Service not found"):
            manager.get_service("nonexistent-service")

    @pytest.mark.asyncio
    async def test_start_all_services_success(self):
        """Test successful startup of all services."""
        manager = ServiceManager()
        
        # Create mock services with initialize methods
        mock_service1 = AsyncMock()
        mock_service1.name = "service1"
        mock_service1.initialize = AsyncMock()
        
        mock_service2 = AsyncMock()
        mock_service2.name = "service2"
        mock_service2.initialize = AsyncMock()
        
        await manager.register_service("service1", mock_service1)
        await manager.register_service("service2", mock_service2)
        
        await manager.start_all_services()
        
        # Verify initialize was called on both services
        mock_service1.initialize.assert_called_once()
        mock_service2.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_all_services_with_config(self):
        """Test startup of services with configuration."""
        manager = ServiceManager()
        
        mock_service = AsyncMock()
        mock_service.name = "test-service"
        mock_service.initialize = AsyncMock()
        
        await manager.register_service("test-service", mock_service)
        
        config = {"test-service": {"setting": "value"}}
        await manager.start_all_services(config)
        
        # Verify initialize was called with config
        mock_service.initialize.assert_called_once_with({"setting": "value"})

    @pytest.mark.asyncio
    async def test_start_all_services_failure(self):
        """Test handling of service startup failure."""
        manager = ServiceManager()
        
        mock_service = AsyncMock()
        mock_service.name = "failing-service"
        mock_service.initialize = AsyncMock(side_effect=Exception("Startup failed"))
        
        await manager.register_service("failing-service", mock_service)
        
        with pytest.raises(ServiceManagerError, match="Failed to start service"):
            await manager.start_all_services()

    @pytest.mark.asyncio
    async def test_stop_all_services_success(self):
        """Test successful shutdown of all services."""
        manager = ServiceManager()
        
        # Create mock services with shutdown methods
        mock_service1 = AsyncMock()
        mock_service1.name = "service1"
        mock_service1.shutdown = AsyncMock()
        
        mock_service2 = AsyncMock()
        mock_service2.name = "service2"
        mock_service2.shutdown = AsyncMock()
        
        await manager.register_service("service1", mock_service1)
        await manager.register_service("service2", mock_service2)
        
        # Start services first
        await manager.start_all_services()
        
        await manager.stop_all_services()
        
        # Verify shutdown was called on both services
        mock_service1.shutdown.assert_called_once()
        mock_service2.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_all_services_failure(self):
        """Test handling of service shutdown failure."""
        manager = ServiceManager()
        
        mock_service = AsyncMock()
        mock_service.name = "failing-service"
        mock_service.shutdown = AsyncMock(side_effect=Exception("Shutdown failed"))
        
        await manager.register_service("failing-service", mock_service)
        
        # Start services first
        await manager.start_all_services()
        
        # Should not raise exception, but log the error
        await manager.stop_all_services()
        
        # Verify shutdown was attempted
        mock_service.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_all_services(self):
        """Test health check of all services."""
        manager = ServiceManager()
        
        # Create mock services with health_check methods
        mock_service1 = AsyncMock()
        mock_service1.name = "service1"
        mock_service1.health_check = AsyncMock(return_value={"status": "healthy"})
        
        mock_service2 = AsyncMock()
        mock_service2.name = "service2"
        mock_service2.health_check = AsyncMock(return_value={"status": "unhealthy"})
        
        await manager.register_service("service1", mock_service1)
        await manager.register_service("service2", mock_service2)
        
        health_status = await manager.health_check_all_services()
        
        assert "service1" in health_status
        assert "service2" in health_status
        assert health_status["service1"]["status"] == "healthy"
        assert health_status["service2"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_service_not_found(self):
        """Test health check of non-existent service."""
        manager = ServiceManager()
        
        with pytest.raises(ServiceManagerError, match="Service not found"):
            await manager.health_check_service("nonexistent-service")

    @pytest.mark.asyncio
    async def test_health_check_service_success(self):
        """Test successful health check of specific service."""
        manager = ServiceManager()
        
        mock_service = AsyncMock()
        mock_service.name = "test-service"
        mock_service.health_check = AsyncMock(return_value={"status": "healthy", "details": "all good"})
        
        await manager.register_service("test-service", mock_service)
        
        health_status = await manager.health_check_service("test-service")
        
        assert health_status["status"] == "healthy"
        assert health_status["details"] == "all good"

    def test_list_services(self):
        """Test listing all registered services."""
        manager = ServiceManager()
        
        # Should be empty initially
        services = manager.list_services()
        assert len(services) == 0
        
        # Add a service
        mock_service = Mock()
        mock_service.name = "test-service"
        manager._services["test-service"] = mock_service
        
        services = manager.list_services()
        assert len(services) == 1
        assert "test-service" in services

    @pytest.mark.asyncio
    async def test_remove_service_success(self):
        """Test successful service removal."""
        manager = ServiceManager()
        
        mock_service = AsyncMock()
        mock_service.name = "test-service"
        mock_service.shutdown = AsyncMock()
        
        await manager.register_service("test-service", mock_service)
        assert "test-service" in manager._services
        
        await manager.remove_service("test-service")
        assert "test-service" not in manager._services
        mock_service.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_service_not_found(self):
        """Test removal of non-existent service."""
        manager = ServiceManager()
        
        with pytest.raises(ServiceManagerError, match="Service not found"):
            await manager.remove_service("nonexistent-service")

    @pytest.mark.asyncio
    async def test_service_lifecycle_workflow(self):
        """Test complete service lifecycle workflow."""
        manager = ServiceManager()
        
        # Create mock service
        mock_service = AsyncMock()
        mock_service.name = "workflow-service"
        mock_service.initialize = AsyncMock()
        mock_service.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_service.shutdown = AsyncMock()
        
        # Register service
        await manager.register_service("workflow-service", mock_service)
        assert "workflow-service" in manager.list_services()
        
        # Start service
        config = {"workflow-service": {"setting": "value"}}
        await manager.start_all_services(config)
        mock_service.initialize.assert_called_once_with({"setting": "value"})
        
        # Check health
        health_status = await manager.health_check_service("workflow-service")
        assert health_status["status"] == "healthy"
        
        # Stop service
        await manager.stop_all_services()
        mock_service.shutdown.assert_called_once()
        
        # Remove service
        await manager.remove_service("workflow-service")
        assert "workflow-service" not in manager.list_services()

    def test_get_service_info(self):
        """Test getting service manager information."""
        manager = ServiceManager()
        
        info = manager.get_service_info()
        
        assert "service_count" in info
        assert "services" in info
        assert info["service_count"] == 0
        assert len(info["services"]) == 0
        
        # Add a service and check again
        mock_service = Mock()
        mock_service.name = "test-service"
        manager._services["test-service"] = mock_service
        
        info = manager.get_service_info()
        assert info["service_count"] == 1
        assert "test-service" in info["services"] 
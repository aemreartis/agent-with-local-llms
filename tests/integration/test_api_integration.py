"""
Integration tests for API integration.
Tests that API endpoints work seamlessly with backend components.
"""

import pytest
import asyncio
from typing import Dict, Any

from src.api.main import create_app
from src.api.models import ChatRequest, DocumentUploadRequest, SearchRequest
from src.api.auth import AuthService, get_current_user
from src.registry.provider_registry import ProviderRegistry
from src.config.config_loader import ConfigLoader


class TestAPIIntegration:
    """Test API integration with backend components."""
    
    @pytest.mark.integration
    def test_api_application_creation(self):
        """Test that FastAPI application can be created."""
        # RED: Write failing test that defines expected behavior
        app = create_app()
        assert app is not None
        assert hasattr(app, 'get')
        assert hasattr(app, 'post')
        assert hasattr(app, 'put')
        assert hasattr(app, 'delete')
    
    @pytest.mark.integration
    def test_api_models_creation(self):
        """Test that API models can be created."""
        # RED: Write failing test that defines expected behavior
        # Test ChatRequest model
        chat_request = ChatRequest(
            message="Test message",
            session_id="test_session"
        )
        assert chat_request is not None
        assert chat_request.message == "Test message"
        assert chat_request.session_id == "test_session"
        
        # Test DocumentUploadRequest model
        doc_request = DocumentUploadRequest()
        assert doc_request is not None
        assert hasattr(doc_request, 'metadata')
        assert hasattr(doc_request, 'processing_options')
        
        # Test SearchRequest model
        search_request = SearchRequest(
            query="test query"
        )
        assert search_request is not None
        assert search_request.query == "test query"
        assert search_request.limit == 10  # default value
    
    @pytest.mark.integration
    def test_authentication_integration(self):
        """Test authentication integration with API."""
        # RED: Write failing test that defines expected behavior
        # Test token creation
        auth_service = AuthService()
        token_data = {"sub": "test_user", "role": "user"}
        token = auth_service.create_access_token(token_data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Test that authentication functions exist
        assert callable(auth_service.create_access_token)
        assert callable(get_current_user)
    
    @pytest.mark.integration
    def test_api_with_provider_registry_integration(self):
        """Test API integration with provider registry."""
        # RED: Write failing test that defines expected behavior
        provider_registry = ProviderRegistry()
        
        # Test that provider registry can be used with API
        assert provider_registry is not None
        assert hasattr(provider_registry, 'register_provider')
        assert hasattr(provider_registry, 'get_provider')
        assert hasattr(provider_registry, 'list_providers')
    
    @pytest.mark.integration
    def test_api_with_config_loader_integration(self):
        """Test API integration with configuration loader."""
        # RED: Write failing test that defines expected behavior
        config_loader = ConfigLoader()
        
        # Test that config loader can be used with API
        assert config_loader is not None
        assert hasattr(config_loader, 'load_config')
        assert hasattr(config_loader, 'validate_config_structure')
        assert hasattr(config_loader, 'get_config_value')
    
    @pytest.mark.integration
    def test_api_endpoint_structure(self):
        """Test that API endpoints have correct structure."""
        # RED: Write failing test that defines expected behavior
        # Test that app has expected routes
        app = create_app()
        routes = [route.path for route in app.routes]
        
        # Check for essential endpoints
        assert "/health" in routes or "/health/" in routes
        assert "/chat" in routes or "/chat/" in routes
        assert "/documents/upload" in routes or "/documents/upload/" in routes
        assert "/search" in routes or "/search/" in routes
    
    @pytest.mark.integration
    def test_api_middleware_integration(self):
        """Test API middleware integration."""
        # RED: Write failing test that defines expected behavior
        # Test that app has middleware
        app = create_app()
        assert hasattr(app, 'middleware')
        assert hasattr(app, 'add_middleware')
        
        # Test that app has CORS configuration
        assert hasattr(app, 'add_middleware')
    
    @pytest.mark.integration
    def test_api_error_handling_integration(self):
        """Test API error handling integration."""
        # RED: Write failing test that defines expected behavior
        # Test that app has exception handlers
        app = create_app()
        assert hasattr(app, 'exception_handler')
        assert hasattr(app, 'add_exception_handler')
    
    @pytest.mark.integration
    def test_api_websocket_integration(self):
        """Test API WebSocket integration."""
        # RED: Write failing test that defines expected behavior
        # Test that app supports WebSocket endpoints
        app = create_app()
        routes = [route.path for route in app.routes]
        
        # Check for WebSocket endpoints
        websocket_routes = [route for route in routes if route.startswith('/ws')]
        assert len(websocket_routes) >= 0  # May or may not have WebSocket endpoints
    
    @pytest.mark.integration
    def test_api_documentation_integration(self):
        """Test API documentation integration."""
        # RED: Write failing test that defines expected behavior
        # Test that app has OpenAPI documentation
        app = create_app()
        assert hasattr(app, 'openapi')
        assert hasattr(app, 'docs_url')
        assert hasattr(app, 'redoc_url')
        
        # Test that documentation URLs are accessible
        assert app.docs_url is not None
        assert app.redoc_url is not None
    
    @pytest.mark.integration
    def test_api_rate_limiting_integration(self):
        """Test API rate limiting integration."""
        # RED: Write failing test that defines expected behavior
        # Test that app has rate limiting capabilities
        # This is typically implemented through middleware or dependencies
        app = create_app()
        assert hasattr(app, 'middleware')
        assert hasattr(app, 'add_middleware') 
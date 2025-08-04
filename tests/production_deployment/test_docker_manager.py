"""
Production Deployment Tests: Docker Manager

Tests Docker deployment manager functionality including validation,
build processes, orchestration, and health checks following TDD methodology.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, List, Any, Optional

from src.deployment.docker_manager import DockerManager, DockerService, DockerBuildConfig


class TestDockerManager:
    """Test Docker deployment manager functionality"""
    
    @pytest.fixture
    def docker_manager(self):
        """Create Docker manager instance for testing"""
        return DockerManager()
    
    @pytest.fixture
    def sample_dockerfile_content(self):
        """Sample Dockerfile content for testing"""
        return """
# Multi-stage build for production
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY configs/ ./configs/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \\
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    @pytest.fixture
    def sample_compose_config(self):
        """Sample Docker Compose configuration for testing"""
        return {
            "version": "3.8",
            "services": {
                "fastapi-app": {
                    "build": {
                        "context": ".",
                        "dockerfile": "Dockerfile"
                    },
                    "ports": ["8000:8000"],
                    "environment": [
                        "APP_ENV=production",
                        "LOG_LEVEL=INFO"
                    ],
                    "volumes": [
                        "./data:/app/data",
                        "./logs:/app/logs"
                    ],
                    "depends_on": ["postgresql", "redis"],
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                },
                "postgresql": {
                    "image": "postgres:15-alpine",
                    "ports": ["5432:5432"],
                    "environment": [
                        "POSTGRES_DB=agentic_rag",
                        "POSTGRES_USER=rag_user",
                        "POSTGRES_PASSWORD=secure_password"
                    ],
                    "volumes": ["postgres_data:/var/lib/postgresql/data"]
                }
            },
            "volumes": {
                "postgres_data": None
            }
        }
    
    def test_docker_manager_initialization(self, docker_manager):
        """Test Docker manager initialization"""
        assert docker_manager.project_root == Path(".")
        assert docker_manager.compose_file == Path("docker-compose.yml")
        assert docker_manager.dockerfile == Path("Dockerfile")
    
    def test_validate_dockerfile_success(self, docker_manager, sample_dockerfile_content):
        """Test successful Dockerfile validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dockerfile', delete=False) as f:
            f.write(sample_dockerfile_content)
            dockerfile_path = f.name
        
        try:
            result = docker_manager.validate_dockerfile(dockerfile_path)
            
            assert result["valid"] is True
            assert len(result["issues"]) == 0
            assert len(result["best_practices"]) >= 3
            
            # Check for specific best practices
            best_practices = result["best_practices"]
            assert any("Non-root user" in practice for practice in best_practices)
            assert any("Health check" in practice for practice in best_practices)
            assert any("Python optimization" in practice for practice in best_practices)
            assert any("Multi-stage build" in practice for practice in best_practices)
            
        finally:
            os.unlink(dockerfile_path)
    
    def test_validate_dockerfile_failure(self, docker_manager):
        """Test Dockerfile validation with missing elements"""
        invalid_dockerfile = """
# Invalid Dockerfile
RUN echo "test"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dockerfile', delete=False) as f:
            f.write(invalid_dockerfile)
            dockerfile_path = f.name
        
        try:
            result = docker_manager.validate_dockerfile(dockerfile_path)
            
            assert result["valid"] is False
            assert len(result["issues"]) >= 1
            
            # Should have issues for missing elements
            issues = result["issues"]
            assert any("FROM" in issue for issue in issues)
            assert any("WORKDIR" in issue for issue in issues)
            assert any("EXPOSE" in issue for issue in issues)
            
        finally:
            os.unlink(dockerfile_path)
    
    def test_validate_compose_config_success(self, docker_manager, sample_compose_config):
        """Test successful Docker Compose validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            import yaml
            yaml.dump(sample_compose_config, f)
            compose_path = f.name
        
        try:
            result = docker_manager.validate_compose_config(compose_path)
            
            assert result["valid"] is True
            assert len(result["issues"]) == 0
            assert len(result["services"]) == 2
            
            # Check service validations
            service_names = [service["name"] for service in result["services"]]
            assert "fastapi-app" in service_names
            assert "postgresql" in service_names
            
        finally:
            os.unlink(compose_path)
    
    def test_validate_compose_config_failure(self, docker_manager):
        """Test Docker Compose validation with invalid config"""
        invalid_config = {
            "services": {
                "invalid-service": {
                    "image": "test-image"
                    # Missing required fields
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            import yaml
            yaml.dump(invalid_config, f)
            compose_path = f.name
        
        try:
            result = docker_manager.validate_compose_config(compose_path)
            
            assert result["valid"] is False
            assert len(result["issues"]) >= 1
            
            # Should have issues for missing required fields
            service_validation = result["services"][0]
            assert service_validation["valid"] is False
            assert len(service_validation["issues"]) >= 1
            
        finally:
            os.unlink(compose_path)
    
    @patch('subprocess.run')
    def test_build_image_success(self, mock_run, docker_manager):
        """Test successful Docker image build"""
        # Mock successful build
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Successfully built image"
        mock_run.return_value.stderr = ""
        
        result = docker_manager.build_image(
            context=".",
            dockerfile="Dockerfile",
            tag="test-image:latest"
        )
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Successfully built" in result["stdout"]
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "docker"
        assert call_args[1] == "build"
        assert call_args[2] == "-t"
        assert call_args[3] == "test-image:latest"
    
    @patch('subprocess.run')
    def test_build_image_failure(self, mock_run, docker_manager):
        """Test Docker image build failure"""
        # Mock failed build
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Build failed"
        
        result = docker_manager.build_image(
            context=".",
            dockerfile="Dockerfile",
            tag="test-image:latest"
        )
        
        assert result["success"] is False
        assert result["returncode"] == 1
        assert "Build failed" in result["stderr"]
    
    @patch('subprocess.run')
    def test_build_compose_services_success(self, mock_run, docker_manager):
        """Test successful Docker Compose build"""
        # Mock successful build
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Successfully built all services"
        mock_run.return_value.stderr = ""
        
        result = docker_manager.build_compose_services(["fastapi-app"])
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Successfully built" in result["stdout"]
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "docker-compose"
        assert call_args[1] == "build"
        assert call_args[2] == "fastapi-app"
    
    @patch('subprocess.run')
    def test_start_services_success(self, mock_run, docker_manager):
        """Test successful service startup"""
        # Mock successful startup
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Services started successfully"
        mock_run.return_value.stderr = ""
        
        result = docker_manager.start_services(detached=True)
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Services started" in result["stdout"]
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "docker-compose"
        assert call_args[1] == "up"
        assert call_args[2] == "-d"
    
    @patch('subprocess.run')
    def test_stop_services_success(self, mock_run, docker_manager):
        """Test successful service shutdown"""
        # Mock successful shutdown
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Services stopped successfully"
        mock_run.return_value.stderr = ""
        
        result = docker_manager.stop_services()
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Services stopped" in result["stdout"]
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "docker-compose"
        assert call_args[1] == "down"
    
    @patch('subprocess.run')
    def test_get_service_status_success(self, mock_run, docker_manager):
        """Test successful service status retrieval"""
        # Mock successful status check
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "fastapi-app    Up   0.0.0.0:8000->8000/tcp"
        mock_run.return_value.stderr = ""
        
        result = docker_manager.get_service_status()
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "fastapi-app" in result["stdout"]
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "docker-compose"
        assert call_args[1] == "ps"
    
    @patch('subprocess.run')
    def test_check_service_health_success(self, mock_run, docker_manager):
        """Test successful service health check"""
        # Mock container ID retrieval
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="container123\n"),
            MagicMock(returncode=0, stdout="'healthy'\n")
        ]
        
        result = docker_manager.check_service_health("fastapi-app")
        
        assert result["success"] is True
        assert result["status"] == "healthy"
        assert result["container_id"] == "container123"
        
        # Verify commands were called correctly
        assert mock_run.call_count == 2
        
        # First call: get container ID
        first_call = mock_run.call_args_list[0][0][0]
        assert first_call[0] == "docker-compose"
        assert first_call[1] == "ps"
        assert first_call[2] == "-q"
        assert first_call[3] == "fastapi-app"
        
        # Second call: check health status
        second_call = mock_run.call_args_list[1][0][0]
        assert second_call[0] == "docker"
        assert second_call[1] == "inspect"
    
    @patch('subprocess.run')
    def test_check_service_health_not_running(self, mock_run, docker_manager):
        """Test service health check when service is not running"""
        # Mock service not running
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        
        result = docker_manager.check_service_health("fastapi-app")
        
        assert result["success"] is False
        assert result["status"] == "not_running"
        assert "Service not running" in result["error"]
    
    @patch('subprocess.run')
    def test_get_service_logs_success(self, mock_run, docker_manager):
        """Test successful service logs retrieval"""
        # Mock successful logs retrieval
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "2024-01-01 10:00:00 INFO Application started"
        mock_run.return_value.stderr = ""
        
        result = docker_manager.get_service_logs("fastapi-app", lines=50)
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Application started" in result["stdout"]
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "docker-compose"
        assert call_args[1] == "logs"
        assert call_args[2] == "--tail"
        assert call_args[3] == "50"
        assert call_args[4] == "fastapi-app"
    
    @patch('subprocess.run')
    def test_restart_service_success(self, mock_run, docker_manager):
        """Test successful service restart"""
        # Mock successful restart
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "fastapi-app restarted"
        mock_run.return_value.stderr = ""
        
        result = docker_manager.restart_service("fastapi-app")
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "restarted" in result["stdout"]
        
        # Verify command was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "docker-compose"
        assert call_args[1] == "restart"
        assert call_args[2] == "fastapi-app"
    
    @patch('subprocess.run')
    def test_optimize_build_cache_success(self, mock_run, docker_manager):
        """Test successful build cache optimization"""
        # Mock successful cache optimization
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Pruned 5 images"),
            MagicMock(returncode=0, stdout="Pruned 3 containers")
        ]
        
        result = docker_manager.optimize_build_cache()
        
        assert result["success"] is True
        assert "Pruned 5 images" in result["images_pruned"]
        assert "Pruned 3 containers" in result["containers_pruned"]
        
        # Verify commands were called correctly
        assert mock_run.call_count == 2
        
        # First call: prune images
        first_call = mock_run.call_args_list[0][0][0]
        assert first_call[0] == "docker"
        assert first_call[1] == "image"
        assert first_call[2] == "prune"
        assert first_call[3] == "-f"
        
        # Second call: prune containers
        second_call = mock_run.call_args_list[1][0][0]
        assert second_call[0] == "docker"
        assert second_call[1] == "container"
        assert second_call[2] == "prune"
        assert second_call[3] == "-f"
    
    def test_generate_compose_config(self, docker_manager, sample_compose_config):
        """Test Docker Compose configuration generation"""
        result = docker_manager.generate_compose_config(sample_compose_config)
        
        assert isinstance(result, str)
        assert "version: '3.8'" in result
        assert "fastapi-app:" in result
        assert "postgresql:" in result
    
    def test_save_compose_config_success(self, docker_manager, sample_compose_config):
        """Test successful Docker Compose configuration save"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            compose_path = f.name
        
        try:
            result = docker_manager.save_compose_config(sample_compose_config, compose_path)
            
            assert result is True
            
            # Verify file was created and contains expected content
            with open(compose_path, 'r') as f:
                content = f.read()
                assert "version: '3.8'" in content
                assert "fastapi-app:" in content
                
        finally:
            os.unlink(compose_path)
    
    def test_save_compose_config_failure(self, docker_manager, sample_compose_config):
        """Test Docker Compose configuration save failure"""
        # Try to save to invalid path
        invalid_path = "/invalid/path/compose.yml"
        
        result = docker_manager.save_compose_config(sample_compose_config, invalid_path)
        
        assert result is False


class TestDockerService:
    """Test Docker service data class"""
    
    def test_docker_service_creation(self):
        """Test Docker service creation"""
        service = DockerService(
            name="test-service",
            image="test-image:latest",
            ports=["8000:8000"],
            environment={"APP_ENV": "production"},
            volumes=["./data:/app/data"],
            depends_on=["postgresql"],
            healthcheck={"test": ["CMD", "curl", "-f", "http://localhost:8000/health"]}
        )
        
        assert service.name == "test-service"
        assert service.image == "test-image:latest"
        assert service.ports == ["8000:8000"]
        assert service.environment == {"APP_ENV": "production"}
        assert service.volumes == ["./data:/app/data"]
        assert service.depends_on == ["postgresql"]
        assert service.healthcheck == {"test": ["CMD", "curl", "-f", "http://localhost:8000/health"]}


class TestDockerBuildConfig:
    """Test Docker build configuration data class"""
    
    def test_docker_build_config_creation(self):
        """Test Docker build configuration creation"""
        config = DockerBuildConfig(
            context=".",
            dockerfile="Dockerfile",
            args={"PYTHON_VERSION": "3.12", "APP_ENV": "production"},
            target="production"
        )
        
        assert config.context == "."
        assert config.dockerfile == "Dockerfile"
        assert config.args == {"PYTHON_VERSION": "3.12", "APP_ENV": "production"}
        assert config.target == "production" 
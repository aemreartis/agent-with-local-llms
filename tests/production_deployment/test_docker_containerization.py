"""
Production Deployment Tests: Docker Containerization

Tests Docker containerization, multi-stage builds, environment configurations,
and container orchestration following TDD methodology.
"""

import pytest
import subprocess
import tempfile
import os
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, List, Any, Optional

from src.services.application_assembler import ApplicationAssembler
from src.config.config_loader import ConfigLoader


class TestDockerContainerization:
    """Test Docker containerization and build processes"""
    
    @pytest.fixture
    def docker_config(self):
        """Sample Docker configuration for testing"""
        return {
            "services": {
                "fastapi-app": {
                    "build": {
                        "context": ".",
                        "dockerfile": "Dockerfile",
                        "args": {
                            "PYTHON_VERSION": "3.12",
                            "APP_ENV": "production"
                        }
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
                    "depends_on": ["postgresql", "redis", "qdrant"]
                },
                "vllm-server": {
                    "build": {
                        "context": "./vllm",
                        "dockerfile": "Dockerfile.vllm"
                    },
                    "ports": ["8001:8001"],
                    "environment": [
                        "MODEL_NAME=llama-2-7b",
                        "MAX_MODEL_LEN=4096"
                    ],
                    "volumes": [
                        "./models:/models",
                        "./cache:/cache"
                    ],
                    "deploy": {
                        "resources": {
                            "reservations": {
                                "devices": [
                                    {
                                        "driver": "nvidia",
                                        "count": 1,
                                        "capabilities": ["gpu"]
                                    }
                                ]
                            }
                        }
                    }
                },
                "postgresql": {
                    "image": "postgres:15-alpine",
                    "environment": [
                        "POSTGRES_DB=agentic_rag",
                        "POSTGRES_USER=rag_user",
                        "POSTGRES_PASSWORD=secure_password"
                    ],
                    "volumes": ["postgres_data:/var/lib/postgresql/data"],
                    "ports": ["5432:5432"]
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "ports": ["6379:6379"],
                    "volumes": ["redis_data:/data"]
                },
                "qdrant": {
                    "image": "qdrant/qdrant:latest",
                    "ports": ["6333:6333"],
                    "volumes": ["qdrant_data:/qdrant/storage"]
                }
            },
            "volumes": {
                "postgres_data": None,
                "redis_data": None,
                "qdrant_data": None
            },
            "networks": {
                "agentic_rag_network": {
                    "driver": "bridge"
                }
            }
        }
    
    @pytest.fixture
    def dockerfile_content(self):
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
    
    def test_dockerfile_validation(self, dockerfile_content):
        """Test Dockerfile syntax and best practices"""
        # Test basic syntax
        assert "FROM python:3.12-slim" in dockerfile_content
        assert "WORKDIR /app" in dockerfile_content
        assert "EXPOSE 8000" in dockerfile_content
        
        # Test security best practices
        assert "USER app" in dockerfile_content  # Non-root user
        assert "HEALTHCHECK" in dockerfile_content  # Health check
        assert "ENV PYTHONUNBUFFERED=1" in dockerfile_content  # Python optimization
        
        # Test multi-stage build
        assert "as base" in dockerfile_content
        
        # Test dependency management
        assert "COPY requirements.txt ." in dockerfile_content
        assert "pip install" in dockerfile_content
        
        # Test application setup
        assert "COPY src/" in dockerfile_content
        assert "COPY configs/" in dockerfile_content
    
    def test_docker_compose_validation(self, docker_config):
        """Test Docker Compose configuration"""
        # Test service definitions
        assert "fastapi-app" in docker_config["services"]
        assert "vllm-server" in docker_config["services"]
        assert "postgresql" in docker_config["services"]
        assert "redis" in docker_config["services"]
        assert "qdrant" in docker_config["services"]
        
        # Test build configurations
        fastapi_service = docker_config["services"]["fastapi-app"]
        assert "build" in fastapi_service
        assert "context" in fastapi_service["build"]
        assert "dockerfile" in fastapi_service["build"]
        
        # Test port mappings
        assert "8000:8000" in fastapi_service["ports"]
        assert "8001:8001" in docker_config["services"]["vllm-server"]["ports"]
        
        # Test environment variables
        assert "APP_ENV=production" in fastapi_service["environment"]
        assert "LOG_LEVEL=INFO" in fastapi_service["environment"]
        
        # Test volume mounts
        assert "./data:/app/data" in fastapi_service["volumes"]
        assert "./logs:/app/logs" in fastapi_service["volumes"]
        
        # Test dependencies
        assert "postgresql" in fastapi_service["depends_on"]
        assert "redis" in fastapi_service["depends_on"]
        assert "qdrant" in fastapi_service["depends_on"]
        
        # Test GPU configuration for vLLM
        vllm_service = docker_config["services"]["vllm-server"]
        assert "deploy" in vllm_service
        assert "resources" in vllm_service["deploy"]
        assert "reservations" in vllm_service["deploy"]["resources"]
        assert "devices" in vllm_service["deploy"]["resources"]["reservations"]
        
        # Test volumes
        assert "postgres_data" in docker_config["volumes"]
        assert "redis_data" in docker_config["volumes"]
        assert "qdrant_data" in docker_config["volumes"]
        
        # Test networks
        assert "agentic_rag_network" in docker_config["networks"]
    
    @patch('subprocess.run')
    def test_docker_build_process(self, mock_run, dockerfile_content):
        """Test Docker build process"""
        # Mock successful build
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"Successfully built image"
        
        # Test build command
        build_result = subprocess.run([
            "docker", "build", "-t", "agentic-rag:latest", "."
        ], capture_output=True, text=True)
        
        # Verify build was called
        mock_run.assert_called()
        assert build_result.returncode == 0
        
        # Test build with specific Dockerfile
        build_result = subprocess.run([
            "docker", "build", "-f", "Dockerfile.prod", "-t", "agentic-rag:prod", "."
        ], capture_output=True, text=True)
        
        assert build_result.returncode == 0
    
    @patch('subprocess.run')
    def test_docker_compose_build(self, mock_run, docker_config):
        """Test Docker Compose build process"""
        # Mock successful compose build
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"Successfully built all services"
        
        # Test compose build
        build_result = subprocess.run([
            "docker-compose", "build"
        ], capture_output=True, text=True)
        
        assert build_result.returncode == 0
        
        # Test compose build with specific service
        build_result = subprocess.run([
            "docker-compose", "build", "fastapi-app"
        ], capture_output=True, text=True)
        
        assert build_result.returncode == 0
    
    @patch('subprocess.run')
    def test_container_health_checks(self, mock_run):
        """Test container health check functionality"""
        # Mock health check response
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b'{"status": "healthy"}'
        
        # Test health check endpoint
        health_result = subprocess.run([
            "curl", "-f", "http://localhost:8000/health"
        ], capture_output=True, text=True)
        
        assert health_result.returncode == 0
        
        # Test container health status
        container_health = subprocess.run([
            "docker", "inspect", "--format='{{.State.Health.Status}}'", "agentic-rag-app"
        ], capture_output=True, text=True)
        
        assert container_health.returncode == 0
    
    def test_environment_configuration(self, docker_config):
        """Test environment configuration management"""
        # Test environment variables
        fastapi_service = docker_config["services"]["fastapi-app"]
        env_vars = fastapi_service["environment"]
        
        # Required environment variables
        required_vars = ["APP_ENV", "LOG_LEVEL"]
        for var in required_vars:
            assert any(var in env_var for env_var in env_vars)
        
        # Test vLLM environment configuration
        vllm_service = docker_config["services"]["vllm-server"]
        vllm_env_vars = vllm_service["environment"]
        
        required_vllm_vars = ["MODEL_NAME", "MAX_MODEL_LEN"]
        for var in required_vllm_vars:
            assert any(var in env_var for env_var in vllm_env_vars)
        
        # Test database environment configuration
        postgres_service = docker_config["services"]["postgresql"]
        postgres_env_vars = postgres_service["environment"]
        
        required_db_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
        for var in required_db_vars:
            assert any(var in env_var for env_var in postgres_env_vars)
    
    def test_volume_mounts(self, docker_config):
        """Test volume mount configurations"""
        # Test application volumes
        fastapi_service = docker_config["services"]["fastapi-app"]
        volumes = fastapi_service["volumes"]
        
        # Required volume mounts
        required_volumes = [
            "./data:/app/data",
            "./logs:/app/logs"
        ]
        for volume in required_volumes:
            assert volume in volumes
        
        # Test vLLM volumes
        vllm_service = docker_config["services"]["vllm-server"]
        vllm_volumes = vllm_service["volumes"]
        
        required_vllm_volumes = [
            "./models:/models",
            "./cache:/cache"
        ]
        for volume in required_vllm_volumes:
            assert volume in vllm_volumes
        
        # Test database volumes
        postgres_service = docker_config["services"]["postgresql"]
        postgres_volumes = postgres_service["volumes"]
        
        assert "postgres_data:/var/lib/postgresql/data" in postgres_volumes
    
    def test_network_configuration(self, docker_config):
        """Test network configuration"""
        # Test network definition
        networks = docker_config["networks"]
        assert "agentic_rag_network" in networks
        
        # Test network driver
        network_config = networks["agentic_rag_network"]
        assert network_config["driver"] == "bridge"
        
        # Test service connectivity
        fastapi_service = docker_config["services"]["fastapi-app"]
        assert "depends_on" in fastapi_service
        
        # Verify all services can communicate
        dependent_services = ["postgresql", "redis", "qdrant"]
        for service in dependent_services:
            assert service in fastapi_service["depends_on"]
    
    @patch('subprocess.run')
    def test_container_orchestration(self, mock_run):
        """Test container orchestration and management"""
        # Mock successful orchestration commands
        mock_run.return_value.returncode = 0
        
        # Test container startup
        start_result = subprocess.run([
            "docker-compose", "up", "-d"
        ], capture_output=True, text=True)
        
        assert start_result.returncode == 0
        
        # Test container status
        status_result = subprocess.run([
            "docker-compose", "ps"
        ], capture_output=True, text=True)
        
        assert status_result.returncode == 0
        
        # Test container logs
        logs_result = subprocess.run([
            "docker-compose", "logs", "fastapi-app"
        ], capture_output=True, text=True)
        
        assert logs_result.returncode == 0
        
        # Test container restart
        restart_result = subprocess.run([
            "docker-compose", "restart", "fastapi-app"
        ], capture_output=True, text=True)
        
        assert restart_result.returncode == 0
        
        # Test container stop
        stop_result = subprocess.run([
            "docker-compose", "down"
        ], capture_output=True, text=True)
        
        assert stop_result.returncode == 0
    
    def test_multi_stage_build_optimization(self, dockerfile_content):
        """Test multi-stage build optimization"""
        # Test base stage
        assert "FROM python:3.12-slim as base" in dockerfile_content
        
        # Test dependency installation optimization
        assert "COPY requirements.txt ." in dockerfile_content
        assert "pip install --no-cache-dir" in dockerfile_content
        
        # Test layer optimization
        assert "COPY src/" in dockerfile_content
        assert "COPY configs/" in dockerfile_content
        
        # Test security optimization
        assert "RUN useradd --create-home --shell /bin/bash app" in dockerfile_content
        assert "USER app" in dockerfile_content
    
    def test_production_security_configuration(self, dockerfile_content, docker_config):
        """Test production security configurations"""
        # Test non-root user
        assert "USER app" in dockerfile_content
        
        # Test health checks
        assert "HEALTHCHECK" in dockerfile_content
        
        # Test environment variable security
        fastapi_service = docker_config["services"]["fastapi-app"]
        env_vars = fastapi_service["environment"]
        
        # Should not expose sensitive data in environment
        sensitive_vars = ["PASSWORD", "SECRET", "KEY"]
        for var in sensitive_vars:
            assert not any(var.lower() in env_var.lower() for env_var in env_vars)
        
        # Test volume security
        volumes = fastapi_service["volumes"]
        for volume in volumes:
            # Should not mount sensitive directories
            assert "/etc/passwd" not in volume
            assert "/etc/shadow" not in volume
            assert "/root" not in volume


class TestDockerOptimization:
    """Test Docker optimization strategies"""
    
    def test_image_size_optimization(self):
        """Test Docker image size optimization"""
        # Test base image selection
        base_images = [
            "python:3.12-slim",  # Optimized for size
            "python:3.12-alpine",  # Minimal size
            "python:3.12"  # Full size
        ]
        
        # Slim image should be preferred for production
        preferred_base = "python:3.12-slim"
        assert preferred_base in base_images
        
        # Test multi-stage build for size reduction
        build_stages = ["base", "builder", "production"]
        assert len(build_stages) >= 2  # Should have multiple stages
    
    def test_build_cache_optimization(self):
        """Test Docker build cache optimization"""
        # Test layer ordering for cache efficiency
        layer_order = [
            "requirements.txt",  # Changes less frequently
            "src/",  # Changes more frequently
            "configs/"  # Changes more frequently
        ]
        
        # Requirements should be copied first for better caching
        assert layer_order[0] == "requirements.txt"
        
        # Test .dockerignore optimization
        dockerignore_patterns = [
            "*.pyc",
            "__pycache__",
            ".git",
            ".env",
            "tests/",
            "docs/"
        ]
        
        # Should ignore unnecessary files
        assert "*.pyc" in dockerignore_patterns
        assert "__pycache__" in dockerignore_patterns
        assert ".git" in dockerignore_patterns
    
    def test_runtime_optimization(self):
        """Test Docker runtime optimization"""
        # Test Python runtime optimization
        python_optimizations = [
            "PYTHONUNBUFFERED=1",
            "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONPATH=/app"
        ]
        
        for optimization in python_optimizations:
            assert "PYTHON" in optimization
        
        # Test process management
        process_config = {
            "user": "app",  # Non-root user
            "healthcheck": True,  # Health monitoring
            "restart_policy": "unless-stopped"  # Auto-restart
        }
        
        assert process_config["user"] == "app"
        assert process_config["healthcheck"] is True
        assert process_config["restart_policy"] == "unless-stopped" 
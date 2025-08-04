"""
Docker Deployment Manager

Manages Docker containerization, builds, orchestration, and deployment
following TDD methodology.
"""

import subprocess
import yaml
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DockerService:
    """Represents a Docker service configuration"""
    name: str
    image: str
    ports: List[str]
    environment: Dict[str, str]
    volumes: List[str]
    depends_on: List[str]
    healthcheck: Optional[Dict[str, Any]] = None


@dataclass
class DockerBuildConfig:
    """Represents a Docker build configuration"""
    context: str
    dockerfile: str
    args: Dict[str, str]
    target: Optional[str] = None


class DockerManager:
    """Manages Docker containerization and deployment"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.compose_file = self.project_root / "docker-compose.yml"
        self.dockerfile = self.project_root / "Dockerfile"
        
    def validate_dockerfile(self, dockerfile_path: str) -> Dict[str, Any]:
        """Validate Dockerfile syntax and best practices"""
        dockerfile_content = Path(dockerfile_path).read_text()
        
        validation_result = {
            "valid": True,
            "issues": [],
            "best_practices": []
        }
        
        # Check basic syntax
        required_elements = [
            "FROM",
            "WORKDIR",
            "EXPOSE"
        ]
        
        for element in required_elements:
            if element not in dockerfile_content:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Missing required element: {element}")
        
        # Check security best practices
        security_checks = [
            ("USER", "Non-root user should be used"),
            ("HEALTHCHECK", "Health check should be defined"),
            ("ENV PYTHONUNBUFFERED=1", "Python optimization should be enabled")
        ]
        
        for check, description in security_checks:
            if check in dockerfile_content:
                validation_result["best_practices"].append(f"✓ {description}")
            else:
                validation_result["issues"].append(f"Missing: {description}")
        
        # Check multi-stage build
        if "as " in dockerfile_content:
            validation_result["best_practices"].append("✓ Multi-stage build detected")
        
        return validation_result
    
    def validate_compose_config(self, compose_file: str) -> Dict[str, Any]:
        """Validate Docker Compose configuration"""
        with open(compose_file, 'r') as f:
            config = yaml.safe_load(f)
        
        validation_result = {
            "valid": True,
            "issues": [],
            "services": []
        }
        
        if "services" not in config:
            validation_result["valid"] = False
            validation_result["issues"].append("No services defined")
            return validation_result
        
        # Validate each service
        for service_name, service_config in config["services"].items():
            service_validation = {
                "name": service_name,
                "valid": True,
                "issues": []
            }
            
            # Check required fields - either image or build must be present
            has_image = "image" in service_config
            has_build = "build" in service_config
            
            if not has_image and not has_build:
                service_validation["valid"] = False
                service_validation["issues"].append("Missing required field: either 'image' or 'build'")
            
            # Check ports
            if "ports" not in service_config:
                service_validation["valid"] = False
                service_validation["issues"].append("Missing required field: ports")
            
            # Check health checks
            if "healthcheck" not in service_config:
                service_validation["issues"].append("Health check not defined")
            
            # Check environment variables
            if "environment" in service_config:
                env_vars = service_config["environment"]
                if isinstance(env_vars, list):
                    for env_var in env_vars:
                        if "PASSWORD" in env_var or "SECRET" in env_var:
                            service_validation["issues"].append(f"Sensitive data in environment: {env_var}")
            
            validation_result["services"].append(service_validation)
            
            if not service_validation["valid"]:
                validation_result["valid"] = False
                # Add service issues to top-level issues
                for issue in service_validation["issues"]:
                    validation_result["issues"].append(f"{service_name}: {issue}")
        
        return validation_result
    
    def build_image(self, context: str = ".", dockerfile: str = "Dockerfile", 
                   tag: str = "agentic-rag:latest", **kwargs) -> Dict[str, Any]:
        """Build Docker image"""
        try:
            cmd = [
                "docker", "build",
                "-t", tag,
                "-f", dockerfile,
                context
            ]
            
            # Add build args
            for key, value in kwargs.items():
                cmd.extend(["--build-arg", f"{key}={value}"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to build Docker image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def build_compose_services(self, services: Optional[List[str]] = None) -> Dict[str, Any]:
        """Build Docker Compose services"""
        try:
            cmd = ["docker-compose", "build"]
            if services:
                cmd.extend(services)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to build Docker Compose services: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def start_services(self, services: Optional[List[str]] = None, 
                      detached: bool = True) -> Dict[str, Any]:
        """Start Docker Compose services"""
        try:
            cmd = ["docker-compose", "up"]
            if detached:
                cmd.append("-d")
            if services:
                cmd.extend(services)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to start Docker Compose services: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop_services(self, services: Optional[List[str]] = None) -> Dict[str, Any]:
        """Stop Docker Compose services"""
        try:
            cmd = ["docker-compose", "down"]
            if services:
                cmd.extend(services)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to stop Docker Compose services: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all Docker Compose services"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        try:
            # Check if service is running
            result = subprocess.run(
                ["docker-compose", "ps", "-q", service_name],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                return {
                    "success": False,
                    "status": "not_running",
                    "error": "Service not running"
                }
            
            # Check health status
            container_id = result.stdout.strip()
            health_result = subprocess.run(
                ["docker", "inspect", "--format='{{.State.Health.Status}}'", container_id],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            health_status = health_result.stdout.strip().strip("'")
            
            return {
                "success": True,
                "status": health_status,
                "container_id": container_id
            }
            
        except Exception as e:
            logger.error(f"Failed to check service health: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_service_logs(self, service_name: str, lines: int = 100) -> Dict[str, Any]:
        """Get logs for a specific service"""
        try:
            result = subprocess.run(
                ["docker-compose", "logs", "--tail", str(lines), service_name],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to get service logs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a specific service"""
        try:
            result = subprocess.run(
                ["docker-compose", "restart", service_name],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to restart service: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def optimize_build_cache(self) -> Dict[str, Any]:
        """Optimize Docker build cache"""
        try:
            # Prune unused images
            prune_result = subprocess.run(
                ["docker", "image", "prune", "-f"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            # Prune unused containers
            container_prune_result = subprocess.run(
                ["docker", "container", "prune", "-f"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "success": prune_result.returncode == 0 and container_prune_result.returncode == 0,
                "images_pruned": prune_result.stdout,
                "containers_pruned": container_prune_result.stdout
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize build cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_compose_config(self, config: Dict[str, Any]) -> str:
        """Generate Docker Compose configuration"""
        return yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    def save_compose_config(self, config: Dict[str, Any], file_path: str) -> bool:
        """Save Docker Compose configuration to file"""
        try:
            with open(file_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save compose config: {e}")
            return False 
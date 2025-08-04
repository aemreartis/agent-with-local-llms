"""
CI/CD Deployment Manager

Manages CI/CD pipeline automation, GitHub Actions workflows, automated testing,
deployment automation, and pipeline validation following TDD methodology.
"""

import subprocess
import yaml
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GitHubActionsWorkflow:
    """Represents a GitHub Actions workflow configuration"""
    name: str
    triggers: List[str]
    jobs: List[str]
    environment_variables: Dict[str, str]
    
    def is_valid(self) -> bool:
        """Validate workflow configuration"""
        return (
            self.name != "" and
            len(self.triggers) > 0 and
            len(self.jobs) > 0
        )


@dataclass
class DeploymentPipeline:
    """Represents a deployment pipeline configuration"""
    name: str
    environments: List[str]
    auto_deploy_environments: List[str]
    manual_approval_environments: List[str]
    rollback_enabled: bool
    
    def is_valid(self) -> bool:
        """Validate pipeline configuration"""
        return (
            self.name != "" and
            len(self.environments) > 0 and
            len(self.auto_deploy_environments) > 0
        )


class CICDManager:
    """Manages CI/CD pipeline automation and deployment"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.workflows_dir = Path(".github/workflows")
        self.pipeline_config = {}
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> bool:
        """Load CI/CD configuration from file"""
        try:
            with open(config_path, 'r') as f:
                self.pipeline_config = yaml.safe_load(f)
            return True
        except Exception as e:
            logger.error(f"Failed to load CI/CD config: {e}")
            return False
    
    def validate_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GitHub Actions workflow configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check basic structure
        if "name" not in workflow_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing workflow name")
        
        if "on" not in workflow_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing workflow triggers")
        
        if "jobs" not in workflow_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing workflow jobs")
        else:
            jobs = workflow_config["jobs"]
            if len(jobs) == 0:
                validation_result["valid"] = False
                validation_result["issues"].append("No jobs defined")
            else:
                # Validate required jobs
                required_jobs = ["test", "build"]
                for job_name in required_jobs:
                    if job_name not in jobs:
                        validation_result["warnings"].append(f"Missing recommended job: {job_name}")
                
                # Validate job structure
                for job_name, job_config in jobs.items():
                    job_validation = self._validate_job(job_name, job_config)
                    validation_result["issues"].extend(job_validation["issues"])
                    validation_result["warnings"].extend(job_validation["warnings"])
                    if not job_validation["valid"]:
                        validation_result["valid"] = False
        
        # Check environment variables
        if "env" in workflow_config:
            env = workflow_config["env"]
            if "PYTHON_VERSION" not in env:
                validation_result["warnings"].append("PYTHON_VERSION not specified")
            if "DOCKER_REGISTRY" not in env:
                validation_result["warnings"].append("DOCKER_REGISTRY not specified")
        
        return validation_result
    
    def _validate_job(self, job_name: str, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual job configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check required fields
        if "runs-on" not in job_config:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Job {job_name}: Missing runs-on")
        
        if "steps" not in job_config:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Job {job_name}: Missing steps")
        else:
            steps = job_config["steps"]
            if len(steps) == 0:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Job {job_name}: No steps defined")
            else:
                # Validate steps
                for i, step in enumerate(steps):
                    step_validation = self._validate_step(job_name, i, step)
                    validation_result["issues"].extend(step_validation["issues"])
                    validation_result["warnings"].extend(step_validation["warnings"])
                    if not step_validation["valid"]:
                        validation_result["valid"] = False
        
        return validation_result
    
    def _validate_step(self, job_name: str, step_index: int, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual step configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check required fields
        if "name" not in step_config:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Job {job_name} step {step_index}: Missing name")
        
        # Check action or run
        if "uses" not in step_config and "run" not in step_config:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Job {job_name} step {step_index}: Missing uses or run")
        
        # Check security for login steps
        if "name" in step_config and "login" in step_config["name"].lower():
            if "with" in step_config:
                with_config = step_config["with"]
                if "password" in with_config:
                    password = with_config["password"]
                    if not password.startswith("${{ secrets."):
                        validation_result["warnings"].append(f"Job {job_name} step {step_index}: Password not using secrets")
        
        return validation_result
    
    def validate_pipeline(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deployment pipeline configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check basic structure
        if "environments" not in pipeline_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing environments configuration")
        else:
            environments = pipeline_config["environments"]
            if len(environments) == 0:
                validation_result["valid"] = False
                validation_result["issues"].append("No environments defined")
            else:
                # Validate each environment
                for env_name, env_config in environments.items():
                    env_validation = self._validate_environment(env_name, env_config)
                    validation_result["issues"].extend(env_validation["issues"])
                    validation_result["warnings"].extend(env_validation["warnings"])
                    if not env_validation["valid"]:
                        validation_result["valid"] = False
        
        # Check rollback configuration
        if "rollback" in pipeline_config:
            rollback = pipeline_config["rollback"]
            if "enabled" in rollback and rollback["enabled"]:
                if "max_versions" not in rollback:
                    validation_result["warnings"].append("Rollback enabled but max_versions not specified")
        
        # Check testing configuration
        if "testing" in pipeline_config:
            testing = pipeline_config["testing"]
            if not testing.get("unit_tests", False):
                validation_result["warnings"].append("Unit tests not enabled")
            if not testing.get("integration_tests", False):
                validation_result["warnings"].append("Integration tests not enabled")
        
        return validation_result
    
    def _validate_environment(self, env_name: str, env_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual environment configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check required fields
        if "branch" not in env_config:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Environment {env_name}: Missing branch")
        
        if "kubernetes_namespace" not in env_config:
            validation_result["warnings"].append(f"Environment {env_name}: Kubernetes namespace not specified")
        
        if "helm_chart" not in env_config:
            validation_result["warnings"].append(f"Environment {env_name}: Helm chart not specified")
        
        # Check deployment strategy
        if "auto_deploy" in env_config and env_config["auto_deploy"]:
            if env_name == "production":
                validation_result["warnings"].append("Production environment has auto-deploy enabled")
        
        return validation_result
    
    def generate_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate GitHub Actions workflow"""
        try:
            workflow = {
                "name": workflow_config.get("name", "CI/CD Pipeline"),
                "on": {
                    "push": {
                        "branches": workflow_config.get("branches", ["main", "develop"])
                    },
                    "pull_request": {
                        "branches": workflow_config.get("pr_branches", ["main"])
                    }
                },
                "env": {
                    "PYTHON_VERSION": workflow_config.get("python_version", "3.12"),
                    "DOCKER_REGISTRY": workflow_config.get("docker_registry", "ghcr.io"),
                    "IMAGE_NAME": workflow_config.get("image_name", "agentic-rag")
                },
                "jobs": self._generate_jobs(workflow_config)
            }
            
            return {
                "success": True,
                "workflow": workflow
            }
            
        except Exception as e:
            logger.error(f"Failed to generate workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_jobs(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate workflow jobs"""
        jobs = {}
        
        # Test job
        jobs["test"] = {
            "runs-on": "ubuntu-latest",
            "steps": [
                {
                    "name": "Checkout code",
                    "uses": "actions/checkout@v4"
                },
                {
                    "name": "Set up Python",
                    "uses": "actions/setup-python@v4",
                    "with": {
                        "python-version": "${{ env.PYTHON_VERSION }}"
                    }
                },
                {
                    "name": "Install dependencies",
                    "run": "pip install -r requirements.txt -r requirements-dev.txt"
                },
                {
                    "name": "Run tests",
                    "run": "python -m pytest tests/ -v --cov=src --cov-report=xml"
                },
                {
                    "name": "Upload coverage",
                    "uses": "codecov/codecov-action@v3",
                    "with": {
                        "file": "./coverage.xml"
                    }
                }
            ]
        }
        
        # Build job
        jobs["build"] = {
            "runs-on": "ubuntu-latest",
            "needs": "test",
            "steps": [
                {
                    "name": "Checkout code",
                    "uses": "actions/checkout@v4"
                },
                {
                    "name": "Set up Docker Buildx",
                    "uses": "docker/setup-buildx-action@v3"
                },
                {
                    "name": "Login to Container Registry",
                    "uses": "docker/login-action@v3",
                    "with": {
                        "registry": "${{ env.DOCKER_REGISTRY }}",
                        "username": "${{ github.actor }}",
                        "password": "${{ secrets.GITHUB_TOKEN }}"
                    }
                },
                {
                    "name": "Build and push Docker image",
                    "uses": "docker/build-push-action@v5",
                    "with": {
                        "context": ".",
                        "push": True,
                        "tags": "${{ env.DOCKER_REGISTRY }}/${{ github.repository }}:${{ github.sha }}"
                    }
                }
            ]
        }
        
        # Deploy job (only for main branch)
        jobs["deploy"] = {
            "runs-on": "ubuntu-latest",
            "needs": "build",
            "if": "github.ref == 'refs/heads/main'",
            "steps": [
                {
                    "name": "Deploy to production",
                    "run": "echo 'Deploying to production...'"
                }
            ]
        }
        
        return jobs
    
    def save_workflow(self, workflow: Dict[str, Any], filename: str) -> bool:
        """Save workflow to file"""
        try:
            # Ensure workflows directory exists
            self.workflows_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_path = self.workflows_dir / filename
            
            with open(workflow_path, 'w') as f:
                yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            return False
    
    def deploy_to_environment(self, environment: str, version: str) -> Dict[str, Any]:
        """Deploy to specific environment"""
        try:
            # Mock deployment process
            cmd = ["echo", f"Deploying {version} to {environment}"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "environment": environment,
                "version": version,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to deploy to {environment}: {e}")
            return {
                "success": False,
                "environment": environment,
                "version": version,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "returncode": 1
            }
    
    def rollback_deployment(self, environment: str, version: str) -> Dict[str, Any]:
        """Rollback deployment to specific version"""
        try:
            # Mock rollback process
            cmd = ["echo", f"Rolling back {environment} to {version}"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "environment": environment,
                "rollback_version": version,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to rollback {environment}: {e}")
            return {
                "success": False,
                "environment": environment,
                "rollback_version": version,
                "error": str(e)
            }
    
    def get_deployment_status(self, environment: str) -> Dict[str, Any]:
        """Get deployment status for environment"""
        try:
            # Mock status check
            return {
                "success": True,
                "environment": environment,
                "status": "deployed",
                "version": "v1.0.0",
                "timestamp": "2024-01-01T10:00:00Z",
                "health": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment status for {environment}: {e}")
            return {
                "success": False,
                "environment": environment,
                "error": str(e)
            }
    
    def run_tests(self, test_type: str = "all") -> Dict[str, Any]:
        """Run automated tests"""
        try:
            cmd = ["python", "-m", "pytest"]
            
            if test_type == "unit":
                cmd.extend(["tests/unit/"])
            elif test_type == "integration":
                cmd.extend(["tests/integration/"])
            elif test_type == "e2e":
                cmd.extend(["tests/e2e/"])
            else:
                cmd.extend(["tests/"])
            
            cmd.extend(["-v", "--tb=short"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "test_type": test_type,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to run {test_type} tests: {e}")
            return {
                "success": False,
                "test_type": test_type,
                "error": str(e)
            }
    
    def run_security_scan(self) -> Dict[str, Any]:
        """Run security scanning"""
        try:
            # Mock security scan
            cmd = ["echo", "Running security scan..."]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "scan_type": "security",
                "vulnerabilities": [],
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to run security scan: {e}")
            return {
                "success": False,
                "scan_type": "security",
                "error": str(e)
            }
    
    def run_performance_test(self) -> Dict[str, Any]:
        """Run performance testing"""
        try:
            # Mock performance test
            cmd = ["echo", "Running performance test..."]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "test_type": "performance",
                "metrics": {
                    "response_time": 150,
                    "throughput": 100,
                    "error_rate": 0.01
                },
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to run performance test: {e}")
            return {
                "success": False,
                "test_type": "performance",
                "error": str(e)
            } 
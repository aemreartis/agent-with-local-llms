"""
Production Deployment Tests: CI/CD Pipeline

Tests CI/CD pipeline automation, GitHub Actions workflows, automated testing,
deployment automation, and pipeline validation following TDD methodology.
"""

import pytest
import yaml
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, List, Any, Optional

from src.deployment.cicd_manager import CICDManager, GitHubActionsWorkflow, DeploymentPipeline


class TestCICDPipeline:
    """Test CI/CD pipeline automation and workflows"""
    
    @pytest.fixture
    def github_actions_workflow(self):
        """Sample GitHub Actions workflow configuration"""
        return {
            "name": "CI/CD Pipeline",
            "on": {
                "push": {
                    "branches": ["main", "develop"]
                },
                "pull_request": {
                    "branches": ["main"]
                }
            },
            "env": {
                "PYTHON_VERSION": "3.12",
                "DOCKER_REGISTRY": "ghcr.io",
                "IMAGE_NAME": "agentic-rag"
            },
            "jobs": {
                "test": {
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
                },
                "build": {
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
                },
                "deploy": {
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
            }
        }
    
    @pytest.fixture
    def deployment_pipeline_config(self):
        """Sample deployment pipeline configuration"""
        return {
            "environments": {
                "development": {
                    "branch": "develop",
                    "auto_deploy": True,
                    "kubernetes_namespace": "agentic-rag-dev",
                    "helm_chart": "agentic-rag",
                    "helm_values": "values-dev.yaml"
                },
                "staging": {
                    "branch": "staging",
                    "auto_deploy": True,
                    "kubernetes_namespace": "agentic-rag-staging",
                    "helm_chart": "agentic-rag",
                    "helm_values": "values-staging.yaml"
                },
                "production": {
                    "branch": "main",
                    "auto_deploy": False,
                    "manual_approval": True,
                    "kubernetes_namespace": "agentic-rag",
                    "helm_chart": "agentic-rag",
                    "helm_values": "values-prod.yaml"
                }
            },
            "rollback": {
                "enabled": True,
                "max_versions": 5,
                "auto_rollback_on_failure": True
            },
            "testing": {
                "unit_tests": True,
                "integration_tests": True,
                "e2e_tests": True,
                "security_scanning": True,
                "performance_testing": True
            }
        }
    
    def test_github_actions_workflow_validation(self, github_actions_workflow):
        """Test GitHub Actions workflow configuration"""
        # Test basic structure
        assert "name" in github_actions_workflow
        assert "on" in github_actions_workflow
        assert "jobs" in github_actions_workflow
        
        # Test workflow triggers
        triggers = github_actions_workflow["on"]
        assert "push" in triggers
        assert "pull_request" in triggers
        
        # Test environment variables
        env = github_actions_workflow["env"]
        assert "PYTHON_VERSION" in env
        assert "DOCKER_REGISTRY" in env
        assert "IMAGE_NAME" in env
        
        # Test jobs
        jobs = github_actions_workflow["jobs"]
        required_jobs = ["test", "build", "deploy"]
        for job_name in required_jobs:
            assert job_name in jobs
        
        # Test test job
        test_job = jobs["test"]
        assert test_job["runs-on"] == "ubuntu-latest"
        assert "steps" in test_job
        
        # Test build job
        build_job = jobs["build"]
        assert build_job["runs-on"] == "ubuntu-latest"
        assert "needs" in build_job
        assert build_job["needs"] == "test"
        
        # Test deploy job
        deploy_job = jobs["deploy"]
        assert deploy_job["runs-on"] == "ubuntu-latest"
        assert "needs" in deploy_job
        assert deploy_job["needs"] == "build"
        assert "if" in deploy_job
        assert "github.ref == 'refs/heads/main'" in deploy_job["if"]
    
    def test_deployment_pipeline_validation(self, deployment_pipeline_config):
        """Test deployment pipeline configuration"""
        # Test basic structure
        assert "environments" in deployment_pipeline_config
        assert "rollback" in deployment_pipeline_config
        assert "testing" in deployment_pipeline_config
        
        # Test environments
        environments = deployment_pipeline_config["environments"]
        required_envs = ["development", "staging", "production"]
        for env_name in required_envs:
            assert env_name in environments
        
        # Test development environment
        dev_env = environments["development"]
        assert dev_env["branch"] == "develop"
        assert dev_env["auto_deploy"] is True
        assert "kubernetes_namespace" in dev_env
        assert "helm_chart" in dev_env
        assert "helm_values" in dev_env
        
        # Test staging environment
        staging_env = environments["staging"]
        assert staging_env["branch"] == "staging"
        assert staging_env["auto_deploy"] is True
        assert "kubernetes_namespace" in staging_env
        
        # Test production environment
        prod_env = environments["production"]
        assert prod_env["branch"] == "main"
        assert prod_env["auto_deploy"] is False
        assert prod_env["manual_approval"] is True
        
        # Test rollback configuration
        rollback = deployment_pipeline_config["rollback"]
        assert rollback["enabled"] is True
        assert rollback["max_versions"] >= 1
        assert rollback["auto_rollback_on_failure"] is True
        
        # Test testing configuration
        testing = deployment_pipeline_config["testing"]
        assert testing["unit_tests"] is True
        assert testing["integration_tests"] is True
        assert testing["e2e_tests"] is True
        assert testing["security_scanning"] is True
        assert testing["performance_testing"] is True
    
    def test_workflow_steps_validation(self, github_actions_workflow):
        """Test GitHub Actions workflow steps"""
        jobs = github_actions_workflow["jobs"]
        
        # Test test job steps
        test_steps = jobs["test"]["steps"]
        step_names = [step["name"] for step in test_steps]
        
        required_test_steps = [
            "Checkout code",
            "Set up Python",
            "Install dependencies",
            "Run tests",
            "Upload coverage"
        ]
        
        for step_name in required_test_steps:
            assert step_name in step_names
        
        # Test build job steps
        build_steps = jobs["build"]["steps"]
        build_step_names = [step["name"] for step in build_steps]
        
        required_build_steps = [
            "Checkout code",
            "Set up Docker Buildx",
            "Login to Container Registry",
            "Build and push Docker image"
        ]
        
        for step_name in required_build_steps:
            assert step_name in build_step_names
    
    def test_environment_promotion_validation(self, deployment_pipeline_config):
        """Test environment promotion strategy"""
        environments = deployment_pipeline_config["environments"]
        
        # Test promotion flow: dev -> staging -> production
        dev_env = environments["development"]
        staging_env = environments["staging"]
        prod_env = environments["production"]
        
        # Development should auto-deploy
        assert dev_env["auto_deploy"] is True
        assert "manual_approval" not in dev_env
        
        # Staging should auto-deploy
        assert staging_env["auto_deploy"] is True
        assert "manual_approval" not in staging_env
        
        # Production should require manual approval
        assert prod_env["auto_deploy"] is False
        assert prod_env["manual_approval"] is True
    
    def test_security_validation(self, github_actions_workflow):
        """Test security configuration in CI/CD pipeline"""
        jobs = github_actions_workflow["jobs"]
        
        # Test that secrets are used properly
        build_steps = jobs["build"]["steps"]
        login_step = next(step for step in build_steps if step["name"] == "Login to Container Registry")
        
        assert "with" in login_step
        assert "username" in login_step["with"]
        assert "password" in login_step["with"]
        assert "${{ github.actor }}" in login_step["with"]["username"]
        assert "${{ secrets.GITHUB_TOKEN }}" in login_step["with"]["password"]
    
    def test_testing_strategy_validation(self, deployment_pipeline_config):
        """Test testing strategy configuration"""
        testing = deployment_pipeline_config["testing"]
        
        # All testing types should be enabled
        assert testing["unit_tests"] is True
        assert testing["integration_tests"] is True
        assert testing["e2e_tests"] is True
        assert testing["security_scanning"] is True
        assert testing["performance_testing"] is True
    
    def test_rollback_strategy_validation(self, deployment_pipeline_config):
        """Test rollback strategy configuration"""
        rollback = deployment_pipeline_config["rollback"]
        
        # Rollback should be enabled
        assert rollback["enabled"] is True
        
        # Should have reasonable version limits
        assert rollback["max_versions"] >= 3
        assert rollback["max_versions"] <= 10
        
        # Should auto-rollback on failure
        assert rollback["auto_rollback_on_failure"] is True


class TestCICDManager:
    """Test CI/CD manager functionality"""
    
    @pytest.fixture
    def cicd_manager(self):
        """Create CI/CD manager instance for testing"""
        return CICDManager()
    
    def test_cicd_manager_initialization(self, cicd_manager):
        """Test CI/CD manager initialization"""
        assert cicd_manager is not None
        assert hasattr(cicd_manager, 'validate_workflow')
        assert hasattr(cicd_manager, 'generate_workflow')
        assert hasattr(cicd_manager, 'deploy_to_environment')
    
    def test_workflow_validation_success(self, cicd_manager):
        """Test successful workflow validation"""
        workflow_config = {
            "name": "CI/CD Pipeline",
            "on": {
                "push": {"branches": ["main", "develop"]},
                "pull_request": {"branches": ["main"]}
            },
            "env": {
                "PYTHON_VERSION": "3.12",
                "DOCKER_REGISTRY": "ghcr.io",
                "IMAGE_NAME": "agentic-rag"
            },
            "jobs": {
                "test": {"runs-on": "ubuntu-latest", "steps": [{"name": "test", "run": "echo test"}]},
                "build": {"runs-on": "ubuntu-latest", "steps": [{"name": "build", "run": "echo build"}]}
            }
        }
        
        result = cicd_manager.validate_workflow(workflow_config)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert len(result["warnings"]) >= 0
    
    def test_workflow_validation_failure(self, cicd_manager):
        """Test workflow validation with invalid configuration"""
        invalid_workflow = {
            "name": "Invalid Workflow",
            # Missing required fields
        }
        
        result = cicd_manager.validate_workflow(invalid_workflow)
        
        assert result["valid"] is False
        assert len(result["issues"]) >= 1
    
    def test_pipeline_validation_success(self, cicd_manager):
        """Test successful pipeline validation"""
        pipeline_config = {
            "environments": {
                "development": {
                    "branch": "develop",
                    "auto_deploy": True,
                    "kubernetes_namespace": "agentic-rag-dev",
                    "helm_chart": "agentic-rag",
                    "helm_values": "values-dev.yaml"
                },
                "staging": {
                    "branch": "staging",
                    "auto_deploy": True,
                    "kubernetes_namespace": "agentic-rag-staging",
                    "helm_chart": "agentic-rag",
                    "helm_values": "values-staging.yaml"
                },
                "production": {
                    "branch": "main",
                    "auto_deploy": False,
                    "manual_approval": True,
                    "kubernetes_namespace": "agentic-rag",
                    "helm_chart": "agentic-rag",
                    "helm_values": "values-prod.yaml"
                }
            },
            "rollback": {
                "enabled": True,
                "max_versions": 5,
                "auto_rollback_on_failure": True
            },
            "testing": {
                "unit_tests": True,
                "integration_tests": True,
                "e2e_tests": True,
                "security_scanning": True,
                "performance_testing": True
            }
        }
        
        result = cicd_manager.validate_pipeline(pipeline_config)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert len(result["warnings"]) >= 0
    
    def test_pipeline_validation_failure(self, cicd_manager):
        """Test pipeline validation with invalid configuration"""
        invalid_pipeline = {
            "environments": {
                # Missing required environments
            }
        }
        
        result = cicd_manager.validate_pipeline(invalid_pipeline)
        
        assert result["valid"] is False
        assert len(result["issues"]) >= 1
    
    @patch('subprocess.run')
    def test_deploy_to_environment_success(self, mock_run, cicd_manager):
        """Test successful deployment to environment"""
        # Mock successful deployment
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Deployment successful"
        
        result = cicd_manager.deploy_to_environment("staging", "v1.0.0")
        
        assert result["success"] is True
        assert result["environment"] == "staging"
        assert result["version"] == "v1.0.0"
    
    @patch('subprocess.run')
    def test_deploy_to_environment_failure(self, mock_run, cicd_manager):
        """Test failed deployment to environment"""
        # Mock failed deployment by raising an exception
        mock_run.side_effect = Exception("Deployment failed")
        
        result = cicd_manager.deploy_to_environment("production", "v1.0.0")
        
        assert result["success"] is False
        assert "Deployment failed" in result["error"]
    
    def test_generate_workflow(self, cicd_manager):
        """Test workflow generation"""
        workflow_config = {
            "name": "Test Workflow",
            "python_version": "3.12",
            "docker_registry": "ghcr.io",
            "image_name": "test-image"
        }
        
        result = cicd_manager.generate_workflow(workflow_config)
        
        assert result["success"] is True
        assert "name" in result["workflow"]
        assert "jobs" in result["workflow"]
        assert result["workflow"]["name"] == "Test Workflow"
    
    def test_rollback_deployment(self, cicd_manager):
        """Test deployment rollback"""
        result = cicd_manager.rollback_deployment("production", "v0.9.0")
        
        assert result["success"] is True
        assert result["environment"] == "production"
        assert result["rollback_version"] == "v0.9.0"
    
    def test_get_deployment_status(self, cicd_manager):
        """Test deployment status retrieval"""
        result = cicd_manager.get_deployment_status("staging")
        
        assert result["success"] is True
        assert "status" in result
        assert "version" in result
        assert "timestamp" in result


class TestGitHubActionsWorkflow:
    """Test GitHub Actions workflow data class"""
    
    def test_workflow_creation(self):
        """Test GitHub Actions workflow creation"""
        workflow = GitHubActionsWorkflow(
            name="Test Workflow",
            triggers=["push", "pull_request"],
            jobs=["test", "build", "deploy"],
            environment_variables={
                "PYTHON_VERSION": "3.12",
                "DOCKER_REGISTRY": "ghcr.io"
            }
        )
        
        assert workflow.name == "Test Workflow"
        assert "push" in workflow.triggers
        assert "test" in workflow.jobs
        assert workflow.environment_variables["PYTHON_VERSION"] == "3.12"
    
    def test_workflow_validation(self):
        """Test workflow validation"""
        workflow = GitHubActionsWorkflow(
            name="Valid Workflow",
            triggers=["push"],
            jobs=["test"],
            environment_variables={}
        )
        
        assert workflow.is_valid() is True
        
        # Test invalid workflow
        invalid_workflow = GitHubActionsWorkflow(
            name="",
            triggers=[],
            jobs=[],
            environment_variables={}
        )
        
        assert invalid_workflow.is_valid() is False


class TestDeploymentPipeline:
    """Test deployment pipeline data class"""
    
    def test_pipeline_creation(self):
        """Test deployment pipeline creation"""
        pipeline = DeploymentPipeline(
            name="Test Pipeline",
            environments=["dev", "staging", "production"],
            auto_deploy_environments=["dev", "staging"],
            manual_approval_environments=["production"],
            rollback_enabled=True
        )
        
        assert pipeline.name == "Test Pipeline"
        assert "dev" in pipeline.environments
        assert "production" in pipeline.manual_approval_environments
        assert pipeline.rollback_enabled is True
    
    def test_pipeline_validation(self):
        """Test pipeline validation"""
        pipeline = DeploymentPipeline(
            name="Valid Pipeline",
            environments=["dev", "staging", "production"],
            auto_deploy_environments=["dev"],
            manual_approval_environments=["production"],
            rollback_enabled=True
        )
        
        assert pipeline.is_valid() is True
        
        # Test invalid pipeline
        invalid_pipeline = DeploymentPipeline(
            name="",
            environments=[],
            auto_deploy_environments=[],
            manual_approval_environments=[],
            rollback_enabled=False
        )
        
        assert invalid_pipeline.is_valid() is False


class TestAutomatedTesting:
    """Test automated testing integration"""
    
    def test_unit_testing_integration(self):
        """Test unit testing integration in CI/CD"""
        test_config = {
            "framework": "pytest",
            "coverage_threshold": 90,
            "test_pattern": "tests/unit/",
            "parallel_execution": True
        }
        
        assert test_config["framework"] == "pytest"
        assert test_config["coverage_threshold"] >= 80
        assert test_config["parallel_execution"] is True
    
    def test_integration_testing_integration(self):
        """Test integration testing integration in CI/CD"""
        test_config = {
            "framework": "pytest",
            "test_pattern": "tests/integration/",
            "requires_database": True,
            "requires_redis": True,
            "timeout": 300
        }
        
        assert test_config["framework"] == "pytest"
        assert test_config["requires_database"] is True
        assert test_config["timeout"] >= 60
    
    def test_e2e_testing_integration(self):
        """Test end-to-end testing integration in CI/CD"""
        test_config = {
            "framework": "pytest",
            "test_pattern": "tests/e2e/",
            "requires_full_stack": True,
            "browser_testing": True,
            "timeout": 600
        }
        
        assert test_config["framework"] == "pytest"
        assert test_config["requires_full_stack"] is True
        assert test_config["timeout"] >= 300
    
    def test_security_scanning_integration(self):
        """Test security scanning integration in CI/CD"""
        security_config = {
            "vulnerability_scanning": True,
            "dependency_checking": True,
            "container_scanning": True,
            "secrets_detection": True,
            "fail_on_high_severity": True
        }
        
        assert security_config["vulnerability_scanning"] is True
        assert security_config["dependency_checking"] is True
        assert security_config["fail_on_high_severity"] is True
    
    def test_performance_testing_integration(self):
        """Test performance testing integration in CI/CD"""
        performance_config = {
            "load_testing": True,
            "stress_testing": True,
            "benchmark_testing": True,
            "response_time_threshold": 2000,
            "throughput_threshold": 100
        }
        
        assert performance_config["load_testing"] is True
        assert performance_config["response_time_threshold"] <= 5000
        assert performance_config["throughput_threshold"] >= 10 
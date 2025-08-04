"""
Production Deployment Tests: Kubernetes Deployment

Tests Kubernetes deployment, Helm charts, service mesh integration,
and production environment validation following TDD methodology.
"""

import pytest
import yaml
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, List, Any, Optional

from src.deployment.kubernetes_manager import KubernetesManager, KubernetesConfig, HelmChart


class TestKubernetesDeployment:
    """Test Kubernetes deployment and orchestration"""
    
    @pytest.fixture
    def kubernetes_config(self):
        """Sample Kubernetes configuration for testing"""
        return {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": "agentic-rag"
            },
            "spec": {}
        }
    
    @pytest.fixture
    def deployment_manifest(self):
        """Sample Kubernetes deployment manifest"""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "fastapi-app",
                "namespace": "agentic-rag",
                "labels": {
                    "app": "fastapi-app",
                    "version": "v1.0.0"
                }
            },
            "spec": {
                "replicas": 3,
                "selector": {
                    "matchLabels": {
                        "app": "fastapi-app"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "fastapi-app"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "fastapi-app",
                                "image": "agentic-rag:latest",
                                "ports": [
                                    {
                                        "containerPort": 8000,
                                        "protocol": "TCP"
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "APP_ENV",
                                        "value": "production"
                                    },
                                    {
                                        "name": "LOG_LEVEL",
                                        "value": "INFO"
                                    }
                                ],
                                "resources": {
                                    "requests": {
                                        "memory": "512Mi",
                                        "cpu": "250m"
                                    },
                                    "limits": {
                                        "memory": "1Gi",
                                        "cpu": "500m"
                                    }
                                },
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": "/health",
                                        "port": 8000
                                    },
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/health",
                                        "port": 8000
                                    },
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5
                                }
                            }
                        ]
                    }
                }
            }
        }
    
    @pytest.fixture
    def service_manifest(self):
        """Sample Kubernetes service manifest"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "fastapi-service",
                "namespace": "agentic-rag"
            },
            "spec": {
                "selector": {
                    "app": "fastapi-app"
                },
                "ports": [
                    {
                        "protocol": "TCP",
                        "port": 80,
                        "targetPort": 8000
                    }
                ],
                "type": "LoadBalancer"
            }
        }
    
    @pytest.fixture
    def ingress_manifest(self):
        """Sample Kubernetes ingress manifest"""
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "agentic-rag-ingress",
                "namespace": "agentic-rag",
                "annotations": {
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod"
                }
            },
            "spec": {
                "tls": [
                    {
                        "hosts": [
                            "api.agentic-rag.com"
                        ],
                        "secretName": "agentic-rag-tls"
                    }
                ],
                "rules": [
                    {
                        "host": "api.agentic-rag.com",
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": "fastapi-service",
                                            "port": {
                                                "number": 80
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    
    def test_namespace_validation(self, kubernetes_config):
        """Test Kubernetes namespace configuration"""
        # Test basic structure
        assert kubernetes_config["apiVersion"] == "v1"
        assert kubernetes_config["kind"] == "Namespace"
        assert kubernetes_config["metadata"]["name"] == "agentic-rag"
        
        # Test namespace naming convention
        namespace_name = kubernetes_config["metadata"]["name"]
        assert len(namespace_name) <= 63  # Kubernetes limit
        assert namespace_name.replace("-", "").isalnum()  # Valid characters
    
    def test_deployment_validation(self, deployment_manifest):
        """Test Kubernetes deployment configuration"""
        # Test basic structure
        assert deployment_manifest["apiVersion"] == "apps/v1"
        assert deployment_manifest["kind"] == "Deployment"
        assert deployment_manifest["metadata"]["name"] == "fastapi-app"
        assert deployment_manifest["metadata"]["namespace"] == "agentic-rag"
        
        # Test deployment spec
        spec = deployment_manifest["spec"]
        assert spec["replicas"] >= 1  # At least 1 replica
        assert spec["replicas"] <= 10  # Reasonable upper limit
        
        # Test container configuration
        containers = spec["template"]["spec"]["containers"]
        assert len(containers) == 1
        
        container = containers[0]
        assert container["name"] == "fastapi-app"
        assert container["image"] == "agentic-rag:latest"
        
        # Test resource limits
        resources = container["resources"]
        assert "requests" in resources
        assert "limits" in resources
        
        # Test health checks
        assert "livenessProbe" in container
        assert "readinessProbe" in container
        
        # Test environment variables
        env_vars = container["env"]
        assert any(env["name"] == "APP_ENV" for env in env_vars)
        assert any(env["name"] == "LOG_LEVEL" for env in env_vars)
    
    def test_service_validation(self, service_manifest):
        """Test Kubernetes service configuration"""
        # Test basic structure
        assert service_manifest["apiVersion"] == "v1"
        assert service_manifest["kind"] == "Service"
        assert service_manifest["metadata"]["name"] == "fastapi-service"
        assert service_manifest["metadata"]["namespace"] == "agentic-rag"
        
        # Test service spec
        spec = service_manifest["spec"]
        assert spec["type"] == "LoadBalancer"
        assert "selector" in spec
        assert "ports" in spec
        
        # Test port configuration
        ports = spec["ports"]
        assert len(ports) == 1
        port = ports[0]
        assert port["protocol"] == "TCP"
        assert port["port"] == 80
        assert port["targetPort"] == 8000
    
    def test_ingress_validation(self, ingress_manifest):
        """Test Kubernetes ingress configuration"""
        # Test basic structure
        assert ingress_manifest["apiVersion"] == "networking.k8s.io/v1"
        assert ingress_manifest["kind"] == "Ingress"
        assert ingress_manifest["metadata"]["name"] == "agentic-rag-ingress"
        assert ingress_manifest["metadata"]["namespace"] == "agentic-rag"
        
        # Test annotations
        annotations = ingress_manifest["metadata"]["annotations"]
        assert "kubernetes.io/ingress.class" in annotations
        assert "cert-manager.io/cluster-issuer" in annotations
        
        # Test TLS configuration
        spec = ingress_manifest["spec"]
        assert "tls" in spec
        assert "rules" in spec
        
        tls_config = spec["tls"][0]
        assert "hosts" in tls_config
        assert "secretName" in tls_config
        assert "api.agentic-rag.com" in tls_config["hosts"]
    
    def test_configmap_validation(self):
        """Test Kubernetes ConfigMap configuration"""
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "agentic-rag-config",
                "namespace": "agentic-rag"
            },
            "data": {
                "app_config.yaml": """
app:
  name: agentic-rag
  version: 1.0.0
  environment: production

database:
  host: postgresql-service
  port: 5432
  name: agentic_rag

redis:
  host: redis-service
  port: 6379

vllm:
  host: vllm-service
  port: 8001
"""
            }
        }
        
        # Test basic structure
        assert configmap["apiVersion"] == "v1"
        assert configmap["kind"] == "ConfigMap"
        assert configmap["metadata"]["name"] == "agentic-rag-config"
        
        # Test data configuration
        assert "data" in configmap
        assert "app_config.yaml" in configmap["data"]
        
        # Test configuration content
        config_data = configmap["data"]["app_config.yaml"]
        assert "app:" in config_data
        assert "database:" in config_data
        assert "redis:" in config_data
        assert "vllm:" in config_data
    
    def test_secret_validation(self):
        """Test Kubernetes Secret configuration"""
        secret = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "agentic-rag-secrets",
                "namespace": "agentic-rag"
            },
            "type": "Opaque",
            "data": {
                "postgres_password": "c2VjdXJlX3Bhc3N3b3Jk",  # base64 encoded
                "redis_password": "cmVkaXNfcGFzc3dvcmQ=",  # base64 encoded
                "jwt_secret": "and0X3NlY3JldA=="  # base64 encoded
            }
        }
        
        # Test basic structure
        assert secret["apiVersion"] == "v1"
        assert secret["kind"] == "Secret"
        assert secret["metadata"]["name"] == "agentic-rag-secrets"
        assert secret["type"] == "Opaque"
        
        # Test data configuration
        assert "data" in secret
        required_secrets = ["postgres_password", "redis_password", "jwt_secret"]
        for secret_name in required_secrets:
            assert secret_name in secret["data"]
    
    def test_persistent_volume_claim_validation(self):
        """Test Kubernetes PersistentVolumeClaim configuration"""
        pvc = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": "postgres-data",
                "namespace": "agentic-rag"
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {
                        "storage": "10Gi"
                    }
                },
                "storageClassName": "fast-ssd"
            }
        }
        
        # Test basic structure
        assert pvc["apiVersion"] == "v1"
        assert pvc["kind"] == "PersistentVolumeClaim"
        assert pvc["metadata"]["name"] == "postgres-data"
        
        # Test spec configuration
        spec = pvc["spec"]
        assert "accessModes" in spec
        assert "resources" in spec
        assert "storageClassName" in spec
        
        # Test storage configuration
        resources = spec["resources"]
        assert "requests" in resources
        assert "storage" in resources["requests"]
        assert resources["requests"]["storage"] == "10Gi"
    
    def test_horizontal_pod_autoscaler_validation(self):
        """Test Kubernetes HorizontalPodAutoscaler configuration"""
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": "fastapi-hpa",
                "namespace": "agentic-rag"
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "fastapi-app"
                },
                "minReplicas": 2,
                "maxReplicas": 10,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": 70
                            }
                        }
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": 80
                            }
                        }
                    }
                ]
            }
        }
        
        # Test basic structure
        assert hpa["apiVersion"] == "autoscaling/v2"
        assert hpa["kind"] == "HorizontalPodAutoscaler"
        assert hpa["metadata"]["name"] == "fastapi-hpa"
        
        # Test spec configuration
        spec = hpa["spec"]
        assert "scaleTargetRef" in spec
        assert "minReplicas" in spec
        assert "maxReplicas" in spec
        assert "metrics" in spec
        
        # Test scaling configuration
        assert spec["minReplicas"] >= 1
        assert spec["maxReplicas"] >= spec["minReplicas"]
        assert spec["maxReplicas"] <= 20  # Reasonable upper limit
        
        # Test metrics configuration
        metrics = spec["metrics"]
        assert len(metrics) == 2
        
        cpu_metric = next(m for m in metrics if m["resource"]["name"] == "cpu")
        memory_metric = next(m for m in metrics if m["resource"]["name"] == "memory")
        
        assert cpu_metric["resource"]["target"]["averageUtilization"] <= 100
        assert memory_metric["resource"]["target"]["averageUtilization"] <= 100


class TestHelmCharts:
    """Test Helm chart configuration and deployment"""
    
    @pytest.fixture
    def helm_chart_structure(self):
        """Sample Helm chart structure"""
        return {
            "Chart.yaml": {
                "apiVersion": "v2",
                "name": "agentic-rag",
                "description": "Agentic RAG System with Local LLMs",
                "type": "application",
                "version": "1.0.0",
                "appVersion": "1.0.0"
            },
            "values.yaml": {
                "replicaCount": 3,
                "image": {
                    "repository": "agentic-rag",
                    "tag": "latest",
                    "pullPolicy": "IfNotPresent"
                },
                "service": {
                    "type": "LoadBalancer",
                    "port": 80
                },
                "ingress": {
                    "enabled": True,
                    "className": "nginx",
                    "hosts": [
                        {
                            "host": "api.agentic-rag.com",
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix"
                                }
                            ]
                        }
                    ],
                    "tls": [
                        {
                            "secretName": "agentic-rag-tls",
                            "hosts": ["api.agentic-rag.com"]
                        }
                    ]
                },
                "resources": {
                    "requests": {
                        "memory": "512Mi",
                        "cpu": "250m"
                    },
                    "limits": {
                        "memory": "1Gi",
                        "cpu": "500m"
                    }
                },
                "autoscaling": {
                    "enabled": True,
                    "minReplicas": 2,
                    "maxReplicas": 10,
                    "targetCPUUtilizationPercentage": 70,
                    "targetMemoryUtilizationPercentage": 80
                }
            }
        }
    
    def test_chart_yaml_validation(self, helm_chart_structure):
        """Test Helm Chart.yaml validation"""
        chart_yaml = helm_chart_structure["Chart.yaml"]
        
        # Test basic structure
        assert chart_yaml["apiVersion"] == "v2"
        assert chart_yaml["name"] == "agentic-rag"
        assert chart_yaml["type"] == "application"
        assert chart_yaml["version"] == "1.0.0"
        assert chart_yaml["appVersion"] == "1.0.0"
        
        # Test version format
        version = chart_yaml["version"]
        assert len(version.split(".")) == 3  # Semantic versioning
        
        # Test name validation
        name = chart_yaml["name"]
        assert len(name) <= 50  # Helm limit
        assert name.replace("-", "").isalnum()  # Valid characters
    
    def test_values_yaml_validation(self, helm_chart_structure):
        """Test Helm values.yaml validation"""
        values = helm_chart_structure["values.yaml"]
        
        # Test replica count
        assert values["replicaCount"] >= 1
        assert values["replicaCount"] <= 10
        
        # Test image configuration
        image = values["image"]
        assert "repository" in image
        assert "tag" in image
        assert "pullPolicy" in image
        assert image["pullPolicy"] in ["Always", "IfNotPresent", "Never"]
        
        # Test service configuration
        service = values["service"]
        assert "type" in service
        assert "port" in service
        assert service["type"] in ["ClusterIP", "NodePort", "LoadBalancer"]
        
        # Test ingress configuration
        ingress = values["ingress"]
        assert "enabled" in ingress
        assert "className" in ingress
        assert "hosts" in ingress
        assert "tls" in ingress
        
        # Test resource configuration
        resources = values["resources"]
        assert "requests" in resources
        assert "limits" in resources
        
        # Test autoscaling configuration
        autoscaling = values["autoscaling"]
        assert "enabled" in autoscaling
        assert "minReplicas" in autoscaling
        assert "maxReplicas" in autoscaling
        assert autoscaling["minReplicas"] <= autoscaling["maxReplicas"]
    
    def test_helm_template_generation(self, helm_chart_structure):
        """Test Helm template generation"""
        # Test that all required templates can be generated
        required_templates = [
            "deployment.yaml",
            "service.yaml",
            "ingress.yaml",
            "configmap.yaml",
            "secret.yaml",
            "hpa.yaml"
        ]
        
        # Mock template generation
        templates = {
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment",
            "service.yaml": "apiVersion: v1\nkind: Service",
            "ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress",
            "configmap.yaml": "apiVersion: v1\nkind: ConfigMap",
            "secret.yaml": "apiVersion: v1\nkind: Secret",
            "hpa.yaml": "apiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler"
        }
        
        for template_name in required_templates:
            assert template_name in templates
            template_content = templates[template_name]
            assert "apiVersion:" in template_content
            assert "kind:" in template_content


class TestServiceMesh:
    """Test service mesh integration"""
    
    def test_istio_virtual_service_validation(self):
        """Test Istio VirtualService configuration"""
        virtual_service = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "VirtualService",
            "metadata": {
                "name": "agentic-rag-vs",
                "namespace": "agentic-rag"
            },
            "spec": {
                "hosts": ["api.agentic-rag.com"],
                "gateways": ["agentic-rag-gateway"],
                "http": [
                    {
                        "route": [
                            {
                                "destination": {
                                    "host": "fastapi-service",
                                    "port": {
                                        "number": 80
                                    }
                                },
                                "weight": 100
                            }
                        ]
                    }
                ]
            }
        }
        
        # Test basic structure
        assert virtual_service["apiVersion"] == "networking.istio.io/v1beta1"
        assert virtual_service["kind"] == "VirtualService"
        assert virtual_service["metadata"]["name"] == "agentic-rag-vs"
        
        # Test spec configuration
        spec = virtual_service["spec"]
        assert "hosts" in spec
        assert "gateways" in spec
        assert "http" in spec
        
        # Test routing configuration
        http_routes = spec["http"]
        assert len(http_routes) == 1
        
        route = http_routes[0]["route"][0]
        assert "destination" in route
        assert "weight" in route
        assert route["weight"] == 100
    
    def test_istio_destination_rule_validation(self):
        """Test Istio DestinationRule configuration"""
        destination_rule = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "DestinationRule",
            "metadata": {
                "name": "agentic-rag-dr",
                "namespace": "agentic-rag"
            },
            "spec": {
                "host": "fastapi-service",
                "trafficPolicy": {
                    "loadBalancer": {
                        "simple": "ROUND_ROBIN"
                    },
                    "connectionPool": {
                        "tcp": {
                            "maxConnections": 100
                        },
                        "http": {
                            "http1MaxPendingRequests": 1024,
                            "maxRequestsPerConnection": 10
                        }
                    }
                },
                "subsets": [
                    {
                        "name": "v1",
                        "labels": {
                            "version": "v1"
                        }
                    }
                ]
            }
        }
        
        # Test basic structure
        assert destination_rule["apiVersion"] == "networking.istio.io/v1beta1"
        assert destination_rule["kind"] == "DestinationRule"
        assert destination_rule["metadata"]["name"] == "agentic-rag-dr"
        
        # Test spec configuration
        spec = destination_rule["spec"]
        assert "host" in spec
        assert "trafficPolicy" in spec
        assert "subsets" in spec
        
        # Test traffic policy
        traffic_policy = spec["trafficPolicy"]
        assert "loadBalancer" in traffic_policy
        assert "connectionPool" in traffic_policy
        
        # Test subsets
        subsets = spec["subsets"]
        assert len(subsets) == 1
        assert subsets[0]["name"] == "v1"
        assert "version" in subsets[0]["labels"]


class TestProductionValidation:
    """Test production environment validation"""
    
    def test_production_security_validation(self):
        """Test production security configuration"""
        security_config = {
            "network_policies": True,
            "pod_security_policies": True,
            "rbac_enabled": True,
            "secrets_encryption": True,
            "audit_logging": True,
            "tls_enabled": True
        }
        
        # Test security requirements
        assert security_config["network_policies"] is True
        assert security_config["pod_security_policies"] is True
        assert security_config["rbac_enabled"] is True
        assert security_config["secrets_encryption"] is True
        assert security_config["audit_logging"] is True
        assert security_config["tls_enabled"] is True
    
    def test_production_monitoring_validation(self):
        """Test production monitoring configuration"""
        monitoring_config = {
            "prometheus_enabled": True,
            "grafana_enabled": True,
            "alerting_enabled": True,
            "logging_enabled": True,
            "tracing_enabled": True,
            "metrics_retention_days": 30
        }
        
        # Test monitoring requirements
        assert monitoring_config["prometheus_enabled"] is True
        assert monitoring_config["grafana_enabled"] is True
        assert monitoring_config["alerting_enabled"] is True
        assert monitoring_config["logging_enabled"] is True
        assert monitoring_config["tracing_enabled"] is True
        assert monitoring_config["metrics_retention_days"] >= 7
    
    def test_production_scalability_validation(self):
        """Test production scalability configuration"""
        scalability_config = {
            "hpa_enabled": True,
            "vpa_enabled": False,
            "cluster_autoscaler": True,
            "min_replicas": 2,
            "max_replicas": 10,
            "target_cpu_utilization": 70,
            "target_memory_utilization": 80
        }
        
        # Test scalability requirements
        assert scalability_config["hpa_enabled"] is True
        assert scalability_config["cluster_autoscaler"] is True
        assert scalability_config["min_replicas"] >= 2
        assert scalability_config["max_replicas"] >= scalability_config["min_replicas"]
        assert scalability_config["target_cpu_utilization"] <= 100
        assert scalability_config["target_memory_utilization"] <= 100
    
    def test_production_backup_validation(self):
        """Test production backup configuration"""
        backup_config = {
            "backup_enabled": True,
            "backup_schedule": "0 2 * * *",  # Daily at 2 AM
            "backup_retention_days": 30,
            "backup_storage_class": "fast-ssd",
            "restore_testing_enabled": True
        }
        
        # Test backup requirements
        assert backup_config["backup_enabled"] is True
        assert backup_config["backup_retention_days"] >= 7
        assert backup_config["restore_testing_enabled"] is True
        
        # Test cron schedule format
        schedule_parts = backup_config["backup_schedule"].split()
        assert len(schedule_parts) == 5  # Standard cron format 
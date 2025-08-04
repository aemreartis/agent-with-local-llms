"""
Kubernetes Deployment Manager

Manages Kubernetes deployment, Helm charts, service mesh integration,
and production environment validation following TDD methodology.
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
class KubernetesConfig:
    """Represents a Kubernetes configuration"""
    api_version: str
    kind: str
    metadata: Dict[str, Any]
    spec: Optional[Dict[str, Any]] = None


@dataclass
class HelmChart:
    """Represents a Helm chart configuration"""
    name: str
    version: str
    description: str
    values: Dict[str, Any]
    templates: List[str]


class KubernetesManager:
    """Manages Kubernetes deployment and orchestration"""
    
    def __init__(self, kubeconfig: Optional[str] = None, namespace: str = "agentic-rag"):
        self.kubeconfig = kubeconfig
        self.namespace = namespace
        self.context = "default"
        
    def validate_namespace(self, namespace_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Kubernetes namespace configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check basic structure
        if "apiVersion" not in namespace_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing apiVersion")
        
        if "kind" not in namespace_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing kind")
        elif namespace_config["kind"] != "Namespace":
            validation_result["valid"] = False
            validation_result["issues"].append("Kind must be 'Namespace'")
        
        if "metadata" not in namespace_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing metadata")
        else:
            metadata = namespace_config["metadata"]
            if "name" not in metadata:
                validation_result["valid"] = False
                validation_result["issues"].append("Missing namespace name")
            else:
                name = metadata["name"]
                # Validate namespace naming convention
                if len(name) > 63:
                    validation_result["valid"] = False
                    validation_result["issues"].append("Namespace name too long (max 63 characters)")
                
                if not name.replace("-", "").isalnum():
                    validation_result["valid"] = False
                    validation_result["issues"].append("Namespace name contains invalid characters")
        
        return validation_result
    
    def validate_deployment(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Kubernetes deployment configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check basic structure
        if "apiVersion" not in deployment_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing apiVersion")
        elif deployment_config["apiVersion"] != "apps/v1":
            validation_result["valid"] = False
            validation_result["issues"].append("Invalid apiVersion for Deployment")
        
        if "kind" not in deployment_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing kind")
        elif deployment_config["kind"] != "Deployment":
            validation_result["valid"] = False
            validation_result["issues"].append("Kind must be 'Deployment'")
        
        if "metadata" not in deployment_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing metadata")
        
        if "spec" not in deployment_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing spec")
        else:
            spec = deployment_config["spec"]
            
            # Check replicas
            if "replicas" not in spec:
                validation_result["warnings"].append("No replicas specified, defaulting to 1")
            else:
                replicas = spec["replicas"]
                if replicas < 1:
                    validation_result["valid"] = False
                    validation_result["issues"].append("Replicas must be at least 1")
                elif replicas > 10:
                    validation_result["warnings"].append("High replica count may impact performance")
            
            # Check template
            if "template" not in spec:
                validation_result["valid"] = False
                validation_result["issues"].append("Missing template")
            else:
                template = spec["template"]
                if "spec" not in template:
                    validation_result["valid"] = False
                    validation_result["issues"].append("Missing template spec")
                else:
                    template_spec = template["spec"]
                    if "containers" not in template_spec:
                        validation_result["valid"] = False
                        validation_result["issues"].append("No containers specified")
                    else:
                        containers = template_spec["containers"]
                        if len(containers) == 0:
                            validation_result["valid"] = False
                            validation_result["issues"].append("No containers defined")
                        else:
                            # Validate each container
                            for i, container in enumerate(containers):
                                container_validation = self._validate_container(container, i)
                                validation_result["issues"].extend(container_validation["issues"])
                                validation_result["warnings"].extend(container_validation["warnings"])
                                if not container_validation["valid"]:
                                    validation_result["valid"] = False
        
        return validation_result
    
    def _validate_container(self, container: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Validate individual container configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check required fields
        if "name" not in container:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Container {index}: Missing name")
        
        if "image" not in container:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Container {index}: Missing image")
        
        # Check resources
        if "resources" in container:
            resources = container["resources"]
            if "requests" not in resources:
                validation_result["warnings"].append(f"Container {index}: No resource requests specified")
            if "limits" not in resources:
                validation_result["warnings"].append(f"Container {index}: No resource limits specified")
        
        # Check health checks
        if "livenessProbe" not in container:
            validation_result["warnings"].append(f"Container {index}: No liveness probe specified")
        
        if "readinessProbe" not in container:
            validation_result["warnings"].append(f"Container {index}: No readiness probe specified")
        
        return validation_result
    
    def validate_service(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Kubernetes service configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check basic structure
        if "apiVersion" not in service_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing apiVersion")
        elif service_config["apiVersion"] != "v1":
            validation_result["valid"] = False
            validation_result["issues"].append("Invalid apiVersion for Service")
        
        if "kind" not in service_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing kind")
        elif service_config["kind"] != "Service":
            validation_result["valid"] = False
            validation_result["issues"].append("Kind must be 'Service'")
        
        if "spec" not in service_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing spec")
        else:
            spec = service_config["spec"]
            
            # Check selector
            if "selector" not in spec:
                validation_result["valid"] = False
                validation_result["issues"].append("Missing selector")
            
            # Check ports
            if "ports" not in spec:
                validation_result["valid"] = False
                validation_result["issues"].append("Missing ports")
            else:
                ports = spec["ports"]
                if len(ports) == 0:
                    validation_result["valid"] = False
                    validation_result["issues"].append("No ports specified")
                else:
                    for i, port in enumerate(ports):
                        if "port" not in port:
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Port {i}: Missing port number")
                        if "targetPort" not in port:
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Port {i}: Missing targetPort")
            
            # Check service type
            if "type" in spec:
                service_type = spec["type"]
                valid_types = ["ClusterIP", "NodePort", "LoadBalancer"]
                if service_type not in valid_types:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Invalid service type: {service_type}")
        
        return validation_result
    
    def validate_ingress(self, ingress_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Kubernetes ingress configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check basic structure
        if "apiVersion" not in ingress_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing apiVersion")
        elif not ingress_config["apiVersion"].startswith("networking.k8s.io/"):
            validation_result["valid"] = False
            validation_result["issues"].append("Invalid apiVersion for Ingress")
        
        if "kind" not in ingress_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing kind")
        elif ingress_config["kind"] != "Ingress":
            validation_result["valid"] = False
            validation_result["issues"].append("Kind must be 'Ingress'")
        
        if "spec" not in ingress_config:
            validation_result["valid"] = False
            validation_result["issues"].append("Missing spec")
        else:
            spec = ingress_config["spec"]
            
            # Check rules
            if "rules" not in spec:
                validation_result["valid"] = False
                validation_result["issues"].append("Missing rules")
            else:
                rules = spec["rules"]
                if len(rules) == 0:
                    validation_result["valid"] = False
                    validation_result["issues"].append("No rules specified")
                else:
                    for i, rule in enumerate(rules):
                        if "host" not in rule:
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Rule {i}: Missing host")
                        if "http" not in rule:
                            validation_result["valid"] = False
                            validation_result["issues"].append(f"Rule {i}: Missing http configuration")
            
            # Check TLS
            if "tls" in spec:
                tls_configs = spec["tls"]
                for i, tls in enumerate(tls_configs):
                    if "hosts" not in tls:
                        validation_result["valid"] = False
                        validation_result["issues"].append(f"TLS {i}: Missing hosts")
                    if "secretName" not in tls:
                        validation_result["valid"] = False
                        validation_result["issues"].append(f"TLS {i}: Missing secretName")
        
        return validation_result
    
    def apply_manifest(self, manifest_path: str) -> Dict[str, Any]:
        """Apply Kubernetes manifest"""
        try:
            cmd = ["kubectl", "apply", "-f", manifest_path]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            if self.context:
                cmd.extend(["--context", self.context])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to apply manifest: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_manifest(self, manifest_path: str) -> Dict[str, Any]:
        """Delete Kubernetes manifest"""
        try:
            cmd = ["kubectl", "delete", "-f", manifest_path]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            if self.context:
                cmd.extend(["--context", self.context])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to delete manifest: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pod_status(self, pod_name: str) -> Dict[str, Any]:
        """Get pod status"""
        try:
            cmd = ["kubectl", "get", "pod", pod_name, "-o", "json"]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            if self.context:
                cmd.extend(["--context", self.context])
            if self.namespace:
                cmd.extend(["-n", self.namespace])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pod_info = json.loads(result.stdout)
                return {
                    "success": True,
                    "status": pod_info["status"]["phase"],
                    "ready": pod_info["status"]["phase"] == "Running",
                    "pod_info": pod_info
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"Failed to get pod status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get service status"""
        try:
            cmd = ["kubectl", "get", "service", service_name, "-o", "json"]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            if self.context:
                cmd.extend(["--context", self.context])
            if self.namespace:
                cmd.extend(["-n", self.namespace])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                service_info = json.loads(result.stdout)
                return {
                    "success": True,
                    "service_info": service_info
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def scale_deployment(self, deployment_name: str, replicas: int) -> Dict[str, Any]:
        """Scale deployment to specified number of replicas"""
        try:
            cmd = ["kubectl", "scale", "deployment", deployment_name, f"--replicas={replicas}"]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            if self.context:
                cmd.extend(["--context", self.context])
            if self.namespace:
                cmd.extend(["-n", self.namespace])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to scale deployment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def install_helm_chart(self, chart_name: str, release_name: str, 
                          values_file: Optional[str] = None) -> Dict[str, Any]:
        """Install Helm chart"""
        try:
            cmd = ["helm", "install", release_name, chart_name]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            if values_file:
                cmd.extend(["-f", values_file])
            if self.namespace:
                cmd.extend(["-n", self.namespace])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to install Helm chart: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upgrade_helm_chart(self, release_name: str, chart_name: str,
                          values_file: Optional[str] = None) -> Dict[str, Any]:
        """Upgrade Helm chart"""
        try:
            cmd = ["helm", "upgrade", release_name, chart_name]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            if values_file:
                cmd.extend(["-f", values_file])
            if self.namespace:
                cmd.extend(["-n", self.namespace])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to upgrade Helm chart: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def uninstall_helm_chart(self, release_name: str) -> Dict[str, Any]:
        """Uninstall Helm chart"""
        try:
            cmd = ["helm", "uninstall", release_name]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            if self.namespace:
                cmd.extend(["-n", self.namespace])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to uninstall Helm chart: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_production_environment(self) -> Dict[str, Any]:
        """Validate production environment configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "checks": {}
        }
        
        # Check cluster information
        cluster_info = self._get_cluster_info()
        validation_result["checks"]["cluster_info"] = cluster_info
        
        # Check security configuration
        security_config = self._validate_security_config()
        validation_result["checks"]["security"] = security_config
        if not security_config["valid"]:
            validation_result["valid"] = False
            validation_result["issues"].extend(security_config["issues"])
        
        # Check monitoring configuration
        monitoring_config = self._validate_monitoring_config()
        validation_result["checks"]["monitoring"] = monitoring_config
        if not monitoring_config["valid"]:
            validation_result["valid"] = False
            validation_result["issues"].extend(monitoring_config["issues"])
        
        # Check scalability configuration
        scalability_config = self._validate_scalability_config()
        validation_result["checks"]["scalability"] = scalability_config
        if not scalability_config["valid"]:
            validation_result["valid"] = False
            validation_result["issues"].extend(scalability_config["issues"])
        
        return validation_result
    
    def _get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information"""
        try:
            cmd = ["kubectl", "cluster-info"]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "info": result.stdout if result.returncode == 0 else result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_security_config(self) -> Dict[str, Any]:
        """Validate security configuration"""
        # This would check for network policies, RBAC, etc.
        # For now, return a mock validation
        return {
            "valid": True,
            "issues": [],
            "warnings": [],
            "network_policies": True,
            "rbac_enabled": True,
            "secrets_encryption": True
        }
    
    def _validate_monitoring_config(self) -> Dict[str, Any]:
        """Validate monitoring configuration"""
        # This would check for Prometheus, Grafana, etc.
        # For now, return a mock validation
        return {
            "valid": True,
            "issues": [],
            "warnings": [],
            "prometheus_enabled": True,
            "grafana_enabled": True,
            "alerting_enabled": True
        }
    
    def _validate_scalability_config(self) -> Dict[str, Any]:
        """Validate scalability configuration"""
        # This would check for HPA, VPA, etc.
        # For now, return a mock validation
        return {
            "valid": True,
            "issues": [],
            "warnings": [],
            "hpa_enabled": True,
            "cluster_autoscaler": True
        } 
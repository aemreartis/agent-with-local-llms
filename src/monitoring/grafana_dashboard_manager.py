"""
Grafana Dashboard Manager

Manages Grafana dashboard creation, updates, and deletion through the Grafana API.
"""

import requests
import json
from typing import Dict, List, Any, Optional
from .dashboard_configs import DashboardConfigs


class GrafanaDashboardManager:
    """Manages Grafana dashboards through API"""
    
    def __init__(self, grafana_url: str, api_key: str):
        """Initialize dashboard manager
        
        Args:
            grafana_url: Grafana server URL
            api_key: Grafana API key
        """
        self.grafana_url = grafana_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.dashboard_configs = DashboardConfigs()
    
    def get_dashboards(self) -> List[Dict[str, Any]]:
        """Get all dashboards from Grafana
        
        Returns:
            List of dashboard configurations
        """
        url = f"{self.grafana_url}/api/search"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_dashboard(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard in Grafana
        
        Args:
            dashboard_config: Dashboard configuration
            
        Returns:
            Creation result
        """
        if not self.validate_dashboard_config(dashboard_config):
            raise ValueError("Invalid dashboard configuration")
        
        payload = self.build_dashboard_payload(dashboard_config)
        url = f"{self.grafana_url}/api/dashboards/db"
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def update_dashboard(self, dashboard_id: int, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing dashboard in Grafana
        
        Args:
            dashboard_id: Dashboard ID
            dashboard_config: Updated dashboard configuration
            
        Returns:
            Update result
        """
        if not self.validate_dashboard_config(dashboard_config):
            raise ValueError("Invalid dashboard configuration")
        
        # Get current dashboard to preserve ID and version
        current_dashboard = self.get_dashboard(dashboard_id)
        if not current_dashboard:
            raise ValueError(f"Dashboard {dashboard_id} not found")
        
        # Update configuration
        dashboard_config['id'] = dashboard_id
        dashboard_config['version'] = current_dashboard['dashboard']['version'] + 1
        
        payload = self.build_dashboard_payload(dashboard_config)
        url = f"{self.grafana_url}/api/dashboards/db"
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def delete_dashboard(self, dashboard_id: int) -> Dict[str, Any]:
        """Delete a dashboard from Grafana
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Deletion result
        """
        url = f"{self.grafana_url}/api/dashboards/uid/{dashboard_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return {'status': 'success'}
    
    def get_dashboard(self, dashboard_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific dashboard by ID
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Dashboard configuration or None if not found
        """
        url = f"{self.grafana_url}/api/dashboards/id/{dashboard_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def dashboard_exists(self, dashboard_title: str) -> bool:
        """Check if a dashboard exists by title
        
        Args:
            dashboard_title: Dashboard title
            
        Returns:
            True if dashboard exists, False otherwise
        """
        try:
            dashboards = self.get_dashboards()
            return any(d.get('title') == dashboard_title for d in dashboards)
        except Exception:
            return False
    
    def validate_dashboard_config(self, config: Dict[str, Any]) -> bool:
        """Validate dashboard configuration
        
        Args:
            config: Dashboard configuration
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'panels']
        return all(field in config for field in required_fields)
    
    def build_dashboard_payload(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build payload for Grafana API
        
        Args:
            dashboard_config: Dashboard configuration
            
        Returns:
            API payload
        """
        return {
            'dashboard': dashboard_config,
            'overwrite': True
        }
    
    def create_all_dashboards(self) -> Dict[str, List[str]]:
        """Create all predefined dashboards
        
        Returns:
            Dictionary with created and failed dashboard names
        """
        configs = self.dashboard_configs.get_all_configs()
        created = []
        failed = []
        
        for name, config in configs.items():
            try:
                if not self.dashboard_exists(config['title']):
                    result = self.create_dashboard(config)
                    created.append(config['title'])
                else:
                    created.append(f"{config['title']} (already exists)")
            except Exception as e:
                failed.append(f"{config['title']}: {str(e)}")
        
        return {
            'created': created,
            'failed': failed
        }
    
    def health_check(self) -> bool:
        """Check if Grafana is accessible
        
        Returns:
            True if accessible, False otherwise
        """
        try:
            url = f"{self.grafana_url}/api/health"
            response = requests.get(url, headers=self.headers, timeout=5)
            return response.status_code == 200
        except Exception:
            return False 
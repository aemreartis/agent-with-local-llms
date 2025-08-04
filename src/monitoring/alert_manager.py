"""
Alert Manager

Manages Grafana alert rules and notification channels through the Grafana API.
"""

import requests
import json
from typing import Dict, List, Any, Optional
from .alert_rules import AlertRules
from .notification_channels import NotificationChannels


class AlertManager:
    """Manages Grafana alerts and notifications through API"""
    
    def __init__(self, grafana_url: str, api_key: str):
        """Initialize alert manager
        
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
        self.alert_rules = AlertRules()
        self.notification_channels = NotificationChannels()
    
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get all alert rules from Grafana
        
        Returns:
            List of alert rule configurations
        """
        url = f"{self.grafana_url}/api/v1/provisioning/alert-rules"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_alert_rule(self, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert rule in Grafana
        
        Args:
            rule_config: Alert rule configuration
            
        Returns:
            Creation result
        """
        if not self.validate_alert_rule_config(rule_config):
            raise ValueError("Invalid alert rule configuration")
        
        payload = self.build_alert_rule_payload(rule_config)
        url = f"{self.grafana_url}/api/v1/provisioning/alert-rules"
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def update_alert_rule(self, rule_id: int, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing alert rule in Grafana
        
        Args:
            rule_id: Alert rule ID
            rule_config: Updated alert rule configuration
            
        Returns:
            Update result
        """
        if not self.validate_alert_rule_config(rule_config):
            raise ValueError("Invalid alert rule configuration")
        
        payload = self.build_alert_rule_payload(rule_config)
        url = f"{self.grafana_url}/api/v1/provisioning/alert-rules/{rule_id}"
        
        response = requests.put(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def delete_alert_rule(self, rule_id: int) -> Dict[str, Any]:
        """Delete an alert rule from Grafana
        
        Args:
            rule_id: Alert rule ID
            
        Returns:
            Deletion result
        """
        url = f"{self.grafana_url}/api/v1/provisioning/alert-rules/{rule_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return {'status': 'success'}
    
    def get_notification_channels(self) -> List[Dict[str, Any]]:
        """Get all notification channels from Grafana
        
        Returns:
            List of notification channel configurations
        """
        url = f"{self.grafana_url}/api/alert-notifications"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_notification_channel(self, channel_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notification channel in Grafana
        
        Args:
            channel_config: Notification channel configuration
            
        Returns:
            Creation result
        """
        if not self.validate_notification_channel_config(channel_config):
            raise ValueError("Invalid notification channel configuration")
        
        url = f"{self.grafana_url}/api/alert-notifications"
        response = requests.post(url, headers=self.headers, json=channel_config)
        response.raise_for_status()
        return response.json()
    
    def update_notification_channel(self, channel_id: int, channel_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing notification channel in Grafana
        
        Args:
            channel_id: Notification channel ID
            channel_config: Updated notification channel configuration
            
        Returns:
            Update result
        """
        if not self.validate_notification_channel_config(channel_config):
            raise ValueError("Invalid notification channel configuration")
        
        url = f"{self.grafana_url}/api/alert-notifications/{channel_id}"
        response = requests.put(url, headers=self.headers, json=channel_config)
        response.raise_for_status()
        return response.json()
    
    def delete_notification_channel(self, channel_id: int) -> Dict[str, Any]:
        """Delete a notification channel from Grafana
        
        Args:
            channel_id: Notification channel ID
            
        Returns:
            Deletion result
        """
        url = f"{self.grafana_url}/api/alert-notifications/{channel_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return {'status': 'success'}
    
    def validate_alert_rule_config(self, config: Dict[str, Any]) -> bool:
        """Validate alert rule configuration
        
        Args:
            config: Alert rule configuration
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['name', 'condition', 'duration']
        return all(field in config for field in required_fields)
    
    def validate_notification_channel_config(self, config: Dict[str, Any]) -> bool:
        """Validate notification channel configuration
        
        Args:
            config: Notification channel configuration
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['name', 'type', 'settings']
        return all(field in config for field in required_fields)
    
    def build_alert_rule_payload(self, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build payload for Grafana alert rule API
        
        Args:
            rule_config: Alert rule configuration
            
        Returns:
            API payload
        """
        return {
            'name': rule_config['name'],
            'condition': rule_config['condition'],
            'duration': rule_config['duration'],
            'severity': rule_config.get('severity', 'warning'),
            'annotations': rule_config.get('annotations', {}),
            'labels': rule_config.get('labels', {})
        }
    
    def alert_rule_exists(self, rule_name: str) -> bool:
        """Check if an alert rule exists by name
        
        Args:
            rule_name: Alert rule name
            
        Returns:
            True if alert rule exists, False otherwise
        """
        try:
            rules = self.get_alert_rules()
            return any(r.get('name') == rule_name for r in rules)
        except Exception:
            return False
    
    def notification_channel_exists(self, channel_name: str) -> bool:
        """Check if a notification channel exists by name
        
        Args:
            channel_name: Notification channel name
            
        Returns:
            True if notification channel exists, False otherwise
        """
        channels = self.get_notification_channels()
        return any(c['name'] == channel_name for c in channels)
    
    def create_all_alert_rules(self) -> Dict[str, List[str]]:
        """Create all predefined alert rules
        
        Returns:
            Dictionary with created and failed alert rule names
        """
        rules = self.alert_rules.get_all_rules()
        created = []
        failed = []
        
        for name, rule in rules.items():
            try:
                if not self.alert_rule_exists(rule['name']):
                    result = self.create_alert_rule(rule)
                    created.append(rule['name'])
                else:
                    created.append(f"{rule['name']} (already exists)")
            except Exception as e:
                failed.append(f"{rule['name']}: {str(e)}")
        
        return {
            'created': created,
            'failed': failed
        }
    
    def create_all_notification_channels(self) -> Dict[str, List[str]]:
        """Create all predefined notification channels
        
        Returns:
            Dictionary with created and failed notification channel names
        """
        channels = self.notification_channels.get_all_channels()
        created = []
        failed = []
        
        for name, channel in channels.items():
            try:
                if not self.notification_channel_exists(channel['name']):
                    result = self.create_notification_channel(channel)
                    created.append(channel['name'])
                else:
                    created.append(f"{channel['name']} (already exists)")
            except Exception as e:
                failed.append(f"{channel['name']}: {str(e)}")
        
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
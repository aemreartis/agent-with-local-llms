"""
Alerting System Tests

Tests for comprehensive alerting system configuration and management.
Following TDD methodology: Tests first, then implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from typing import Dict, List, Any

from src.monitoring.alert_manager import AlertManager
from src.monitoring.alert_rules import AlertRules
from src.monitoring.notification_channels import NotificationChannels


class TestAlertRules:
    """Test alert rule definitions"""
    
    @pytest.fixture
    def alert_rules(self):
        """Create alert rules instance"""
        return AlertRules()
    
    def test_high_error_rate_alert_rule(self, alert_rules):
        """Test high error rate alert rule"""
        rule = alert_rules.get_high_error_rate_rule()
        
        assert rule is not None
        assert 'name' in rule
        assert rule['name'] == 'High Error Rate'
        assert 'condition' in rule
        assert 'threshold' in rule
        assert 'duration' in rule
        assert rule['threshold'] > 0
        assert len(rule['duration']) > 0
    
    def test_performance_degradation_alert_rule(self, alert_rules):
        """Test performance degradation alert rule"""
        rule = alert_rules.get_performance_degradation_rule()
        
        assert rule is not None
        assert 'name' in rule
        assert rule['name'] == 'Performance Degradation'
        assert 'condition' in rule
        assert 'threshold' in rule
        assert 'duration' in rule
        assert rule['threshold'] > 0
        assert len(rule['duration']) > 0
    
    def test_resource_usage_alert_rule(self, alert_rules):
        """Test resource usage alert rule"""
        rule = alert_rules.get_resource_usage_rule()
        
        assert rule is not None
        assert 'name' in rule
        assert rule['name'] == 'High Resource Usage'
        assert 'condition' in rule
        assert 'threshold' in rule
        assert 'duration' in rule
        assert rule['threshold'] > 0
        assert len(rule['duration']) > 0
    
    def test_business_metric_alert_rule(self, alert_rules):
        """Test business metric alert rule"""
        rule = alert_rules.get_business_metric_rule()
        
        assert rule is not None
        assert 'name' in rule
        assert rule['name'] == 'Business Metric Alert'
        assert 'condition' in rule
        assert 'threshold' in rule
        assert 'duration' in rule
        assert rule['threshold'] > 0
        assert len(rule['duration']) > 0
    
    def test_llm_provider_alert_rule(self, alert_rules):
        """Test LLM provider alert rule"""
        rule = alert_rules.get_llm_provider_rule()
        
        assert rule is not None
        assert 'name' in rule
        assert rule['name'] == 'LLM Provider Issues'
        assert 'condition' in rule
        assert 'threshold' in rule
        assert 'duration' in rule
        assert rule['threshold'] > 0
        assert len(rule['duration']) > 0
    
    def test_vector_store_alert_rule(self, alert_rules):
        """Test vector store alert rule"""
        rule = alert_rules.get_vector_store_rule()
        
        assert rule is not None
        assert 'name' in rule
        assert rule['name'] == 'Vector Store Issues'
        assert 'condition' in rule
        assert 'threshold' in rule
        assert 'duration' in rule
        assert rule['threshold'] > 0
        assert len(rule['duration']) > 0
    
    def test_memory_provider_alert_rule(self, alert_rules):
        """Test memory provider alert rule"""
        rule = alert_rules.get_memory_provider_rule()
        
        assert rule is not None
        assert 'name' in rule
        assert rule['name'] == 'Memory Provider Issues'
        assert 'condition' in rule
        assert 'threshold' in rule
        assert 'duration' in rule
        assert rule['threshold'] > 0
        assert len(rule['duration']) > 0
    
    def test_all_alert_rules(self, alert_rules):
        """Test all alert rules are available"""
        rules = alert_rules.get_all_rules()
        
        assert isinstance(rules, dict)
        assert 'high_error_rate' in rules
        assert 'performance_degradation' in rules
        assert 'resource_usage' in rules
        assert 'business_metric' in rules
        assert 'llm_provider' in rules
        assert 'vector_store' in rules
        assert 'memory_provider' in rules


class TestNotificationChannels:
    """Test notification channel definitions"""
    
    @pytest.fixture
    def notification_channels(self):
        """Create notification channels instance"""
        return NotificationChannels()
    
    def test_email_notification_channel(self, notification_channels):
        """Test email notification channel"""
        channel = notification_channels.get_email_channel()
        
        assert channel is not None
        assert 'name' in channel
        assert channel['name'] == 'Email Notifications'
        assert 'type' in channel
        assert channel['type'] == 'email'
        assert 'settings' in channel
        assert isinstance(channel['settings'], dict)
    
    def test_slack_notification_channel(self, notification_channels):
        """Test Slack notification channel"""
        channel = notification_channels.get_slack_channel()
        
        assert channel is not None
        assert 'name' in channel
        assert channel['name'] == 'Slack Notifications'
        assert 'type' in channel
        assert channel['type'] == 'slack'
        assert 'settings' in channel
        assert isinstance(channel['settings'], dict)
    
    def test_webhook_notification_channel(self, notification_channels):
        """Test webhook notification channel"""
        channel = notification_channels.get_webhook_channel()
        
        assert channel is not None
        assert 'name' in channel
        assert channel['name'] == 'Webhook Notifications'
        assert 'type' in channel
        assert channel['type'] == 'webhook'
        assert 'settings' in channel
        assert isinstance(channel['settings'], dict)
    
    def test_pagerduty_notification_channel(self, notification_channels):
        """Test PagerDuty notification channel"""
        channel = notification_channels.get_pagerduty_channel()
        
        assert channel is not None
        assert 'name' in channel
        assert channel['name'] == 'PagerDuty Notifications'
        assert 'type' in channel
        assert channel['type'] == 'pagerduty'
        assert 'settings' in channel
        assert isinstance(channel['settings'], dict)
    
    def test_all_notification_channels(self, notification_channels):
        """Test all notification channels are available"""
        channels = notification_channels.get_all_channels()
        
        assert isinstance(channels, dict)
        assert 'email' in channels
        assert 'slack' in channels
        assert 'webhook' in channels
        assert 'pagerduty' in channels


class TestAlertManager:
    """Test alert manager"""
    
    @pytest.fixture
    def alert_manager(self):
        """Create alert manager instance"""
        return AlertManager(
            grafana_url="http://localhost:3000",
            api_key="test_api_key"
        )
    
    def test_alert_manager_initialization(self, alert_manager):
        """Test alert manager is properly initialized"""
        assert hasattr(alert_manager, 'grafana_url')
        assert hasattr(alert_manager, 'api_key')
        assert hasattr(alert_manager, 'headers')
        assert alert_manager.grafana_url == "http://localhost:3000"
        assert alert_manager.api_key == "test_api_key"
    
    def test_alert_manager_headers(self, alert_manager):
        """Test alert manager headers are properly set"""
        assert 'Authorization' in alert_manager.headers
        assert 'Content-Type' in alert_manager.headers
        assert alert_manager.headers['Content-Type'] == 'application/json'
    
    @patch('src.monitoring.alert_manager.requests.get')
    def test_get_alert_rules(self, mock_get, alert_manager):
        """Test getting alert rules from Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'name': 'High Error Rate'},
            {'id': 2, 'name': 'Performance Degradation'}
        ]
        mock_get.return_value = mock_response
        
        # Test getting alert rules
        rules = alert_manager.get_alert_rules()
        
        assert rules is not None
        assert len(rules) == 2
        assert rules[0]['name'] == 'High Error Rate'
        assert rules[1]['name'] == 'Performance Degradation'
    
    @patch('src.monitoring.alert_manager.requests.post')
    def test_create_alert_rule(self, mock_post, alert_manager):
        """Test creating an alert rule in Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 1, 'status': 'success'}
        mock_post.return_value = mock_response
        
        # Test alert rule config
        rule_config = {
            'name': 'Test Alert Rule',
            'condition': 'rate(api_errors_total[5m]) > 0.1',
            'duration': '5m'
        }
        
        # Test creating alert rule
        result = alert_manager.create_alert_rule(rule_config)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['id'] == 1
    
    @patch('src.monitoring.alert_manager.requests.put')
    def test_update_alert_rule(self, mock_put, alert_manager):
        """Test updating an alert rule in Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_put.return_value = mock_response
        
        # Test alert rule config
        rule_config = {
            'id': 1,
            'name': 'Updated Alert Rule',
            'condition': 'rate(api_errors_total[5m]) > 0.05',
            'duration': '5m'
        }
        
        # Test updating alert rule
        result = alert_manager.update_alert_rule(1, rule_config)
        
        assert result is not None
        assert result['status'] == 'success'
    
    @patch('src.monitoring.alert_manager.requests.delete')
    def test_delete_alert_rule(self, mock_delete, alert_manager):
        """Test deleting an alert rule from Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_delete.return_value = mock_response
        
        # Test deleting alert rule
        result = alert_manager.delete_alert_rule(1)
        
        assert result is not None
        assert result['status'] == 'success'
    
    def test_validate_alert_rule_config(self, alert_manager):
        """Test alert rule configuration validation"""
        # Valid config
        valid_config = {
            'name': 'Test Alert Rule',
            'condition': 'rate(api_errors_total[5m]) > 0.1',
            'duration': '5m'
        }
        
        assert alert_manager.validate_alert_rule_config(valid_config) is True
        
        # Invalid config (missing name)
        invalid_config = {
            'condition': 'rate(api_errors_total[5m]) > 0.1',
            'duration': '5m'
        }
        
        assert alert_manager.validate_alert_rule_config(invalid_config) is False
    
    def test_build_alert_rule_payload(self, alert_manager):
        """Test building alert rule payload for Grafana API"""
        rule_config = {
            'name': 'Test Alert Rule',
            'condition': 'rate(api_errors_total[5m]) > 0.1',
            'duration': '5m'
        }
        
        payload = alert_manager.build_alert_rule_payload(rule_config)
        
        assert payload is not None
        assert 'name' in payload
        assert 'condition' in payload
        assert 'duration' in payload
        assert payload['name'] == 'Test Alert Rule'
    
    @patch('src.monitoring.alert_manager.requests.get')
    def test_alert_rule_exists(self, mock_get, alert_manager):
        """Test checking if alert rule exists"""
        # Mock response for existing rule
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Test Alert Rule'},
            {'id': 2, 'name': 'Another Rule'}
        ]
        mock_get.return_value = mock_response
        
        assert alert_manager.alert_rule_exists('Test Alert Rule') is True
        
        # Mock response for non-existing rule (empty list)
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        assert alert_manager.alert_rule_exists('Non-existent Rule') is False
    
    def test_create_all_alert_rules(self, alert_manager):
        """Test creating all predefined alert rules"""
        with patch.object(alert_manager, 'create_alert_rule') as mock_create:
            mock_create.return_value = {'status': 'success', 'id': 1}
            
            result = alert_manager.create_all_alert_rules()
            
            assert result is not None
            assert isinstance(result, dict)
            assert 'created' in result
            assert 'failed' in result
            assert isinstance(result['created'], list)
            assert isinstance(result['failed'], list)
    
    @patch('src.monitoring.alert_manager.requests.get')
    def test_get_notification_channels(self, mock_get, alert_manager):
        """Test getting notification channels from Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Email Notifications'},
            {'id': 2, 'name': 'Slack Notifications'}
        ]
        mock_get.return_value = mock_response
        
        # Test getting notification channels
        channels = alert_manager.get_notification_channels()
        
        assert channels is not None
        assert len(channels) == 2
        assert channels[0]['name'] == 'Email Notifications'
        assert channels[1]['name'] == 'Slack Notifications'
    
    @patch('src.monitoring.alert_manager.requests.post')
    def test_create_notification_channel(self, mock_post, alert_manager):
        """Test creating a notification channel in Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 1, 'status': 'success'}
        mock_post.return_value = mock_response
        
        # Test notification channel config
        channel_config = {
            'name': 'Test Channel',
            'type': 'email',
            'settings': {
                'addresses': 'admin@example.com'
            }
        }
        
        # Test creating notification channel
        result = alert_manager.create_notification_channel(channel_config)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['id'] == 1
    
    def test_validate_notification_channel_config(self, alert_manager):
        """Test notification channel configuration validation"""
        # Valid config
        valid_config = {
            'name': 'Test Channel',
            'type': 'email',
            'settings': {
                'addresses': 'admin@example.com'
            }
        }
        
        assert alert_manager.validate_notification_channel_config(valid_config) is True
        
        # Invalid config (missing name)
        invalid_config = {
            'type': 'email',
            'settings': {
                'addresses': 'admin@example.com'
            }
        }
        
        assert alert_manager.validate_notification_channel_config(invalid_config) is False 
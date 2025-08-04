"""
Grafana Dashboard Configuration Tests

Tests for comprehensive Grafana dashboard configuration and management.
Following TDD methodology: Tests first, then implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from typing import Dict, List, Any

from src.monitoring.grafana_dashboard_manager import GrafanaDashboardManager
from src.monitoring.dashboard_configs import DashboardConfigs
from src.monitoring.panel_configs import PanelConfigs


class TestDashboardConfigs:
    """Test dashboard configuration definitions"""
    
    @pytest.fixture
    def dashboard_configs(self):
        """Create dashboard configs instance"""
        return DashboardConfigs()
    
    def test_system_overview_dashboard_config(self, dashboard_configs):
        """Test system overview dashboard configuration"""
        config = dashboard_configs.get_system_overview_config()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'System Overview'
        assert 'panels' in config
        assert isinstance(config['panels'], list)
        assert len(config['panels']) > 0
    
    def test_component_breakdown_dashboard_config(self, dashboard_configs):
        """Test component breakdown dashboard configuration"""
        config = dashboard_configs.get_component_breakdown_config()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Component Breakdown'
        assert 'panels' in config
        assert isinstance(config['panels'], list)
        assert len(config['panels']) > 0
    
    def test_business_metrics_dashboard_config(self, dashboard_configs):
        """Test business metrics dashboard configuration"""
        config = dashboard_configs.get_business_metrics_config()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Business Metrics'
        assert 'panels' in config
        assert isinstance(config['panels'], list)
        assert len(config['panels']) > 0
    
    def test_cost_analysis_dashboard_config(self, dashboard_configs):
        """Test cost analysis dashboard configuration"""
        config = dashboard_configs.get_cost_analysis_config()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Cost Analysis'
        assert 'panels' in config
        assert isinstance(config['panels'], list)
        assert len(config['panels']) > 0
    
    def test_performance_comparison_dashboard_config(self, dashboard_configs):
        """Test performance comparison dashboard configuration"""
        config = dashboard_configs.get_performance_comparison_config()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Performance Comparison'
        assert 'panels' in config
        assert isinstance(config['panels'], list)
        assert len(config['panels']) > 0
    
    def test_all_dashboard_configs(self, dashboard_configs):
        """Test all dashboard configurations are available"""
        configs = dashboard_configs.get_all_configs()
        
        assert isinstance(configs, dict)
        assert 'system_overview' in configs
        assert 'component_breakdown' in configs
        assert 'business_metrics' in configs
        assert 'cost_analysis' in configs
        assert 'performance_comparison' in configs


class TestPanelConfigs:
    """Test panel configuration definitions"""
    
    @pytest.fixture
    def panel_configs(self):
        """Create panel configs instance"""
        return PanelConfigs()
    
    def test_request_rate_panel_config(self, panel_configs):
        """Test request rate panel configuration"""
        config = panel_configs.get_request_rate_panel()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Request Rate'
        assert 'type' in config
        assert config['type'] == 'graph'
        assert 'targets' in config
        assert isinstance(config['targets'], list)
    
    def test_response_time_panel_config(self, panel_configs):
        """Test response time panel configuration"""
        config = panel_configs.get_response_time_panel()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Response Time'
        assert 'type' in config
        assert config['type'] == 'graph'
        assert 'targets' in config
        assert isinstance(config['targets'], list)
    
    def test_error_rate_panel_config(self, panel_configs):
        """Test error rate panel configuration"""
        config = panel_configs.get_error_rate_panel()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Error Rate'
        assert 'type' in config
        assert config['type'] == 'graph'
        assert 'targets' in config
        assert isinstance(config['targets'], list)
    
    def test_cpu_usage_panel_config(self, panel_configs):
        """Test CPU usage panel configuration"""
        config = panel_configs.get_cpu_usage_panel()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'CPU Usage'
        assert 'type' in config
        assert config['type'] == 'stat'
        assert 'targets' in config
        assert isinstance(config['targets'], list)
    
    def test_memory_usage_panel_config(self, panel_configs):
        """Test memory usage panel configuration"""
        config = panel_configs.get_memory_usage_panel()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Memory Usage'
        assert 'type' in config
        assert config['type'] == 'stat'
        assert 'targets' in config
        assert isinstance(config['targets'], list)
    
    def test_llm_metrics_panel_config(self, panel_configs):
        """Test LLM metrics panel configuration"""
        config = panel_configs.get_llm_metrics_panel()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'LLM Metrics'
        assert 'type' in config
        assert config['type'] == 'graph'
        assert 'targets' in config
        assert isinstance(config['targets'], list)
    
    def test_vector_store_metrics_panel_config(self, panel_configs):
        """Test vector store metrics panel configuration"""
        config = panel_configs.get_vector_store_metrics_panel()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Vector Store Metrics'
        assert 'type' in config
        assert config['type'] == 'graph'
        assert 'targets' in config
        assert isinstance(config['targets'], list)
    
    def test_memory_metrics_panel_config(self, panel_configs):
        """Test memory metrics panel configuration"""
        config = panel_configs.get_memory_metrics_panel()
        
        assert config is not None
        assert 'title' in config
        assert config['title'] == 'Memory Metrics'
        assert 'type' in config
        assert config['type'] == 'graph'
        assert 'targets' in config
        assert isinstance(config['targets'], list)


class TestGrafanaDashboardManager:
    """Test Grafana dashboard manager"""
    
    @pytest.fixture
    def dashboard_manager(self):
        """Create dashboard manager instance"""
        return GrafanaDashboardManager(
            grafana_url="http://localhost:3000",
            api_key="test_api_key"
        )
    
    def test_dashboard_manager_initialization(self, dashboard_manager):
        """Test dashboard manager is properly initialized"""
        assert hasattr(dashboard_manager, 'grafana_url')
        assert hasattr(dashboard_manager, 'api_key')
        assert hasattr(dashboard_manager, 'headers')
        assert dashboard_manager.grafana_url == "http://localhost:3000"
        assert dashboard_manager.api_key == "test_api_key"
    
    def test_dashboard_manager_headers(self, dashboard_manager):
        """Test dashboard manager headers are properly set"""
        assert 'Authorization' in dashboard_manager.headers
        assert 'Content-Type' in dashboard_manager.headers
        assert dashboard_manager.headers['Content-Type'] == 'application/json'
    
    @patch('src.monitoring.grafana_dashboard_manager.requests.get')
    def test_get_dashboards(self, mock_get, dashboard_manager):
        """Test getting dashboards from Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'title': 'System Overview'},
            {'id': 2, 'title': 'Component Breakdown'}
        ]
        mock_get.return_value = mock_response
        
        # Test getting dashboards
        dashboards = dashboard_manager.get_dashboards()
        
        assert dashboards is not None
        assert len(dashboards) == 2
        assert dashboards[0]['title'] == 'System Overview'
        assert dashboards[1]['title'] == 'Component Breakdown'
    
    @patch('src.monitoring.grafana_dashboard_manager.requests.post')
    def test_create_dashboard(self, mock_post, dashboard_manager):
        """Test creating a dashboard in Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 1, 'status': 'success'}
        mock_post.return_value = mock_response
        
        # Test dashboard config
        dashboard_config = {
            'title': 'Test Dashboard',
            'panels': []
        }
        
        # Test creating dashboard
        result = dashboard_manager.create_dashboard(dashboard_config)
        
        assert result is not None
        assert result['status'] == 'success'
        assert result['id'] == 1
    
    @patch('src.monitoring.grafana_dashboard_manager.requests.get')
    @patch('src.monitoring.grafana_dashboard_manager.requests.post')
    def test_update_dashboard(self, mock_post, mock_get, dashboard_manager):
        """Test updating a dashboard in Grafana"""
        # Mock get response for existing dashboard
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'dashboard': {
                'id': 1,
                'version': 1,
                'title': 'Test Dashboard',
                'panels': []
            }
        }
        mock_get.return_value = mock_get_response
        
        # Mock post response (Grafana uses POST for dashboard updates)
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {'status': 'success'}
        mock_post.return_value = mock_post_response
        
        # Test dashboard config
        dashboard_config = {
            'id': 1,
            'title': 'Updated Dashboard',
            'panels': []
        }
        
        # Test updating dashboard
        result = dashboard_manager.update_dashboard(1, dashboard_config)
        
        assert result is not None
        assert result['status'] == 'success'
    
    @patch('src.monitoring.grafana_dashboard_manager.requests.delete')
    def test_delete_dashboard(self, mock_delete, dashboard_manager):
        """Test deleting a dashboard from Grafana"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_delete.return_value = mock_response
        
        # Test deleting dashboard
        result = dashboard_manager.delete_dashboard(1)
        
        assert result is not None
        assert result['status'] == 'success'
    
    def test_validate_dashboard_config(self, dashboard_manager):
        """Test dashboard configuration validation"""
        # Valid config
        valid_config = {
            'title': 'Test Dashboard',
            'panels': [
                {
                    'title': 'Test Panel',
                    'type': 'graph',
                    'targets': []
                }
            ]
        }
        
        assert dashboard_manager.validate_dashboard_config(valid_config) is True
        
        # Invalid config (missing title)
        invalid_config = {
            'panels': []
        }
        
        assert dashboard_manager.validate_dashboard_config(invalid_config) is False
    
    def test_build_dashboard_payload(self, dashboard_manager):
        """Test building dashboard payload for Grafana API"""
        dashboard_config = {
            'title': 'Test Dashboard',
            'panels': [
                {
                    'title': 'Test Panel',
                    'type': 'graph',
                    'targets': []
                }
            ]
        }
        
        payload = dashboard_manager.build_dashboard_payload(dashboard_config)
        
        assert payload is not None
        assert 'dashboard' in payload
        assert 'overwrite' in payload
        assert payload['dashboard']['title'] == 'Test Dashboard'
        assert payload['overwrite'] is True
    
    @patch('src.monitoring.grafana_dashboard_manager.requests.get')
    def test_dashboard_exists(self, mock_get, dashboard_manager):
        """Test checking if dashboard exists"""
        # Mock response for existing dashboard
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'title': 'Test Dashboard'},
            {'id': 2, 'title': 'Another Dashboard'}
        ]
        mock_get.return_value = mock_response
        
        assert dashboard_manager.dashboard_exists('Test Dashboard') is True
        
        # Mock response for non-existing dashboard (empty list)
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        assert dashboard_manager.dashboard_exists('Non-existent Dashboard') is False
    
    def test_create_all_dashboards(self, dashboard_manager):
        """Test creating all predefined dashboards"""
        with patch.object(dashboard_manager, 'create_dashboard') as mock_create:
            mock_create.return_value = {'status': 'success', 'id': 1}
            
            result = dashboard_manager.create_all_dashboards()
            
            assert result is not None
            assert isinstance(result, dict)
            assert 'created' in result
            assert 'failed' in result
            assert isinstance(result['created'], list)
            assert isinstance(result['failed'], list) 
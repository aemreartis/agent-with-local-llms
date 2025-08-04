"""
Dashboard Configuration Definitions

Defines various Grafana dashboard configurations for different monitoring views.
"""

from typing import Dict, List, Any
from .panel_configs import PanelConfigs


class DashboardConfigs:
    """Dashboard configuration definitions for Grafana"""
    
    def __init__(self):
        """Initialize dashboard configs with panel configs"""
        self.panel_configs = PanelConfigs()
    
    def get_system_overview_config(self) -> Dict[str, Any]:
        """Get system overview dashboard configuration"""
        return {
            'title': 'System Overview',
            'panels': [
                {
                    **self.panel_configs.get_request_rate_panel(),
                    'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 0}
                },
                {
                    **self.panel_configs.get_response_time_panel(),
                    'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 0}
                },
                {
                    **self.panel_configs.get_error_rate_panel(),
                    'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 8}
                },
                {
                    **self.panel_configs.get_cpu_usage_panel(),
                    'gridPos': {'h': 8, 'w': 6, 'x': 12, 'y': 8}
                },
                {
                    **self.panel_configs.get_memory_usage_panel(),
                    'gridPos': {'h': 8, 'w': 6, 'x': 18, 'y': 8}
                },
                {
                    **self.panel_configs.get_network_io_panel(),
                    'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 16}
                },
                {
                    **self.panel_configs.get_process_count_panel(),
                    'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 16}
                }
            ],
            'time': {
                'from': 'now-1h',
                'to': 'now'
            },
            'refresh': '30s'
        }
    
    def get_component_breakdown_config(self) -> Dict[str, Any]:
        """Get component breakdown dashboard configuration"""
        return {
            'title': 'Component Breakdown',
            'panels': [
                {
                    **self.panel_configs.get_llm_metrics_panel(),
                    'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 0}
                },
                {
                    **self.panel_configs.get_vector_store_metrics_panel(),
                    'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 0}
                },
                {
                    **self.panel_configs.get_memory_metrics_panel(),
                    'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 8}
                },
                {
                    'title': 'API Active Connections',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'api_active_connections',
                            'legendFormat': 'Active Connections'
                        }
                    ],
                    'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 8}
                }
            ],
            'time': {
                'from': 'now-1h',
                'to': 'now'
            },
            'refresh': '30s'
        }
    
    def get_business_metrics_config(self) -> Dict[str, Any]:
        """Get business metrics dashboard configuration"""
        return {
            'title': 'Business Metrics',
            'panels': [
                {
                    'title': 'User Satisfaction Score',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'user_satisfaction_score',
                            'legendFormat': 'Satisfaction Score'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 'percent',
                            'color': {
                                'mode': 'thresholds'
                            },
                            'thresholds': {
                                'steps': [
                                    {'color': 'red', 'value': 0},
                                    {'color': 'yellow', 'value': 70},
                                    {'color': 'green', 'value': 90}
                                ]
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 6, 'x': 0, 'y': 0}
                },
                {
                    'title': 'Response Quality Score',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'response_quality_score',
                            'legendFormat': 'Quality Score'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 'percent',
                            'color': {
                                'mode': 'thresholds'
                            },
                            'thresholds': {
                                'steps': [
                                    {'color': 'red', 'value': 0},
                                    {'color': 'yellow', 'value': 70},
                                    {'color': 'green', 'value': 90}
                                ]
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 6, 'x': 6, 'y': 0}
                },
                {
                    'title': 'Hallucination Rate',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'rate(hallucination_events_total[5m])',
                            'legendFormat': 'Hallucination Rate'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 'reqps',
                            'color': {
                                'mode': 'thresholds'
                            },
                            'thresholds': {
                                'steps': [
                                    {'color': 'green', 'value': 0},
                                    {'color': 'yellow', 'value': 0.01},
                                    {'color': 'red', 'value': 0.05}
                                ]
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 6, 'x': 12, 'y': 0}
                },
                {
                    'title': 'Task Success Rate',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'task_success_rate',
                            'legendFormat': 'Success Rate'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 'percent',
                            'color': {
                                'mode': 'thresholds'
                            },
                            'thresholds': {
                                'steps': [
                                    {'color': 'red', 'value': 0},
                                    {'color': 'yellow', 'value': 80},
                                    {'color': 'green', 'value': 95}
                                ]
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 6, 'x': 18, 'y': 0}
                }
            ],
            'time': {
                'from': 'now-24h',
                'to': 'now'
            },
            'refresh': '1m'
        }
    
    def get_cost_analysis_config(self) -> Dict[str, Any]:
        """Get cost analysis dashboard configuration"""
        return {
            'title': 'Cost Analysis',
            'panels': [
                {
                    'title': 'Cost per Query',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'cost_per_query_dollars',
                            'legendFormat': 'Cost per Query'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 'currencyUSD',
                            'color': {
                                'mode': 'thresholds'
                            },
                            'thresholds': {
                                'steps': [
                                    {'color': 'green', 'value': 0},
                                    {'color': 'yellow', 'value': 0.01},
                                    {'color': 'red', 'value': 0.05}
                                ]
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 6, 'x': 0, 'y': 0}
                },
                {
                    'title': 'Total Cost (24h)',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'increase(total_cost_dollars[24h])',
                            'legendFormat': 'Total Cost'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 'currencyUSD',
                            'color': {
                                'mode': 'thresholds'
                            },
                            'thresholds': {
                                'steps': [
                                    {'color': 'green', 'value': 0},
                                    {'color': 'yellow', 'value': 10},
                                    {'color': 'red', 'value': 50}
                                ]
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 6, 'x': 6, 'y': 0}
                },
                {
                    'title': 'Resource Utilization Cost',
                    'type': 'graph',
                    'targets': [
                        {
                            'expr': 'rate(cpu_cost_dollars[5m])',
                            'legendFormat': 'CPU Cost'
                        },
                        {
                            'expr': 'rate(memory_cost_dollars[5m])',
                            'legendFormat': 'Memory Cost'
                        },
                        {
                            'expr': 'rate(storage_cost_dollars[5m])',
                            'legendFormat': 'Storage Cost'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 'currencyUSD',
                            'color': {
                                'mode': 'palette-classic'
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 0}
                }
            ],
            'time': {
                'from': 'now-24h',
                'to': 'now'
            },
            'refresh': '5m'
        }
    
    def get_performance_comparison_config(self) -> Dict[str, Any]:
        """Get performance comparison dashboard configuration"""
        return {
            'title': 'Performance Comparison',
            'panels': [
                {
                    'title': 'LLM Provider Performance',
                    'type': 'graph',
                    'targets': [
                        {
                            'expr': 'rate(llm_request_duration_seconds_sum[5m]) / rate(llm_request_duration_seconds_count[5m])',
                            'legendFormat': 'Avg Response Time - {{provider}}'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 's',
                            'color': {
                                'mode': 'palette-classic'
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 0}
                },
                {
                    'title': 'Vector Store Performance',
                    'type': 'graph',
                    'targets': [
                        {
                            'expr': 'rate(vector_search_duration_seconds_sum[5m]) / rate(vector_search_duration_seconds_count[5m])',
                            'legendFormat': 'Avg Search Time - {{provider}}'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 's',
                            'color': {
                                'mode': 'palette-classic'
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 0}
                },
                {
                    'title': 'Memory Provider Performance',
                    'type': 'graph',
                    'targets': [
                        {
                            'expr': 'memory_cache_hit_rate',
                            'legendFormat': 'Cache Hit Rate - {{provider}}'
                        }
                    ],
                    'fieldConfig': {
                        'defaults': {
                            'unit': 'percent',
                            'color': {
                                'mode': 'palette-classic'
                            }
                        }
                    },
                    'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 8}
                }
            ],
            'time': {
                'from': 'now-1h',
                'to': 'now'
            },
            'refresh': '30s'
        }
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all dashboard configurations"""
        return {
            'system_overview': self.get_system_overview_config(),
            'component_breakdown': self.get_component_breakdown_config(),
            'business_metrics': self.get_business_metrics_config(),
            'cost_analysis': self.get_cost_analysis_config(),
            'performance_comparison': self.get_performance_comparison_config()
        } 
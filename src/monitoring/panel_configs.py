"""
Panel Configuration Definitions

Defines various Grafana panel configurations for different metrics visualization.
"""

from typing import Dict, List, Any


class PanelConfigs:
    """Panel configuration definitions for Grafana dashboards"""
    
    def get_request_rate_panel(self) -> Dict[str, Any]:
        """Get request rate panel configuration"""
        return {
            'title': 'Request Rate',
            'type': 'graph',
            'targets': [
                {
                    'expr': 'rate(api_requests_total[5m])',
                    'legendFormat': '{{endpoint}} - {{method}}'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'unit': 'reqps',
                    'color': {
                        'mode': 'palette-classic'
                    }
                }
            }
        }
    
    def get_response_time_panel(self) -> Dict[str, Any]:
        """Get response time panel configuration"""
        return {
            'title': 'Response Time',
            'type': 'graph',
            'targets': [
                {
                    'expr': 'histogram_quantile(0.95, rate(api_response_time_seconds_bucket[5m]))',
                    'legendFormat': '95th percentile - {{endpoint}}'
                },
                {
                    'expr': 'histogram_quantile(0.50, rate(api_response_time_seconds_bucket[5m]))',
                    'legendFormat': '50th percentile - {{endpoint}}'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'unit': 's',
                    'color': {
                        'mode': 'palette-classic'
                    }
                }
            }
        }
    
    def get_error_rate_panel(self) -> Dict[str, Any]:
        """Get error rate panel configuration"""
        return {
            'title': 'Error Rate',
            'type': 'graph',
            'targets': [
                {
                    'expr': 'rate(api_errors_total[5m])',
                    'legendFormat': '{{endpoint}} - {{error_type}}'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'unit': 'reqps',
                    'color': {
                        'mode': 'palette-classic'
                    }
                }
            }
        }
    
    def get_cpu_usage_panel(self) -> Dict[str, Any]:
        """Get CPU usage panel configuration"""
        return {
            'title': 'CPU Usage',
            'type': 'stat',
            'targets': [
                {
                    'expr': 'system_cpu_usage_percent',
                    'legendFormat': 'CPU Usage'
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
                            {'color': 'green', 'value': 0},
                            {'color': 'yellow', 'value': 70},
                            {'color': 'red', 'value': 90}
                        ]
                    }
                }
            }
        }
    
    def get_memory_usage_panel(self) -> Dict[str, Any]:
        """Get memory usage panel configuration"""
        return {
            'title': 'Memory Usage',
            'type': 'stat',
            'targets': [
                {
                    'expr': 'system_memory_usage_bytes',
                    'legendFormat': 'Memory Usage'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'unit': 'bytes',
                    'color': {
                        'mode': 'thresholds'
                    },
                    'thresholds': {
                        'steps': [
                            {'color': 'green', 'value': 0},
                            {'color': 'yellow', 'value': 8589934592},  # 8GB
                            {'color': 'red', 'value': 12884901888}     # 12GB
                        ]
                    }
                }
            }
        }
    
    def get_llm_metrics_panel(self) -> Dict[str, Any]:
        """Get LLM metrics panel configuration"""
        return {
            'title': 'LLM Metrics',
            'type': 'graph',
            'targets': [
                {
                    'expr': 'rate(llm_requests_total[5m])',
                    'legendFormat': 'Requests - {{provider}}'
                },
                {
                    'expr': 'rate(llm_tokens_generated_total[5m])',
                    'legendFormat': 'Tokens - {{provider}}'
                },
                {
                    'expr': 'rate(llm_errors_total[5m])',
                    'legendFormat': 'Errors - {{provider}}'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'color': {
                        'mode': 'palette-classic'
                    }
                }
            }
        }
    
    def get_vector_store_metrics_panel(self) -> Dict[str, Any]:
        """Get vector store metrics panel configuration"""
        return {
            'title': 'Vector Store Metrics',
            'type': 'graph',
            'targets': [
                {
                    'expr': 'rate(vector_search_queries_total[5m])',
                    'legendFormat': 'Search Queries - {{provider}}'
                },
                {
                    'expr': 'rate(vector_operations_total[5m])',
                    'legendFormat': 'Operations - {{provider}}'
                },
                {
                    'expr': 'vector_index_size_bytes',
                    'legendFormat': 'Index Size - {{provider}}'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'color': {
                        'mode': 'palette-classic'
                    }
                }
            }
        }
    
    def get_memory_metrics_panel(self) -> Dict[str, Any]:
        """Get memory metrics panel configuration"""
        return {
            'title': 'Memory Metrics',
            'type': 'graph',
            'targets': [
                {
                    'expr': 'rate(memory_operations_total[5m])',
                    'legendFormat': 'Operations - {{provider}}'
                },
                {
                    'expr': 'memory_cache_hit_rate',
                    'legendFormat': 'Cache Hit Rate - {{provider}}'
                },
                {
                    'expr': 'memory_storage_usage_bytes',
                    'legendFormat': 'Storage Usage - {{provider}}'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'color': {
                        'mode': 'palette-classic'
                    }
                }
            }
        }
    
    def get_network_io_panel(self) -> Dict[str, Any]:
        """Get network I/O panel configuration"""
        return {
            'title': 'Network I/O',
            'type': 'graph',
            'targets': [
                {
                    'expr': 'rate(system_network_io_bytes_total{direction="in"}[5m])',
                    'legendFormat': 'Network In'
                },
                {
                    'expr': 'rate(system_network_io_bytes_total{direction="out"}[5m])',
                    'legendFormat': 'Network Out'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'unit': 'Bps',
                    'color': {
                        'mode': 'palette-classic'
                    }
                }
            }
        }
    
    def get_process_count_panel(self) -> Dict[str, Any]:
        """Get process count panel configuration"""
        return {
            'title': 'Process Count',
            'type': 'stat',
            'targets': [
                {
                    'expr': 'system_process_count',
                    'legendFormat': 'Active Processes'
                }
            ],
            'fieldConfig': {
                'defaults': {
                    'unit': 'short',
                    'color': {
                        'mode': 'thresholds'
                    },
                    'thresholds': {
                        'steps': [
                            {'color': 'green', 'value': 0},
                            {'color': 'yellow', 'value': 100},
                            {'color': 'red', 'value': 200}
                        ]
                    }
                }
            }
        } 
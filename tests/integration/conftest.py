"""
Integration test configuration and fixtures for Stage 8.
Provides base classes and fixtures for comprehensive integration testing.
"""

import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any, AsyncGenerator
from unittest.mock import AsyncMock, patch

from src.registry.provider_registry import ProviderRegistry
from src.config.config_loader import ConfigLoader
from src.services.application_assembler import ApplicationAssembler
from src.services.service_manager import ServiceManager


class IntegrationTestBase:
    """Base class for all integration tests with common setup and teardown."""
    
    def __init__(self):
        self.provider_registry = None
        self.config_loader = None
        self.application_assembler = None
        self.service_manager = None
        self.test_data = {}
        self.temp_files = []
    
    async def setup_integration_environment(self, config: Dict[str, Any] = None):
        """Set up the integration test environment."""
        # Initialize core components
        self.config_loader = ConfigLoader()
        self.provider_registry = ProviderRegistry()
        self.application_assembler = ApplicationAssembler(self.provider_registry)
        self.service_manager = ServiceManager()
        
        # Load test configuration
        if config:
            await self.config_loader.load_config_from_dict(config)
        else:
            await self.config_loader.load_config("configs/providers.yaml")
        
        # Initialize providers
        await self.provider_registry.initialize_providers(self.config_loader.config)
        
        # Assemble application
        await self.application_assembler.assemble_application(self.config_loader.config)
        
        # Start services
        await self.service_manager.start_all_services(self.config_loader.config)
    
    async def teardown_integration_environment(self):
        """Clean up the integration test environment."""
        if self.service_manager:
            await self.service_manager.stop_all_services()
        
        if self.provider_registry:
            await self.provider_registry.shutdown()
        
        # Clean up temp files
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def create_temp_file(self, content: str, extension: str = ".txt") -> str:
        """Create a temporary file for testing."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=extension, 
            delete=False
        )
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name


@pytest.fixture
async def integration_base() -> AsyncGenerator[IntegrationTestBase, None]:
    """Fixture providing base integration test setup."""
    base = IntegrationTestBase()
    yield base
    await base.teardown_integration_environment()


@pytest.fixture
async def provider_registry() -> AsyncGenerator[ProviderRegistry, None]:
    """Fixture providing initialized provider registry."""
    registry = ProviderRegistry()
    config_loader = ConfigLoader()
    await config_loader.load_config("configs/providers.yaml")
    await registry.initialize_providers(config_loader.config)
    yield registry
    await registry.shutdown()


@pytest.fixture
async def application_assembler() -> AsyncGenerator[ApplicationAssembler, None]:
    """Fixture providing assembled application."""
    registry = ProviderRegistry()
    assembler = ApplicationAssembler(registry)
    config_loader = ConfigLoader()
    await config_loader.load_config("configs/providers.yaml")
    await assembler.assemble_application(config_loader.config)
    yield assembler
    await registry.shutdown()


@pytest.fixture
def sample_documents() -> Dict[str, str]:
    """Fixture providing sample documents for testing."""
    return {
        "sample.txt": "This is a sample text document for testing integration scenarios. It contains information about various topics including technology, science, and business.",
        "sample.md": "# Sample Markdown Document\n\nThis is a sample markdown document with **bold text** and *italic text*.\n\n## Section 1\n\nContent for section 1.\n\n## Section 2\n\nContent for section 2.",
        "sample.html": "<html><body><h1>Sample HTML Document</h1><p>This is a sample HTML document with <strong>bold</strong> and <em>italic</em> text.</p><ul><li>Item 1</li><li>Item 2</li></ul></body></html>"
    }


@pytest.fixture
def test_configurations() -> Dict[str, Dict[str, Any]]:
    """Fixture providing test configurations for different provider combinations."""
    return {
        "vllm_qdrant_bge_redis": {
            "llm": {
                "default": "vllm",
                "providers": {
                    "vllm": {
                        "class": "src.providers.llm.vllm_provider.VLLMProvider",
                        "config": {
                            "base_url": "http://localhost:8001",
                            "model": "llama-2-7b"
                        }
                    }
                }
            },
            "vector_store": {
                "default": "qdrant",
                "providers": {
                    "qdrant": {
                        "class": "src.providers.vector_stores.qdrant_provider.QdrantProvider",
                        "config": {
                            "url": "http://localhost:6333",
                            "collection_name": "test_collection"
                        }
                    }
                }
            },
            "reranker": {
                "default": "bge",
                "providers": {
                    "bge": {
                        "class": "src.providers.rerankers.bge_provider.BGEProvider",
                        "config": {
                            "model": "BAAI/bge-reranker-base"
                        }
                    }
                }
            },
            "memory": {
                "default": "redis",
                "providers": {
                    "redis": {
                        "class": "src.providers.memory.redis_provider.RedisMemoryProvider",
                        "config": {
                            "host": "localhost",
                            "port": 6379,
                            "db": 1
                        }
                    }
                }
            }
        },
        "vllm_qdrant_bge_postgresql": {
            "llm": {
                "default": "vllm",
                "providers": {
                    "vllm": {
                        "class": "src.providers.llm.vllm_provider.VLLMProvider",
                        "config": {
                            "base_url": "http://localhost:8001",
                            "model": "llama-2-7b"
                        }
                    }
                }
            },
            "vector_store": {
                "default": "qdrant",
                "providers": {
                    "qdrant": {
                        "class": "src.providers.vector_stores.qdrant_provider.QdrantProvider",
                        "config": {
                            "url": "http://localhost:6333",
                            "collection_name": "test_collection"
                        }
                    }
                }
            },
            "reranker": {
                "default": "bge",
                "providers": {
                    "bge": {
                        "class": "src.providers.rerankers.bge_provider.BGEProvider",
                        "config": {
                            "model": "BAAI/bge-reranker-base"
                        }
                    }
                }
            },
            "memory": {
                "default": "postgresql",
                "providers": {
                    "postgresql": {
                        "class": "src.providers.memory.postgresql_provider.PostgreSQLMemoryProvider",
                        "config": {
                            "host": "localhost",
                            "port": 5432,
                            "database": "test_db",
                            "username": "test_user",
                            "password": "test_password"
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_external_services():
    """Fixture providing mocked external services for testing."""
    with patch('src.providers.llm.vllm_provider.httpx.AsyncClient') as mock_vllm, \
         patch('src.providers.vector_stores.qdrant_provider.AsyncQdrantClient') as mock_qdrant:
        
        # Mock vLLM responses
        mock_vllm.return_value.post.return_value.json.return_value = {
            "text": "Mocked LLM response",
            "usage": {"total_tokens": 100}
        }
        
        # Mock Qdrant responses
        mock_qdrant.return_value.collection_exists.return_value = True
        mock_qdrant.return_value.upsert.return_value = {"status": "ok"}
        mock_qdrant.return_value.search.return_value = [
            {"id": "1", "score": 0.9, "payload": {"text": "Mocked search result"}}
        ]
        
        yield {
            "vllm": mock_vllm,
            "qdrant": mock_qdrant
        }


@pytest.fixture
def performance_metrics():
    """Fixture providing performance monitoring utilities."""
    class PerformanceMetrics:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.metrics = {}
        
        def start_timer(self):
            """Start performance timer."""
            self.start_time = asyncio.get_event_loop().time()
        
        def end_timer(self):
            """End performance timer and calculate duration."""
            self.end_time = asyncio.get_event_loop().time()
            return self.end_time - self.start_time
        
        def record_metric(self, name: str, value: float):
            """Record a performance metric."""
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(value)
        
        def get_average(self, name: str) -> float:
            """Get average value for a metric."""
            if name in self.metrics and self.metrics[name]:
                return sum(self.metrics[name]) / len(self.metrics[name])
            return 0.0
        
        def get_percentile(self, name: str, percentile: float) -> float:
            """Get percentile value for a metric."""
            if name in self.metrics and self.metrics[name]:
                sorted_values = sorted(self.metrics[name])
                index = int(len(sorted_values) * percentile / 100)
                return sorted_values[index]
            return 0.0
    
    return PerformanceMetrics() 
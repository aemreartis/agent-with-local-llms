import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
from src.providers.llm.vllm_provider import VLLMProvider
from src.interfaces.llm_interface import LLMInterface


class TestVLLMProvider:
    """Test suite for vLLM Provider implementation."""
    
    @pytest.fixture
    def vllm_config(self):
        """Configuration for vLLM provider."""
        return {
            "base_url": "http://localhost:8000",
            "model": "llama-2-7b-chat",
            "temperature": 0.7,
            "max_tokens": 1024,
            "timeout": 30.0
        }
    
    @pytest.fixture
    def mock_response_generate(self):
        """Mock response for generation endpoint."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from vLLM"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18
            }
        }
    
    @pytest.fixture
    def mock_response_embed(self):
        """Mock response for embedding endpoint."""
        return {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 153,  # 765 dimensions
                    "index": 0
                }
            ],
            "model": "bge-large-en-v1.5",
            "usage": {"total_tokens": 5}
        }
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_vllm_provider_implements_interface(self):
        """Test that VLLMProvider implements LLMInterface correctly."""
        provider = VLLMProvider()
        assert isinstance(provider, LLMInterface)
        
        # Check all required methods exist
        assert hasattr(provider, 'initialize')
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'embed')
        assert hasattr(provider, 'health_check')
        assert hasattr(provider, 'get_provider_info')
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_initialize_success(self, vllm_config):
        """Test successful initialization."""
        provider = VLLMProvider()
        
        with patch('httpx.AsyncClient') as mock_client:
            await provider.initialize(vllm_config)
            
            assert provider.base_url == "http://localhost:8000"
            assert provider.model == "llama-2-7b-chat"
            assert provider.temperature == 0.7
            assert provider.max_tokens == 1024
            assert provider.client is not None
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_initialize_missing_base_url(self):
        """Test initialization fails with missing base_url."""
        provider = VLLMProvider()
        config = {"model": "llama-2-7b"}
        
        with pytest.raises(ValueError, match="base_url is required"):
            await provider.initialize(config)
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_generate_success(self, vllm_config, mock_response_generate):
        """Test successful text generation."""
        provider = VLLMProvider()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_generate
            mock_client.post.return_value = mock_response
            
            await provider.initialize(vllm_config)
            
            result = await provider.generate("Hello, how are you?")
            
            assert result == "This is a test response from vLLM"
            mock_client.post.assert_called_once()
            
            # Check request parameters
            call_args = mock_client.post.call_args
            assert "/v1/chat/completions" in call_args[0][0]
            request_data = call_args[1]["json"]
            assert request_data["model"] == "llama-2-7b-chat"
            assert request_data["temperature"] == 0.7
            assert request_data["max_tokens"] == 1024
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_generate_with_context(self, vllm_config, mock_response_generate):
        """Test text generation with context."""
        provider = VLLMProvider()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_generate
            mock_client.post.return_value = mock_response
            
            await provider.initialize(vllm_config)
            
            context = ["Context 1", "Context 2"]
            result = await provider.generate("Question?", context=context)
            
            assert result == "This is a test response from vLLM"
            
            # Check that context was included in messages
            call_args = mock_client.post.call_args
            request_data = call_args[1]["json"]
            messages = request_data["messages"]
            
            # Should have system message with context + user message
            assert len(messages) >= 2
            assert any("Context 1" in str(msg) and "Context 2" in str(msg) for msg in messages)
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_generate_http_error(self, vllm_config):
        """Test generation handles HTTP errors gracefully."""
        provider = VLLMProvider()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock HTTP error
            mock_client.post.side_effect = httpx.HTTPError("Connection failed")
            
            await provider.initialize(vllm_config)
            
            with pytest.raises(Exception, match="vLLM generation failed"):
                await provider.generate("Hello")
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_embed_success(self, vllm_config, mock_response_embed):
        """Test successful text embedding."""
        provider = VLLMProvider()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_embed
            mock_client.post.return_value = mock_response
            
            await provider.initialize(vllm_config)
            
            result = await provider.embed("Text to embed")
            
            expected_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 153
            assert result == expected_embedding
            assert len(result) == 765
            
            # Check request was made to embeddings endpoint
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/v1/embeddings" in call_args[0][0]
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_health_check_success(self, vllm_config):
        """Test successful health check."""
        provider = VLLMProvider()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock successful health response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_client.get.return_value = mock_response
            
            await provider.initialize(vllm_config)
            
            result = await provider.health_check()
            
            assert result is True
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "/health" in call_args[0][0]
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_health_check_failure(self, vllm_config):
        """Test health check failure."""
        provider = VLLMProvider()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock health check failure
            mock_client.get.side_effect = httpx.HTTPError("Service unavailable")
            
            await provider.initialize(vllm_config)
            
            result = await provider.health_check()
            
            assert result is False
    
    @pytest.mark.provider
    def test_get_provider_info(self):
        """Test provider info retrieval."""
        provider = VLLMProvider()
        
        info = provider.get_provider_info()
        
        assert info["name"] == "VLLMProvider"
        assert info["type"] == "llm"
        assert "generation" in info["capabilities"]
        assert "embedding" in info["capabilities"]
        assert "version" in info
    
    @pytest.mark.provider
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, vllm_config):
        """Test graceful shutdown of provider."""
        provider = VLLMProvider()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            await provider.initialize(vllm_config)
            await provider.graceful_shutdown()
            
            # Should close the HTTP client
            mock_client.aclose.assert_called_once() 
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.interfaces.llm_interface import LLMInterface


class VLLMProvider(LLMInterface):
    """vLLM Provider for local LLM inference.
    
    Connects to a vLLM server instance for text generation and embedding.
    Supports OpenAI-compatible API endpoints.
    """
    
    def __init__(self):
        """Initialize the vLLM provider."""
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url: Optional[str] = None
        self.model: Optional[str] = None
        self.temperature: float = 0.7
        self.max_tokens: int = 1024
        self.timeout: float = 30.0
        self._initialized: bool = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the vLLM provider with configuration.
        
        Args:
            config: Configuration dictionary containing:
                - base_url: vLLM server URL (required)
                - model: Model name (optional, defaults to server default)
                - temperature: Sampling temperature (optional, default 0.7)
                - max_tokens: Maximum tokens to generate (optional, default 1024)
                - timeout: HTTP timeout in seconds (optional, default 30.0)
                
        Raises:
            ValueError: If required configuration is missing
        """
        if "base_url" not in config:
            raise ValueError("base_url is required for vLLM provider")
        
        self.base_url = config["base_url"].rstrip("/")
        self.model = config.get("model", "default")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1024)
        self.timeout = config.get("timeout", 30.0)
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={"Content-Type": "application/json"}
        )
        
        self._initialized = True
    
    async def generate(self, prompt: str, context: Optional[List[str]] = None, **kwargs) -> str:
        """Generate text response from prompt.
        
        Args:
            prompt: Input prompt for generation
            context: Optional context documents to include
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If generation fails or provider not initialized
        """
        if not self._initialized or self.client is None:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        try:
            # Build messages for chat completion
            messages = []
            
            # Add context as system message if provided
            if context:
                context_text = "\n".join(context)
                messages.append({
                    "role": "system",
                    "content": f"Use the following context to answer the user's question:\n\n{context_text}"
                })
            
            # Add user prompt
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": False
            }
            
            # Make request to vLLM chat completions endpoint
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"vLLM generation failed with status {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Extract generated text from response
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception("No choices returned in vLLM response")
                
        except httpx.HTTPError as e:
            raise Exception(f"vLLM generation failed: HTTP error - {str(e)}")
        except Exception as e:
            if "vLLM generation failed" in str(e):
                raise
            raise Exception(f"vLLM generation failed: {str(e)}")
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
            
        Raises:
            Exception: If embedding fails or provider not initialized
        """
        if not self._initialized or self.client is None:
            raise Exception("Provider not initialized. Call initialize() first.")
        
        try:
            payload = {
                "input": text,
                "model": "bge-large-en-v1.5"  # Default embedding model
            }
            
            response = await self.client.post(
                f"{self.base_url}/v1/embeddings",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"vLLM embedding failed with status {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Extract embedding from response
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0]["embedding"]
            else:
                raise Exception("No embedding data returned in vLLM response")
                
        except httpx.HTTPError as e:
            raise Exception(f"vLLM embedding failed: HTTP error - {str(e)}")
        except Exception as e:
            if "vLLM embedding failed" in str(e):
                raise
            raise Exception(f"vLLM embedding failed: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if vLLM provider is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self._initialized or self.client is None:
            return False
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and capabilities.
        
        Returns:
            Dictionary with provider metadata
        """
        return {
            "name": "VLLMProvider",
            "version": "1.0",
            "capabilities": ["generation", "embedding", "chat_completion"],
            "type": "llm",
            "model": self.model,
            "base_url": self.base_url,
            "initialized": self._initialized
        }
    
    async def graceful_shutdown(self) -> None:
        """Gracefully shutdown the provider and cleanup resources."""
        if self.client is not None:
            await self.client.aclose()
            self.client = None
        self._initialized = False 
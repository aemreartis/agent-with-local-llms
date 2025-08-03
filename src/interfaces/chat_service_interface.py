from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ChatRequest:
    """Request structure for chat operations."""
    query: str
    conversation_id: Optional[str] = None
    context_limit: int = 10
    search_strategy: str = "hybrid"  # "vector", "keyword", "hybrid"
    use_reranking: bool = True
    temperature: float = 0.7
    max_tokens: Optional[int] = None


@dataclass 
class ChatResponse:
    """Response structure from chat operations."""
    response: str
    sources: List[Dict[str, Any]]
    conversation_id: str
    search_results_count: int
    reranked_results_count: Optional[int] = None
    llm_model: str = ""
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = None


class ChatServiceInterface(ABC):
    """Interface for orchestrating end-to-end chat conversations using multiple providers."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the chat service with provider registry and configuration."""
        pass
    
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat request through the full RAG pipeline:
        1. Search for relevant context (vector + keyword if hybrid)
        2. Rerank results if enabled
        3. Generate response using LLM with context
        4. Return structured response with sources
        """
        pass
    
    @abstractmethod
    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve conversation history for context."""
        pass
    
    @abstractmethod
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all underlying providers."""
        pass
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the chat service."""
        return {
            "name": self.__class__.__name__,
            "version": "1.0",
            "capabilities": [
                "multi_provider_orchestration",
                "hybrid_search",
                "reranking",
                "conversation_management",
                "context_assembly"
            ],
            "type": "chat_service"
        } 
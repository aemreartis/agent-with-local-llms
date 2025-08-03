import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional

from src.interfaces.chat_service_interface import (
    ChatServiceInterface,
    ChatRequest,
    ChatResponse
)
from src.interfaces.query_orchestrator_interface import QueryOrchestratorInterface, QueryContext, QueryType, SearchStrategy
from src.interfaces.memory_interface import MemoryInterface


class ChatService(ChatServiceInterface):
    """Orchestrates end-to-end chat conversations using multiple providers."""
    
    def __init__(self):
        """Initialize the chat service."""
        self.query_orchestrator: Optional[QueryOrchestratorInterface] = None
        self.memory_provider: Optional[MemoryInterface] = None
        self.config: Optional[Dict[str, Any]] = None
        self.max_conversation_length: int = 50
        self.conversation_ttl: int = 3600
        self.use_reranking: bool = True
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the chat service with configuration."""
        self.config = config
        self.max_conversation_length = config.get("max_conversation_length", 50)
        self.conversation_ttl = config.get("conversation_ttl", 3600)
        self.use_reranking = config.get("use_reranking", True)
    
    def generate_conversation_id(self) -> str:
        """Generate a unique conversation ID."""
        return f"conv_{uuid.uuid4().hex[:8]}"
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request through the full RAG pipeline."""
        start_time = time.time()
        
        try:
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or self.generate_conversation_id()
            
            # Get conversation history if available
            conversation_history = []
            if self.memory_provider and conversation_id:
                try:
                    conversation_history = await self.memory_provider.retrieve(conversation_id)
                    # Limit history length
                    if len(conversation_history) > self.max_conversation_length:
                        conversation_history = conversation_history[-self.max_conversation_length:]
                except Exception:
                    conversation_history = []
            
            # Build enhanced query with context if needed
            enhanced_query = request.query
            if conversation_history:
                # Add recent context to the query
                recent_context = " ".join([
                    msg.get("content", "") for msg in conversation_history[-3:]  # Last 3 messages
                ])
                enhanced_query = f"Context: {recent_context}\n\nQuery: {request.query}"
            
            # Create query context
            query_context = QueryContext(
                query=enhanced_query,
                query_type=None,  # Will be determined by orchestrator
                search_strategy=SearchStrategy.HYBRID if request.search_strategy == "hybrid" else SearchStrategy.VECTOR_ONLY,
                conversation_id=conversation_id,
                context_limit=request.context_limit,
                use_reranking=request.use_reranking,
                llm_config={
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            # Process query through orchestrator
            if self.query_orchestrator:
                query_result = await self.query_orchestrator.process_query(query_context)
                
                # Prepare sources
                sources = []
                if query_result.context_documents:
                    sources = query_result.context_documents
                
                # Store conversation in memory
                if self.memory_provider:
                    try:
                        # Store user message
                        await self.memory_provider.store(
                            conversation_id,
                            {
                                "role": "user",
                                "content": request.query,
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                            },
                            ttl=self.conversation_ttl
                        )
                        
                        # Store assistant response
                        await self.memory_provider.store(
                            conversation_id,
                            {
                                "role": "assistant", 
                                "content": query_result.llm_response,
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                            },
                            ttl=self.conversation_ttl
                        )
                    except Exception:
                        pass  # Memory storage failure shouldn't break chat
                
                processing_time = (time.time() - start_time) * 1000
                
                return ChatResponse(
                    response=query_result.llm_response,
                    sources=sources,
                    conversation_id=conversation_id,
                    search_results_count=len(query_result.search_results),
                    reranked_results_count=len(query_result.reranked_results) if query_result.reranked_results else None,
                    llm_model="",  # Could be extracted from query_result if available
                    processing_time_ms=processing_time,
                    metadata={
                        "query_type": query_result.query_type.value if query_result.query_type else None,
                        "search_strategy": query_result.search_strategy_used.value if query_result.search_strategy_used else None,
                        "processing_steps": query_result.processing_steps,
                        "error_occurred": query_result.metadata.get("error_occurred", False) if query_result.metadata else False
                    }
                )
            else:
                # Fallback response if no orchestrator
                processing_time = (time.time() - start_time) * 1000
                return ChatResponse(
                    response="Error: Query orchestrator not available",
                    sources=[],
                    conversation_id=conversation_id,
                    search_results_count=0,
                    reranked_results_count=None,
                    processing_time_ms=processing_time,
                    metadata={"error_occurred": True}
                )
                
        except Exception as e:
            # Error handling
            processing_time = (time.time() - start_time) * 1000
            conversation_id = request.conversation_id or self.generate_conversation_id()
            
            return ChatResponse(
                response=f"Error processing chat request: {str(e)}",
                sources=[],
                conversation_id=conversation_id,
                search_results_count=0,
                reranked_results_count=None,
                processing_time_ms=processing_time,
                metadata={"error_occurred": True}
            )
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve conversation history for context."""
        if not self.memory_provider:
            return []
        
        try:
            history = await self.memory_provider.retrieve(conversation_id)
            # Limit to requested number of messages
            if limit and len(history) > limit:
                history = history[-limit:]
            return history
        except Exception:
            return []
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history."""
        if not self.memory_provider:
            return False
        
        try:
            await self.memory_provider.clear(conversation_id)
            return True
        except Exception:
            return False
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all underlying providers."""
        health_status = {
            "query_orchestrator": False,
            "memory_provider": False,
            "overall_health": False
        }
        
        try:
            if self.query_orchestrator:
                query_health = await self.query_orchestrator.health_check()
                health_status["query_orchestrator"] = query_health.get("overall_health", False)
            
            if self.memory_provider:
                health_status["memory_provider"] = await self.memory_provider.health_check()
            
            # Overall health requires at least query orchestrator to be healthy
            health_status["overall_health"] = health_status["query_orchestrator"]
            
        except Exception:
            pass
        
        return health_status
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the chat service."""
        return {
            "service_name": "ChatService",
            "version": "1.0.0",
            "capabilities": [
                "multi_provider_orchestration",
                "hybrid_search",
                "reranking", 
                "conversation_management",
                "context_assembly",
                "memory_persistence"
            ],
            "max_conversation_length": self.max_conversation_length,
            "conversation_ttl": self.conversation_ttl,
            "use_reranking": self.use_reranking,
            "dependencies": [
                "QueryOrchestrator",
                "MemoryProvider"
            ]
        } 
"""
RAG Pipeline Orchestrator

Implements the flow: User Input → RAG → Rerank → LLM → Agent Response
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.interfaces.search_orchestrator_interface import SearchOrchestratorInterface
from src.interfaces.query_orchestrator_interface import QueryOrchestratorInterface
from src.interfaces.llm_interface import LLMInterface
from src.interfaces.memory_interface import MemoryInterface
from src.interfaces.reranker_interface import RerankerInterface

logger = logging.getLogger(__name__)


class RAGPipelineOrchestrator:
    """
    Orchestrates the complete RAG pipeline:
    User Input → RAG → Rerank → LLM → Agent Response
    """
    
    def __init__(
        self,
        search_orchestrator: SearchOrchestratorInterface,
        reranker: RerankerInterface,
        llm_provider: LLMInterface,
        memory_provider: MemoryInterface,
        config: Dict[str, Any]
    ):
        self.search_orchestrator = search_orchestrator
        self.reranker = reranker
        self.llm_provider = llm_provider
        self.memory_provider = memory_provider
        self.config = config
        
        # Pipeline configuration
        self.search_top_k = config.get("search_top_k", 10)
        self.rerank_top_k = config.get("rerank_top_k", 5)
        self.max_context_length = config.get("max_context_length", 4000)
        self.enable_memory = config.get("enable_memory", True)
        
        logger.info("RAG Pipeline Orchestrator initialized")
    
    async def process_query(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the complete RAG pipeline
        
        Args:
            user_input: The user's query/question
            user_id: Unique identifier for the user
            session_id: Optional session identifier
            conversation_id: Optional conversation identifier
            
        Returns:
            Dictionary containing the complete pipeline response
        """
        
        pipeline_start = datetime.now()
        logger.info(f"Starting RAG pipeline for user {user_id}: {user_input[:100]}...")
        
        try:
            # Step 1: Load conversation context from memory
            context = await self._load_conversation_context(
                user_id, session_id, conversation_id
            )
            
            # Step 2: RAG - Search for relevant documents
            search_results = await self._perform_rag_search(user_input, context)
            
            # Step 3: Rerank - Improve result relevance
            reranked_results = await self._rerank_results(user_input, search_results)
            
            # Step 4: LLM - Generate response with context
            llm_response = await self._generate_llm_response(
                user_input, reranked_results, context
            )
            
            # Step 5: Store conversation in memory
            await self._store_conversation(
                user_id, session_id, conversation_id, user_input, llm_response
            )
            
            # Calculate pipeline metrics
            pipeline_duration = (datetime.now() - pipeline_start).total_seconds()
            
            # Prepare response
            response = {
                "status": "success",
                "user_input": user_input,
                "agent_response": llm_response["response"],
                "pipeline_metrics": {
                    "total_duration": pipeline_duration,
                    "search_duration": search_results.get("duration", 0),
                    "rerank_duration": reranked_results.get("duration", 0),
                    "llm_duration": llm_response.get("duration", 0),
                    "search_results_count": len(search_results.get("results", [])),
                    "reranked_results_count": len(reranked_results.get("results", [])),
                    "context_length": len(llm_response.get("context", ""))
                },
                "search_results": search_results.get("results", []),
                "reranked_results": reranked_results.get("results", []),
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"RAG pipeline completed in {pipeline_duration:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "user_input": user_input,
                "agent_response": "I apologize, but I encountered an error processing your request. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _load_conversation_context(
        self,
        user_id: str,
        session_id: Optional[str],
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Load conversation context from memory"""
        
        if not self.enable_memory:
            return {"conversation_history": [], "session_state": {}}
        
        try:
            # Load conversation history
            history_key = f"conversation_{conversation_id or user_id}"
            conversation_history = await self.memory_provider.retrieve(history_key)
            
            # Load session state
            session_key = f"session_{session_id or user_id}"
            session_state = await self.memory_provider.retrieve(session_key)
            
            return {
                "conversation_history": conversation_history or [],
                "session_state": session_state or {},
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.warning(f"Failed to load conversation context: {e}")
            return {"conversation_history": [], "session_state": {}}
    
    async def _perform_rag_search(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 2: Perform RAG search for relevant documents"""
        
        search_start = datetime.now()
        logger.info("Performing RAG search...")
        
        try:
            # Create enhanced search query with context
            enhanced_query = self._enhance_query_with_context(user_input, context)
            
            # Perform search using search orchestrator
            search_results = await self.search_orchestrator.search(
                query=enhanced_query,
                top_k=self.search_top_k,
                filters={},  # Add any filters if needed
                include_metadata=True
            )
            
            search_duration = (datetime.now() - search_start).total_seconds()
            
            logger.info(f"RAG search completed: {len(search_results.get('results', []))} results in {search_duration:.2f}s")
            
            return {
                "results": search_results.get("results", []),
                "duration": search_duration,
                "query": enhanced_query,
                "total_results": len(search_results.get("results", []))
            }
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return {
                "results": [],
                "duration": 0,
                "error": str(e)
            }
    
    async def _rerank_results(
        self,
        user_input: str,
        search_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 3: Rerank search results for better relevance"""
        
        rerank_start = datetime.now()
        logger.info("Reranking search results...")
        
        try:
            results = search_results.get("results", [])
            
            if not results:
                logger.warning("No search results to rerank")
                return {
                    "results": [],
                    "duration": 0,
                    "original_count": 0,
                    "reranked_count": 0
                }
            
            # Prepare documents for reranking
            documents = []
            for result in results:
                documents.append({
                    "id": result.get("id", ""),
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0)
                })
            
            # Perform reranking
            reranked_documents = await self.reranker.rerank(
                query=user_input,
                documents=documents,
                top_k=self.rerank_top_k
            )
            
            rerank_duration = (datetime.now() - rerank_start).total_seconds()
            
            logger.info(f"Reranking completed: {len(reranked_documents)} results in {rerank_duration:.2f}s")
            
            return {
                "results": reranked_documents,
                "duration": rerank_duration,
                "original_count": len(results),
                "reranked_count": len(reranked_documents)
            }
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return {
                "results": search_results.get("results", []),
                "duration": 0,
                "error": str(e)
            }
    
    async def _generate_llm_response(
        self,
        user_input: str,
        reranked_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 4: Generate LLM response with context"""
        
        llm_start = datetime.now()
        logger.info("Generating LLM response...")
        
        try:
            # Prepare context for LLM
            context_text = self._prepare_context_for_llm(
                user_input, reranked_results, context
            )
            
            # Create prompt for LLM
            prompt = self._create_llm_prompt(user_input, context_text, context)
            
            # Generate response
            response = await self.llm_provider.generate(
                prompt=prompt,
                max_tokens=self.config.get("max_tokens", 1000),
                temperature=self.config.get("temperature", 0.7),
                stop_tokens=self.config.get("stop_tokens", [])
            )
            
            llm_duration = (datetime.now() - llm_start).total_seconds()
            
            logger.info(f"LLM response generated in {llm_duration:.2f}s")
            
            return {
                "response": response,
                "duration": llm_duration,
                "context": context_text,
                "prompt_length": len(prompt),
                "response_length": len(response)
            }
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return {
                "response": "I apologize, but I'm unable to generate a response at the moment. Please try again.",
                "duration": 0,
                "error": str(e)
            }
    
    async def _store_conversation(
        self,
        user_id: str,
        session_id: Optional[str],
        conversation_id: Optional[str],
        user_input: str,
        llm_response: Dict[str, Any]
    ):
        """Step 5: Store conversation in memory"""
        
        if not self.enable_memory:
            return
        
        try:
            # Store conversation history
            conversation_data = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "agent_response": llm_response.get("response", ""),
                "pipeline_metrics": llm_response.get("pipeline_metrics", {}),
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id
            }
            
            # Store in conversation memory
            history_key = f"conversation_{conversation_id or user_id}"
            await self.memory_provider.store(history_key, conversation_data)
            
            # Update session state
            session_key = f"session_{session_id or user_id}"
            session_data = {
                "last_interaction": datetime.now().isoformat(),
                "interaction_count": 1,  # This should be incremented
                "user_id": user_id
            }
            await self.memory_provider.store(session_key, session_data)
            
            logger.info(f"Conversation stored for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to store conversation: {e}")
    
    def _enhance_query_with_context(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> str:
        """Enhance user query with conversation context"""
        
        conversation_history = context.get("conversation_history", [])
        
        if not conversation_history:
            return user_input
        
        # Get recent conversation context (last 3 interactions)
        recent_context = conversation_history[-3:]
        
        # Create context-enhanced query
        context_text = ""
        for interaction in recent_context:
            if isinstance(interaction, dict):
                context_text += f"User: {interaction.get('user_input', '')}\n"
                context_text += f"Assistant: {interaction.get('agent_response', '')}\n"
        
        enhanced_query = f"Context:\n{context_text}\n\nCurrent Query: {user_input}"
        
        return enhanced_query
    
    def _prepare_context_for_llm(
        self,
        user_input: str,
        reranked_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Prepare context for LLM input"""
        
        # Get reranked documents
        documents = reranked_results.get("results", [])
        
        # Build context from documents
        context_parts = []
        
        # Add conversation history
        conversation_history = context.get("conversation_history", [])
        if conversation_history:
            history_text = "Previous Conversation:\n"
            for interaction in conversation_history[-2:]:  # Last 2 interactions
                if isinstance(interaction, dict):
                    history_text += f"User: {interaction.get('user_input', '')}\n"
                    history_text += f"Assistant: {interaction.get('agent_response', '')}\n"
            context_parts.append(history_text)
        
        # Add relevant documents
        if documents:
            documents_text = "Relevant Information:\n"
            for i, doc in enumerate(documents[:3], 1):  # Top 3 documents
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                source = metadata.get("source", "Unknown")
                
                documents_text += f"{i}. {content[:500]}...\n"
                documents_text += f"   Source: {source}\n\n"
            
            context_parts.append(documents_text)
        
        # Combine context parts
        full_context = "\n".join(context_parts)
        
        # Truncate if too long
        if len(full_context) > self.max_context_length:
            full_context = full_context[:self.max_context_length] + "..."
        
        return full_context
    
    def _create_llm_prompt(
        self,
        user_input: str,
        context_text: str,
        context: Dict[str, Any]
    ) -> str:
        """Create prompt for LLM"""
        
        system_prompt = """You are a helpful AI assistant with access to relevant information. 
Use the provided context to answer the user's question accurately and helpfully.
If the context doesn't contain enough information, say so clearly.
Always be honest about what you know and don't know."""

        prompt = f"""{system_prompt}

{context_text}

User Question: {user_input}

Please provide a helpful and accurate response based on the available information:"""

        return prompt
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all pipeline components"""
        
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check search orchestrator
            search_health = await self.search_orchestrator.health_check()
            health_status["components"]["search_orchestrator"] = search_health
            
            # Check reranker
            reranker_health = await self.reranker.health_check()
            health_status["components"]["reranker"] = reranker_health
            
            # Check LLM provider
            llm_health = await self.llm_provider.health_check()
            health_status["components"]["llm_provider"] = llm_health
            
            # Check memory provider
            memory_health = await self.memory_provider.health_check()
            health_status["components"]["memory_provider"] = memory_health
            
            # Overall health
            all_healthy = all(
                component.get("status") == "healthy" 
                for component in health_status["components"].values()
            )
            
            if not all_healthy:
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status 
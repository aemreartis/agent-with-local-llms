"""Agent Workflows.

Pre-defined workflow patterns for common agent tasks.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.interfaces.agent_interface import (
    AgentWorkflowInterface,
    AgentState,
    AgentContext,
    AgentExecutionState,
    WorkflowDefinition,
    WorkflowStep,
    AgentNodeInterface,
    ToolResult
)
from src.agents.agent_nodes import ReasoningNode


class RAGWorkflow(AgentWorkflowInterface):
    """RAG (Retrieval-Augmented Generation) workflow for document-based reasoning."""
    
    def __init__(self):
        """Initialize the RAG workflow."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._search_providers: List[str] = ["vector"]
        self._reranker: str = "bge"
        self._llm_provider: str = "vllm"
        self._max_context_length: int = 4000
        self._chunk_size: int = 512
        self._search_provider: Optional[Any] = None
        self._reranker_provider: Optional[Any] = None
        self._llm_provider_instance: Optional[Any] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the RAG workflow with configuration."""
        self._config = config.copy()
        self._search_providers = config.get("search_providers", ["vector"])
        self._reranker = config.get("reranker", "bge")
        self._llm_provider = config.get("llm_provider", "vllm")
        self._max_context_length = config.get("max_context_length", 4000)
        self._chunk_size = config.get("chunk_size", 512)
        
        # Initialize providers (would be injected in real implementation)
        self._search_provider = None  # Mock for now
        self._reranker_provider = None  # Mock for now
        self._llm_provider_instance = None  # Mock for now
        
        self._initialized = True
    
    async def execute(self, initial_state: AgentState, context: AgentContext) -> AgentState:
        """Execute the RAG workflow."""
        if not self._initialized:
            raise RuntimeError("RAG workflow not initialized")
        
        # Create a copy of the state to modify
        result_state = AgentState(
            state=AgentExecutionState.RUNNING,
            context=initial_state.context,
            data=initial_state.data.copy(),
            history=initial_state.history.copy(),
            current_step="rag_started",
            error=initial_state.error,
            created_at=initial_state.created_at,
            updated_at=datetime.now()
        )
        
        try:
            query = initial_state.data.get("query", "")
            
            # Step 1: Search for relevant documents
            result_state.current_step = "searching"
            result_state.updated_at = datetime.now()
            
            if self._search_provider:
                try:
                    search_results = await self._search_provider.search(query)
                except Exception as e:
                    result_state.state = AgentExecutionState.FAILED
                    result_state.error = str(e)
                    result_state.updated_at = datetime.now()
                    return result_state
            else:
                # Mock search results for testing
                search_results = [
                    {"content": "Document 1 content", "score": 0.9},
                    {"content": "Document 2 content", "score": 0.8}
                ]
            
            # Step 2: Rerank results
            result_state.current_step = "reranking"
            result_state.updated_at = datetime.now()
            
            if self._reranker_provider:
                reranked_results = await self._reranker_provider.rerank(search_results, query)
            else:
                # Mock reranked results for testing
                reranked_results = [
                    {"content": "Document 1 content", "score": 0.95},
                    {"content": "Document 2 content", "score": 0.85}
                ]
            
            # Step 3: Prepare context for LLM
            result_state.current_step = "preparing_context"
            result_state.updated_at = datetime.now()
            
            context_text = self._prepare_context(reranked_results, query)
            
            # Step 4: Generate answer
            result_state.current_step = "generating_answer"
            result_state.updated_at = datetime.now()
            
            if self._llm_provider_instance:
                answer = await self._llm_provider_instance.generate(
                    prompt=f"Context: {context_text}\n\nQuestion: {query}\n\nAnswer:"
                )
            else:
                # Mock answer for testing
                answer = "Based on the documents, here is the answer."
            
            # Update result state
            result_state.data["answer"] = answer
            result_state.data["retrieved_documents"] = reranked_results
            result_state.data["context"] = context_text
            result_state.state = AgentExecutionState.COMPLETED
            result_state.current_step = "rag_completed"
            result_state.updated_at = datetime.now()
            
            # Add to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "rag_execution",
                "query": query,
                "documents_retrieved": len(reranked_results),
                "answer": answer
            }
            result_state.history.append(history_entry)
            
        except Exception as e:
            result_state.state = AgentExecutionState.FAILED
            result_state.error = str(e)
            result_state.updated_at = datetime.now()
        
        return result_state
    
    async def execute_step(self, step_id: str, state: AgentState, context: AgentContext) -> AgentState:
        """Execute a specific step of the RAG workflow."""
        if not self._initialized:
            raise RuntimeError("RAG workflow not initialized")
        
        # For now, just execute the full workflow
        return await self.execute(state, context)
    
    async def health_check(self) -> bool:
        """Check if the RAG workflow is healthy."""
        return self._initialized
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the RAG workflow."""
        return {
            "type": "RAGWorkflow",
            "initialized": self._initialized,
            "search_providers": self._search_providers,
            "reranker": self._reranker,
            "llm_provider": self._llm_provider,
            "max_context_length": self._max_context_length,
            "chunk_size": self._chunk_size
        }
    
    def get_workflow_definition(self) -> WorkflowDefinition:
        """Get the workflow definition."""
        return WorkflowDefinition(
            workflow_id="rag_workflow",
            name="RAG Workflow",
            description="Retrieval-Augmented Generation workflow for document-based reasoning",
            version="1.0.0",
            steps=[
                WorkflowStep(
                    step_id="search",
                    node_id="search_node",
                    name="Document Search",
                    description="Search for relevant documents"
                ),
                WorkflowStep(
                    step_id="rerank",
                    node_id="rerank_node",
                    name="Result Reranking",
                    description="Rerank search results for relevance"
                ),
                WorkflowStep(
                    step_id="generate",
                    node_id="llm_node",
                    name="Answer Generation",
                    description="Generate answer based on retrieved documents"
                )
            ],
            config=self._config,
            entry_point="search",
            exit_points=["generate"]
        )
    
    def get_available_steps(self) -> List[str]:
        """Get list of available steps in the workflow."""
        return ["search", "rerank", "generate"]
    
    def _prepare_context(self, documents: List[Dict[str, Any]], query: str) -> str:
        """Prepare context from retrieved documents."""
        context_parts = []
        current_length = 0
        
        for doc in documents:
            content = doc.get("content", "")
            if current_length + len(content) <= self._max_context_length:
                context_parts.append(content)
                current_length += len(content)
            else:
                break
        
        return "\n\n".join(context_parts)


class MultiStepReasoningWorkflow(AgentWorkflowInterface):
    """Multi-step reasoning workflow for complex problem solving."""
    
    def __init__(self):
        """Initialize the multi-step reasoning workflow."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._max_steps: int = 5
        self._reasoning_model: str = "default"
        self._temperature: float = 0.7
        self._max_tokens: int = 1000
        self._reasoning_node: Optional[ReasoningNode] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the multi-step reasoning workflow with configuration."""
        self._config = config.copy()
        self._max_steps = config.get("max_steps", 5)
        self._reasoning_model = config.get("reasoning_model", "default")
        self._temperature = config.get("temperature", 0.7)
        self._max_tokens = config.get("max_tokens", 1000)
        
        # Initialize reasoning node
        self._reasoning_node = ReasoningNode()
        await self._reasoning_node.initialize({
            "model": self._reasoning_model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens
        })
        
        self._initialized = True
    
    async def execute(self, initial_state: AgentState, context: AgentContext) -> AgentState:
        """Execute the multi-step reasoning workflow."""
        if not self._initialized:
            raise RuntimeError("Multi-step reasoning workflow not initialized")
        
        # Create a copy of the state to modify
        result_state = AgentState(
            state=AgentExecutionState.RUNNING,
            context=initial_state.context,
            data=initial_state.data.copy(),
            history=initial_state.history.copy(),
            current_step="reasoning_started",
            error=initial_state.error,
            created_at=initial_state.created_at,
            updated_at=datetime.now()
        )
        
        try:
            query = initial_state.data.get("query", "")
            current_step = 0
            
            # Execute reasoning steps
            while current_step < self._max_steps:
                result_state.current_step = f"step_{current_step + 1}"
                result_state.updated_at = datetime.now()
                
                # Execute reasoning node
                step_result = await self._reasoning_node.execute(result_state, context)
                
                if step_result.state == AgentExecutionState.FAILED:
                    result_state.state = AgentExecutionState.FAILED
                    result_state.error = step_result.error
                    result_state.updated_at = datetime.now()
                    return result_state
                
                # Update state with step result
                result_state.data.update(step_result.data)
                result_state.history.extend(step_result.history)
                
                # Check if reasoning is complete
                if step_result.state == AgentExecutionState.COMPLETED:
                    break
                
                current_step += 1
            
            # Check if max steps reached
            if current_step >= self._max_steps:
                result_state.data["max_steps_reached"] = True
            
            # Finalize result
            result_state.state = AgentExecutionState.COMPLETED
            result_state.current_step = "reasoning_completed"
            result_state.updated_at = datetime.now()
            
            # Add to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "multi_step_reasoning",
                "query": query,
                "steps_executed": current_step + 1,
                "max_steps_reached": current_step >= self._max_steps
            }
            result_state.history.append(history_entry)
            
        except Exception as e:
            result_state.state = AgentExecutionState.FAILED
            result_state.error = str(e)
            result_state.updated_at = datetime.now()
        
        return result_state
    
    async def execute_step(self, step_id: str, state: AgentState, context: AgentContext) -> AgentState:
        """Execute a specific step of the multi-step reasoning workflow."""
        if not self._initialized:
            raise RuntimeError("Multi-step reasoning workflow not initialized")
        
        # Execute single reasoning step
        return await self._reasoning_node.execute(state, context)
    
    async def health_check(self) -> bool:
        """Check if the multi-step reasoning workflow is healthy."""
        if not self._initialized:
            return False
        
        if self._reasoning_node:
            return await self._reasoning_node.health_check()
        
        return True
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the multi-step reasoning workflow."""
        return {
            "type": "MultiStepReasoningWorkflow",
            "initialized": self._initialized,
            "max_steps": self._max_steps,
            "reasoning_model": self._reasoning_model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens
        }
    
    def get_workflow_definition(self) -> WorkflowDefinition:
        """Get the workflow definition."""
        return WorkflowDefinition(
            workflow_id="multi_step_reasoning_workflow",
            name="Multi-Step Reasoning Workflow",
            description="Multi-step reasoning workflow for complex problem solving",
            version="1.0.0",
            steps=[
                WorkflowStep(
                    step_id="reasoning",
                    node_id="reasoning_node",
                    name="Reasoning",
                    description="Execute reasoning step"
                )
            ],
            config=self._config,
            entry_point="reasoning",
            exit_points=["reasoning"]
        )
    
    def get_available_steps(self) -> List[str]:
        """Get list of available steps in the workflow."""
        return ["reasoning"]


class ToolUsageWorkflow(AgentWorkflowInterface):
    """Tool usage workflow for external tool integration."""
    
    def __init__(self):
        """Initialize the tool usage workflow."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._max_tools: int = 3
        self._tool_timeout: float = 30.0
        self._enable_parallel_execution: bool = False
        self._tool_registry: Optional[Any] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the tool usage workflow with configuration."""
        self._config = config.copy()
        self._max_tools = config.get("max_tools", 3)
        self._tool_timeout = config.get("tool_timeout", 30.0)
        self._enable_parallel_execution = config.get("enable_parallel_execution", False)
        
        # Initialize tool registry (would be injected in real implementation)
        self._tool_registry = None  # Mock for now
        
        self._initialized = True
    
    async def execute(self, initial_state: AgentState, context: AgentContext) -> AgentState:
        """Execute the tool usage workflow."""
        if not self._initialized:
            raise RuntimeError("Tool usage workflow not initialized")
        
        # Create a copy of the state to modify
        result_state = AgentState(
            state=AgentExecutionState.RUNNING,
            context=initial_state.context,
            data=initial_state.data.copy(),
            history=initial_state.history.copy(),
            current_step="tool_execution_started",
            error=initial_state.error,
            created_at=initial_state.created_at,
            updated_at=datetime.now()
        )
        
        try:
            query = initial_state.data.get("query", "")
            tools = initial_state.data.get("tools", [])
            
            # Limit tools to max_tools
            if len(tools) > self._max_tools:
                tools = tools[:self._max_tools]
                result_state.data["max_tools_reached"] = True
            
            tool_results = []
            
            if self._enable_parallel_execution:
                # Execute tools in parallel
                tasks = []
                for tool_name in tools:
                    task = self._execute_tool(tool_name, query, context)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        tool_results.append({
                            "tool": tools[i],
                            "success": False,
                            "error": str(result),
                            "execution_time": 0.0
                        })
                    else:
                        tool_results.append({
                            "tool": tools[i],
                            "success": result.success,
                            "data": result.data,
                            "error": result.error,
                            "execution_time": result.execution_time
                        })
            else:
                # Execute tools sequentially
                for tool_name in tools:
                    try:
                        result = await self._execute_tool(tool_name, query, context)
                        tool_results.append({
                            "tool": tool_name,
                            "success": result.success,
                            "data": result.data,
                            "error": result.error,
                            "execution_time": result.execution_time
                        })
                    except Exception as e:
                        tool_results.append({
                            "tool": tool_name,
                            "success": False,
                            "error": str(e),
                            "execution_time": 0.0
                        })
            
            # Update result state
            result_state.data["tool_results"] = tool_results
            result_state.state = AgentExecutionState.COMPLETED
            result_state.current_step = "tool_execution_completed"
            result_state.updated_at = datetime.now()
            
            # Add to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "tool_execution",
                "query": query,
                "tools_executed": len(tools),
                "successful_tools": len([r for r in tool_results if r["success"]])
            }
            result_state.history.append(history_entry)
            
        except Exception as e:
            result_state.state = AgentExecutionState.FAILED
            result_state.error = str(e)
            result_state.updated_at = datetime.now()
        
        return result_state
    
    async def execute_step(self, step_id: str, state: AgentState, context: AgentContext) -> AgentState:
        """Execute a specific step of the tool usage workflow."""
        if not self._initialized:
            raise RuntimeError("Tool usage workflow not initialized")
        
        # Execute single tool
        if step_id.startswith("tool_"):
            tool_name = step_id[5:]  # Remove "tool_" prefix
            try:
                result = await self._execute_tool(tool_name, state.data.get("query", ""), context)
                state.data["tool_result"] = {
                    "tool": tool_name,
                    "success": result.success,
                    "data": result.data,
                    "error": result.error,
                    "execution_time": result.execution_time
                }
                state.state = AgentExecutionState.COMPLETED
            except Exception as e:
                state.state = AgentExecutionState.FAILED
                state.error = str(e)
        
        return state
    
    async def health_check(self) -> bool:
        """Check if the tool usage workflow is healthy."""
        return self._initialized
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the tool usage workflow."""
        return {
            "type": "ToolUsageWorkflow",
            "initialized": self._initialized,
            "max_tools": self._max_tools,
            "tool_timeout": self._tool_timeout,
            "enable_parallel_execution": self._enable_parallel_execution
        }
    
    def get_workflow_definition(self) -> WorkflowDefinition:
        """Get the workflow definition."""
        return WorkflowDefinition(
            workflow_id="tool_usage_workflow",
            name="Tool Usage Workflow",
            description="Workflow for executing external tools",
            version="1.0.0",
            steps=[
                WorkflowStep(
                    step_id="tool_execution",
                    node_id="tool_node",
                    name="Tool Execution",
                    description="Execute external tools"
                )
            ],
            config=self._config,
            entry_point="tool_execution",
            exit_points=["tool_execution"]
        )
    
    def get_available_steps(self) -> List[str]:
        """Get list of available steps in the workflow."""
        return ["tool_execution"]
    
    async def _execute_tool(self, tool_name: str, query: str, context: AgentContext) -> ToolResult:
        """Execute a single tool."""
        if self._tool_registry:
            return await self._tool_registry.execute_tool(tool_name, {"query": query}, context)
        else:
            # Mock tool execution for testing
            return ToolResult(
                success=True,
                data="Tool execution result",
                error=None,
                metadata={},
                execution_time=1.5
            )


class ConversationWorkflow(AgentWorkflowInterface):
    """Conversation workflow for interactive reasoning."""
    
    def __init__(self):
        """Initialize the conversation workflow."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._max_turns: int = 10
        self._memory_provider: str = "redis"
        self._context_window: int = 2000
        self._enable_sentiment_analysis: bool = False
        self._memory_provider_instance: Optional[Any] = None
        self._llm_provider: Optional[Any] = None
        self._sentiment_analyzer: Optional[Any] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the conversation workflow with configuration."""
        self._config = config.copy()
        self._max_turns = config.get("max_turns", 10)
        self._memory_provider = config.get("memory_provider", "redis")
        self._context_window = config.get("context_window", 2000)
        self._enable_sentiment_analysis = config.get("enable_sentiment_analysis", False)
        
        # Initialize providers (would be injected in real implementation)
        self._memory_provider_instance = None  # Mock for now
        self._llm_provider = None  # Mock for now
        self._sentiment_analyzer = None  # Mock for now
        
        self._initialized = True
    
    async def execute(self, initial_state: AgentState, context: AgentContext) -> AgentState:
        """Execute the conversation workflow."""
        if not self._initialized:
            raise RuntimeError("Conversation workflow not initialized")
        
        # Create a copy of the state to modify
        result_state = AgentState(
            state=AgentExecutionState.RUNNING,
            context=initial_state.context,
            data=initial_state.data.copy(),
            history=initial_state.history.copy(),
            current_step="conversation_started",
            error=initial_state.error,
            created_at=initial_state.created_at,
            updated_at=datetime.now()
        )
        
        try:
            message = initial_state.data.get("message", "")
            
            # Check turn count
            if self._memory_provider_instance:
                existing_context = await self._memory_provider_instance.retrieve_context(context.session_id)
                turn_count = existing_context.metadata.get("turn_count", 0) if existing_context else 0
            else:
                # Mock conversation context for testing
                existing_context = AgentContext(
                    session_id=context.session_id,
                    user_id=context.user_id,
                    metadata={"conversation_history": ["Hello", "Hi there!"], "turn_count": 0}
                )
                turn_count = 0
            
            if turn_count >= self._max_turns:
                result_state.data["max_turns_reached"] = True
                result_state.state = AgentExecutionState.COMPLETED
                result_state.current_step = "max_turns_reached"
                result_state.updated_at = datetime.now()
                return result_state
            
            # Step 1: Retrieve conversation context
            result_state.current_step = "retrieving_context"
            result_state.updated_at = datetime.now()
            
            if self._memory_provider_instance:
                conversation_context = await self._memory_provider_instance.retrieve_context(context.session_id)
            else:
                # Mock conversation context for testing
                conversation_context = AgentContext(
                    session_id=context.session_id,
                    user_id=context.user_id,
                    metadata={"conversation_history": ["Hello", "Hi there!"]}
                )
            
            # Step 2: Analyze sentiment (optional)
            result_state.current_step = "analyzing_sentiment"
            result_state.updated_at = datetime.now()
            
            sentiment_analysis = None
            if self._enable_sentiment_analysis and self._sentiment_analyzer:
                sentiment_analysis = await self._sentiment_analyzer.analyze(message)
            elif self._enable_sentiment_analysis:
                # Mock sentiment analysis for testing
                sentiment_analysis = {
                    "sentiment": "positive",
                    "confidence": 0.85,
                    "emotions": ["joy", "excitement"]
                }
            
            # Step 3: Generate response
            result_state.current_step = "generating_response"
            result_state.updated_at = datetime.now()
            
            if self._llm_provider:
                response = await self._llm_provider.generate(
                    prompt=self._build_conversation_prompt(message, conversation_context)
                )
            else:
                # Mock response for testing
                response = "I understand your question. Here's my response."
            
            # Step 4: Store updated context
            result_state.current_step = "storing_context"
            result_state.updated_at = datetime.now()
            
            if self._memory_provider_instance:
                updated_context = AgentContext(
                    session_id=context.session_id,
                    user_id=context.user_id,
                    metadata={
                        "turn_count": turn_count + 1,
                        "conversation_history": conversation_context.metadata.get("conversation_history", []) + [message, response]
                    }
                )
                await self._memory_provider_instance.store_context(context.session_id, updated_context)
            
            # Update result state
            result_state.data["response"] = response
            result_state.data["conversation_context"] = conversation_context.metadata
            if sentiment_analysis:
                result_state.data["sentiment_analysis"] = sentiment_analysis
            result_state.state = AgentExecutionState.COMPLETED
            result_state.current_step = "conversation_completed"
            result_state.updated_at = datetime.now()
            
            # Add to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "conversation",
                "message": message,
                "response": response,
                "turn_count": turn_count + 1
            }
            result_state.history.append(history_entry)
            
        except Exception as e:
            result_state.state = AgentExecutionState.FAILED
            result_state.error = str(e)
            result_state.updated_at = datetime.now()
        
        return result_state
    
    async def execute_step(self, step_id: str, state: AgentState, context: AgentContext) -> AgentState:
        """Execute a specific step of the conversation workflow."""
        if not self._initialized:
            raise RuntimeError("Conversation workflow not initialized")
        
        # For now, just execute the full workflow
        return await self.execute(state, context)
    
    async def health_check(self) -> bool:
        """Check if the conversation workflow is healthy."""
        return self._initialized
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the conversation workflow."""
        return {
            "type": "ConversationWorkflow",
            "initialized": self._initialized,
            "max_turns": self._max_turns,
            "memory_provider": self._memory_provider,
            "context_window": self._context_window,
            "enable_sentiment_analysis": self._enable_sentiment_analysis
        }
    
    def get_workflow_definition(self) -> WorkflowDefinition:
        """Get the workflow definition."""
        return WorkflowDefinition(
            workflow_id="conversation_workflow",
            name="Conversation Workflow",
            description="Interactive conversation workflow with memory",
            version="1.0.0",
            steps=[
                WorkflowStep(
                    step_id="context_retrieval",
                    node_id="memory_node",
                    name="Context Retrieval",
                    description="Retrieve conversation context"
                ),
                WorkflowStep(
                    step_id="response_generation",
                    node_id="llm_node",
                    name="Response Generation",
                    description="Generate conversational response"
                ),
                WorkflowStep(
                    step_id="context_storage",
                    node_id="memory_node",
                    name="Context Storage",
                    description="Store updated conversation context"
                )
            ],
            config=self._config,
            entry_point="context_retrieval",
            exit_points=["context_storage"]
        )
    
    def get_available_steps(self) -> List[str]:
        """Get list of available steps in the workflow."""
        return ["context_retrieval", "response_generation", "context_storage"]
    
    def _build_conversation_prompt(self, message: str, context: AgentContext) -> str:
        """Build conversation prompt with context."""
        history = context.metadata.get("conversation_history", [])
        
        if history:
            context_text = "\n".join([f"User: {history[i]}\nAssistant: {history[i+1]}" 
                                    for i in range(0, len(history)-1, 2)])
            return f"Previous conversation:\n{context_text}\n\nUser: {message}\nAssistant:"
        else:
            return f"User: {message}\nAssistant:" 
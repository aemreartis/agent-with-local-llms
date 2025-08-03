"""Unit tests for Agent Workflows.

Tests pre-defined workflow patterns for RAG, multi-step reasoning, tool usage, and conversation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, ANY
from datetime import datetime
from typing import Dict, Any, Optional

from src.interfaces.agent_interface import (
    AgentState,
    AgentContext,
    AgentExecutionState,
    WorkflowDefinition,
    WorkflowStep,
    AgentNodeInterface,
    ToolResult
)
from src.agents.agent_workflows import (
    RAGWorkflow,
    MultiStepReasoningWorkflow,
    ToolUsageWorkflow,
    ConversationWorkflow
)


pytestmark = pytest.mark.asyncio


class TestRAGWorkflow:
    """Test RAG (Retrieval-Augmented Generation) workflow."""
    
    async def test_rag_workflow_initialization(self):
        """Test RAG workflow initialization."""
        workflow = RAGWorkflow()
        config = {
            "search_providers": ["vector", "bm25"],
            "reranker": "bge",
            "llm_provider": "vllm",
            "max_context_length": 4000,
            "chunk_size": 512
        }
        
        await workflow.initialize(config)
        
        assert workflow._initialized is True
        assert workflow._config == config
        assert workflow._search_providers == ["vector", "bm25"]
        assert workflow._reranker == "bge"
        assert workflow._llm_provider == "vllm"
    
    async def test_rag_workflow_initialization_with_defaults(self):
        """Test RAG workflow initialization with default values."""
        workflow = RAGWorkflow()
        config = {}
        
        await workflow.initialize(config)
        
        assert workflow._initialized is True
        assert workflow._config == config
        assert workflow._search_providers == ["vector"]
        assert workflow._reranker == "bge"
        assert workflow._llm_provider == "vllm"
    
    async def test_rag_workflow_execute_success(self):
        """Test successful RAG workflow execution."""
        workflow = RAGWorkflow()
        await workflow.initialize({})
        
        # Mock providers
        workflow._search_provider = AsyncMock()
        workflow._search_provider.search.return_value = [
            {"content": "Document 1 content", "score": 0.9},
            {"content": "Document 2 content", "score": 0.8}
        ]
        
        workflow._reranker_provider = AsyncMock()
        workflow._reranker_provider.rerank.return_value = [
            {"content": "Document 1 content", "score": 0.95},
            {"content": "Document 2 content", "score": 0.85}
        ]
        
        workflow._llm_provider = AsyncMock()
        workflow._llm_provider.generate.return_value = "Based on the documents, here is the answer."
        
        # Create initial state
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "What is the capital of France?"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute workflow
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "answer" in result.data
        assert result.data["answer"] == "Based on the documents, here is the answer."
        assert "retrieved_documents" in result.data
        assert len(result.data["retrieved_documents"]) == 2
        assert "context" in result.data
    
    async def test_rag_workflow_execute_not_initialized(self):
        """Test RAG workflow execution when not initialized."""
        workflow = RAGWorkflow()
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "test query"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with pytest.raises(RuntimeError, match="RAG workflow not initialized"):
            await workflow.execute(initial_state, context)
    
    async def test_rag_workflow_execute_with_search_failure(self):
        """Test RAG workflow execution with search failure."""
        workflow = RAGWorkflow()
        await workflow.initialize({})
        
        # Mock search provider to fail
        workflow._search_provider = AsyncMock()
        workflow._search_provider.search.side_effect = RuntimeError("Search failed")
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "test query"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.FAILED
        assert "Search failed" in result.error
    
    async def test_rag_workflow_health_check(self):
        """Test RAG workflow health check."""
        workflow = RAGWorkflow()
        await workflow.initialize({})
        
        result = await workflow.health_check()
        assert result is True
    
    async def test_rag_workflow_get_info(self):
        """Test RAG workflow information retrieval."""
        workflow = RAGWorkflow()
        config = {
            "search_providers": ["vector", "bm25"],
            "reranker": "bge",
            "llm_provider": "vllm"
        }
        await workflow.initialize(config)
        
        info = workflow.get_workflow_info()
        
        assert info["type"] == "RAGWorkflow"
        assert info["initialized"] is True
        assert info["search_providers"] == ["vector", "bm25"]
        assert info["reranker"] == "bge"
        assert info["llm_provider"] == "vllm"


class TestMultiStepReasoningWorkflow:
    """Test Multi-Step Reasoning workflow."""
    
    async def test_multi_step_workflow_initialization(self):
        """Test multi-step reasoning workflow initialization."""
        workflow = MultiStepReasoningWorkflow()
        config = {
            "max_steps": 5,
            "reasoning_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        await workflow.initialize(config)
        
        assert workflow._initialized is True
        assert workflow._config == config
        assert workflow._max_steps == 5
        assert workflow._reasoning_model == "gpt-4"
    
    async def test_multi_step_workflow_execute_success(self):
        """Test successful multi-step reasoning workflow execution."""
        workflow = MultiStepReasoningWorkflow()
        await workflow.initialize({})
        
        # Mock reasoning node
        workflow._reasoning_node = AsyncMock()
        workflow._reasoning_node.execute.return_value = AgentState(
            state=AgentExecutionState.COMPLETED,
            context=AgentContext(session_id="test_session"),
            data={"reasoning": "Step by step reasoning", "answer": "Final answer"},
            history=[],
            current_step="reasoning_complete",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "Solve this complex problem step by step"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "reasoning" in result.data
        assert "answer" in result.data
        assert result.data["reasoning"] == "Step by step reasoning"
        assert result.data["answer"] == "Final answer"
    
    async def test_multi_step_workflow_execute_with_max_steps_reached(self):
        """Test multi-step workflow execution with max steps reached."""
        workflow = MultiStepReasoningWorkflow()
        await workflow.initialize({"max_steps": 2})
        
        # Mock reasoning node to simulate multiple steps
        workflow._reasoning_node = AsyncMock()
        workflow._reasoning_node.execute.side_effect = [
            AgentState(
                state=AgentExecutionState.RUNNING,
                context=AgentContext(session_id="test_session"),
                data={"step": 1, "reasoning": "Step 1"},
                history=[],
                current_step="step_1",
                error=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            AgentState(
                state=AgentExecutionState.RUNNING,
                context=AgentContext(session_id="test_session"),
                data={"step": 2, "reasoning": "Step 2"},
                history=[],
                current_step="step_2",
                error=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            AgentState(
                state=AgentExecutionState.RUNNING,
                context=AgentContext(session_id="test_session"),
                data={"step": 3, "reasoning": "Step 3"},
                history=[],
                current_step="step_3",
                error=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "Complex problem"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "max_steps_reached" in result.data
        assert result.data["max_steps_reached"] is True
    
    async def test_multi_step_workflow_health_check(self):
        """Test multi-step workflow health check."""
        workflow = MultiStepReasoningWorkflow()
        await workflow.initialize({})
        
        result = await workflow.health_check()
        assert result is True
    
    async def test_multi_step_workflow_get_info(self):
        """Test multi-step workflow information retrieval."""
        workflow = MultiStepReasoningWorkflow()
        config = {
            "max_steps": 5,
            "reasoning_model": "gpt-4",
            "temperature": 0.7
        }
        await workflow.initialize(config)
        
        info = workflow.get_workflow_info()
        
        assert info["type"] == "MultiStepReasoningWorkflow"
        assert info["initialized"] is True
        assert info["max_steps"] == 5
        assert info["reasoning_model"] == "gpt-4"


class TestToolUsageWorkflow:
    """Test Tool Usage workflow."""
    
    async def test_tool_usage_workflow_initialization(self):
        """Test tool usage workflow initialization."""
        workflow = ToolUsageWorkflow()
        config = {
            "max_tools": 3,
            "tool_timeout": 30.0,
            "enable_parallel_execution": True
        }
        
        await workflow.initialize(config)
        
        assert workflow._initialized is True
        assert workflow._config == config
        assert workflow._max_tools == 3
        assert workflow._tool_timeout == 30.0
        assert workflow._enable_parallel_execution is True
    
    async def test_tool_usage_workflow_execute_success(self):
        """Test successful tool usage workflow execution."""
        workflow = ToolUsageWorkflow()
        await workflow.initialize({})
        
        # Mock tool registry
        workflow._tool_registry = AsyncMock()
        workflow._tool_registry.execute_tool.return_value = ToolResult(
            success=True,
            data="Tool execution result",
            error=None,
            metadata={},
            execution_time=1.5
        )
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "query": "Calculate 2 + 2",
                "tools": ["calculator"]
            },
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "tool_results" in result.data
        assert len(result.data["tool_results"]) == 1
        assert result.data["tool_results"][0]["tool"] == "calculator"
        assert result.data["tool_results"][0]["success"] is True
    
    async def test_tool_usage_workflow_execute_with_tool_failure(self):
        """Test tool usage workflow execution with tool failure."""
        workflow = ToolUsageWorkflow()
        await workflow.initialize({})
        
        # Mock tool registry to fail
        workflow._tool_registry = AsyncMock()
        workflow._tool_registry.execute_tool.return_value = ToolResult(
            success=False,
            data=None,
            error="Tool execution failed",
            metadata={},
            execution_time=0.5
        )
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "query": "Use calculator",
                "tools": ["calculator"]
            },
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "tool_results" in result.data
        assert result.data["tool_results"][0]["success"] is False
        assert "Tool execution failed" in result.data["tool_results"][0]["error"]
    
    async def test_tool_usage_workflow_execute_with_max_tools_reached(self):
        """Test tool usage workflow execution with max tools reached."""
        workflow = ToolUsageWorkflow()
        await workflow.initialize({"max_tools": 2})
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "query": "Use multiple tools",
                "tools": ["tool1", "tool2", "tool3", "tool4"]
            },
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "max_tools_reached" in result.data
        assert result.data["max_tools_reached"] is True
        assert len(result.data["tool_results"]) <= 2
    
    async def test_tool_usage_workflow_health_check(self):
        """Test tool usage workflow health check."""
        workflow = ToolUsageWorkflow()
        await workflow.initialize({})
        
        result = await workflow.health_check()
        assert result is True
    
    async def test_tool_usage_workflow_get_info(self):
        """Test tool usage workflow information retrieval."""
        workflow = ToolUsageWorkflow()
        config = {
            "max_tools": 3,
            "tool_timeout": 30.0,
            "enable_parallel_execution": True
        }
        await workflow.initialize(config)
        
        info = workflow.get_workflow_info()
        
        assert info["type"] == "ToolUsageWorkflow"
        assert info["initialized"] is True
        assert info["max_tools"] == 3
        assert info["tool_timeout"] == 30.0
        assert info["enable_parallel_execution"] is True


class TestConversationWorkflow:
    """Test Conversation workflow."""
    
    async def test_conversation_workflow_initialization(self):
        """Test conversation workflow initialization."""
        workflow = ConversationWorkflow()
        config = {
            "max_turns": 10,
            "memory_provider": "redis",
            "context_window": 2000,
            "enable_sentiment_analysis": True
        }
        
        await workflow.initialize(config)
        
        assert workflow._initialized is True
        assert workflow._config == config
        assert workflow._max_turns == 10
        assert workflow._memory_provider == "redis"
        assert workflow._context_window == 2000
        assert workflow._enable_sentiment_analysis is True
    
    async def test_conversation_workflow_execute_success(self):
        """Test successful conversation workflow execution."""
        workflow = ConversationWorkflow()
        await workflow.initialize({})
        
        # Mock memory provider
        workflow._memory_provider = AsyncMock()
        workflow._memory_provider.retrieve_context.return_value = AgentContext(
            session_id="test_session",
            user_id="user123",
            metadata={"conversation_history": ["Hello", "Hi there!"]}
        )
        workflow._memory_provider.store_context.return_value = True
        
        # Mock LLM provider
        workflow._llm_provider = AsyncMock()
        workflow._llm_provider.generate.return_value = "I understand your question. Here's my response."
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"message": "What is the weather like?"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "response" in result.data
        assert result.data["response"] == "I understand your question. Here's my response."
        assert "conversation_context" in result.data
    
    async def test_conversation_workflow_execute_with_max_turns_reached(self):
        """Test conversation workflow execution with max turns reached."""
        workflow = ConversationWorkflow()
        await workflow.initialize({"max_turns": 2})
        
        # Mock memory provider with existing conversation
        workflow._memory_provider_instance = AsyncMock()
        workflow._memory_provider_instance.retrieve_context.return_value = AgentContext(
            session_id="test_session",
            user_id="user123",
            metadata={"turn_count": 2}
        )
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"message": "Another message"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "max_turns_reached" in result.data
        assert result.data["max_turns_reached"] is True
    
    async def test_conversation_workflow_execute_with_sentiment_analysis(self):
        """Test conversation workflow execution with sentiment analysis."""
        workflow = ConversationWorkflow()
        await workflow.initialize({"enable_sentiment_analysis": True})
        
        # Mock providers
        workflow._memory_provider = AsyncMock()
        workflow._memory_provider.retrieve_context.return_value = AgentContext(
            session_id="test_session",
            user_id="user123"
        )
        workflow._memory_provider.store_context.return_value = True
        
        workflow._llm_provider = AsyncMock()
        workflow._llm_provider.generate.return_value = "I understand you're feeling positive!"
        
        # Mock sentiment analyzer
        workflow._sentiment_analyzer = AsyncMock()
        workflow._sentiment_analyzer.analyze.return_value = {
            "sentiment": "positive",
            "confidence": 0.85,
            "emotions": ["joy", "excitement"]
        }
        
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"message": "I'm so happy today!"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await workflow.execute(initial_state, context)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert "sentiment_analysis" in result.data
        assert result.data["sentiment_analysis"]["sentiment"] == "positive"
        assert result.data["sentiment_analysis"]["confidence"] == 0.85
    
    async def test_conversation_workflow_health_check(self):
        """Test conversation workflow health check."""
        workflow = ConversationWorkflow()
        await workflow.initialize({})
        
        result = await workflow.health_check()
        assert result is True
    
    async def test_conversation_workflow_get_info(self):
        """Test conversation workflow information retrieval."""
        workflow = ConversationWorkflow()
        config = {
            "max_turns": 10,
            "memory_provider": "redis",
            "context_window": 2000,
            "enable_sentiment_analysis": True
        }
        await workflow.initialize(config)
        
        info = workflow.get_workflow_info()
        
        assert info["type"] == "ConversationWorkflow"
        assert info["initialized"] is True
        assert info["max_turns"] == 10
        assert info["memory_provider"] == "redis"
        assert info["context_window"] == 2000
        assert info["enable_sentiment_analysis"] is True


class TestWorkflowIntegration:
    """Test workflow integration scenarios."""
    
    async def test_workflow_registration_and_execution(self):
        """Test workflow registration and execution through orchestrator."""
        # This test would verify that workflows can be registered
        # and executed through the workflow orchestrator
        pass
    
    async def test_workflow_error_handling_and_recovery(self):
        """Test workflow error handling and recovery mechanisms."""
        # This test would verify that workflows handle errors gracefully
        # and can recover from failures
        pass
    
    async def test_workflow_performance_and_scalability(self):
        """Test workflow performance and scalability."""
        # This test would verify that workflows perform well under load
        # and can scale appropriately
        pass 
"""Integration tests for Agent System.

End-to-end testing of agent workflows, tool integration, and system-wide functionality.
"""

import pytest
import asyncio
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
from src.agents.agent_orchestrator import AgentOrchestrator
from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
from src.agents.agent_workflows import (
    RAGWorkflow,
    MultiStepReasoningWorkflow,
    ToolUsageWorkflow,
    ConversationWorkflow
)
from src.agents.agent_memory import AgentMemory
from src.agents.agent_state_manager import AgentStateManager
from src.agents.tool_registry import ToolRegistry
from src.agents.agent_nodes import ReasoningNode, DecisionNode, ActionNode


pytestmark = pytest.mark.asyncio


class TestAgentSystemIntegration:
    """Test complete agent system integration."""
    
    async def test_agent_system_full_initialization(self):
        """Test complete agent system initialization."""
        # Initialize all components
        orchestrator = AgentOrchestrator()
        workflow_orchestrator = AgentWorkflowOrchestrator()
        memory = AgentMemory()
        state_manager = AgentStateManager()
        tool_registry = ToolRegistry()
        
        # Initialize with configurations
        await orchestrator.initialize({
            "max_sessions": 10,
            "session_timeout": 1800.0,
            "default_workflow": "rag_workflow"
        })
        
        await workflow_orchestrator.initialize({
            "max_concurrent_workflows": 5,
            "workflow_timeout": 300.0
        })
        
        await memory.initialize({
            "provider": "inmemory",
            "session_timeout": 3600.0
        })
        
        await state_manager.initialize({
            "max_history_size": 100,
            "cleanup_interval": 300.0
        })
        
        await tool_registry.initialize({
            "max_tools": 20,
            "tool_timeout": 30.0
        })
        
        # Verify all components are initialized
        assert orchestrator._initialized is True
        assert workflow_orchestrator._initialized is True
        assert memory._initialized is True
        assert state_manager._initialized is True
        assert tool_registry._initialized is True
    
    async def test_agent_system_health_check(self):
        """Test complete agent system health check."""
        # Initialize all components
        orchestrator = AgentOrchestrator()
        workflow_orchestrator = AgentWorkflowOrchestrator()
        memory = AgentMemory()
        state_manager = AgentStateManager()
        tool_registry = ToolRegistry()
        
        # Initialize components
        await orchestrator.initialize({})
        await workflow_orchestrator.initialize({})
        await memory.initialize({})
        await state_manager.initialize({})
        await tool_registry.initialize({})
        
        # Check health of all components
        assert await orchestrator.health_check() is True
        assert await workflow_orchestrator.health_check() is True
        assert await memory.health_check() is True
        assert await state_manager.health_check() is True
        assert await tool_registry.health_check() is True
    
    async def test_agent_session_lifecycle(self):
        """Test complete agent session lifecycle."""
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({
            "max_sessions": 5,
            "session_timeout": 1800.0
        })
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        assert session_id == "test_session"
        
        # Get session state
        session_state = await orchestrator.get_session_state(session_id)
        assert session_state is not None
        assert session_state.state == AgentExecutionState.IDLE
        
        # Pause session
        paused = await orchestrator.pause_session(session_id)
        assert paused is True
        
        session_state = await orchestrator.get_session_state(session_id)
        assert session_state.state == AgentExecutionState.PAUSED
        
        # Resume session
        resumed = await orchestrator.resume_session(session_id)
        assert resumed is True
        
        session_state = await orchestrator.get_session_state(session_id)
        assert session_state.state == AgentExecutionState.IDLE
        
        # Terminate session
        terminated = await orchestrator.terminate_session(session_id)
        assert terminated is True
        
        session_state = await orchestrator.get_session_state(session_id)
        assert session_state.state == AgentExecutionState.TERMINATED
    
    async def test_workflow_registration_and_execution(self):
        """Test workflow registration and execution through orchestrator."""
        # Initialize workflow orchestrator
        workflow_orchestrator = AgentWorkflowOrchestrator()
        await workflow_orchestrator.initialize({})
        
        # Create and register workflows
        rag_workflow = RAGWorkflow()
        await rag_workflow.initialize({})
        
        multi_step_workflow = MultiStepReasoningWorkflow()
        await multi_step_workflow.initialize({})
        
        tool_workflow = ToolUsageWorkflow()
        await tool_workflow.initialize({})
        
        conversation_workflow = ConversationWorkflow()
        await conversation_workflow.initialize({})
        
        # Register workflows
        rag_definition = rag_workflow.get_workflow_definition()
        multi_step_definition = multi_step_workflow.get_workflow_definition()
        tool_definition = tool_workflow.get_workflow_definition()
        conversation_definition = conversation_workflow.get_workflow_definition()
        
        await workflow_orchestrator.register_workflow(rag_definition)
        await workflow_orchestrator.register_workflow(multi_step_definition)
        await workflow_orchestrator.register_workflow(tool_definition)
        await workflow_orchestrator.register_workflow(conversation_definition)
        
        # Verify workflows are registered
        workflows = await workflow_orchestrator.list_workflows()
        assert "RAG Workflow" in workflows
        assert "Multi-Step Reasoning Workflow" in workflows
        assert "Tool Usage Workflow" in workflows
        assert "Conversation Workflow" in workflows
        
        # Execute a workflow
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
        
        result = await workflow_orchestrator.execute_workflow("RAG Workflow", initial_state)
        assert result.state == AgentExecutionState.COMPLETED
        assert "answer" in result.data
    
    async def test_memory_and_state_integration(self):
        """Test memory and state manager integration."""
        # Initialize components
        memory = AgentMemory()
        state_manager = AgentStateManager()
        
        await memory.initialize({})
        await state_manager.initialize({})
        
        # Create context and state
        context = AgentContext(session_id="test_session", user_id="user123")
        agent_state = AgentState(
            state=AgentExecutionState.RUNNING,
            context=context,
            data={"query": "test query", "step": 1},
            history=[],
            current_step="processing",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store in both memory and state manager
        await memory.store_state("test_session", agent_state)
        await memory.store_context("test_session", context)
        
        created_state = await state_manager.create_state("test_session", context)
        assert created_state is not None
        assert created_state.context.session_id == "test_session"
        
        # Retrieve from both
        retrieved_state = await memory.retrieve_state("test_session")
        retrieved_context = await memory.retrieve_context("test_session")
        state_manager_state = await state_manager.get_state("test_session")
        
        assert retrieved_state is not None
        assert retrieved_context is not None
        assert state_manager_state is not None
        
        # Verify data consistency
        assert retrieved_state.data["query"] == "test query"
        assert retrieved_state.data["step"] == 1
        assert state_manager_state.data["query"] == "test query"
        assert state_manager_state.data["step"] == 1
    
    async def test_tool_registry_integration(self):
        """Test tool registry integration with agent workflows."""
        # Initialize tool registry
        tool_registry = ToolRegistry()
        await tool_registry.initialize({})
        
        # Create mock tools that implement ToolInterface
        from src.interfaces.agent_interface import ToolInterface
        
        class MockCalculator(ToolInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
                return ToolResult(
                    success=True,
                    data="4",
                    error=None,
                    metadata={"operation": "addition"},
                    execution_time=0.1
                )
            
            async def health_check(self) -> bool:
                return True
            
            def get_tool_info(self) -> Dict[str, Any]:
                return {
                    "name": "calculator",
                    "description": "Basic calculator"
                }
            
            def get_input_schema(self) -> Dict[str, Any]:
                return {"operation": "str", "a": "float", "b": "float"}
            
            def get_output_schema(self) -> Dict[str, Any]:
                return {"result": "str"}
        
        class MockSearch(ToolInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
                return ToolResult(
                    success=True,
                    data=["result1", "result2"],
                    error=None,
                    metadata={"query": "test"},
                    execution_time=0.5
                )
            
            async def health_check(self) -> bool:
                return True
            
            def get_tool_info(self) -> Dict[str, Any]:
                return {
                    "name": "search",
                    "description": "Search tool"
                }
            
            def get_input_schema(self) -> Dict[str, Any]:
                return {"query": "str"}
            
            def get_output_schema(self) -> Dict[str, Any]:
                return {"results": "list"}
        
        mock_calculator = MockCalculator()
        mock_search = MockSearch()
        
        # Register tools
        await tool_registry.register_tool("calculator", mock_calculator)
        await tool_registry.register_tool("search", mock_search)
        
        # Verify tools are registered
        tools = await tool_registry.list_tools()
        assert "calculator" in tools
        assert "search" in tools
        
        # Execute tools
        context = AgentContext(session_id="test_session", user_id="user123")
        
        calculator_result = await tool_registry.execute_tool("calculator", {"operation": "add", "a": 2, "b": 2}, context)
        assert calculator_result.success is True
        assert calculator_result.data == "4"
        
        search_result = await tool_registry.execute_tool("search", {"query": "test query"}, context)
        assert search_result.success is True
        assert len(search_result.data) == 2
    
    async def test_agent_node_integration(self):
        """Test agent node integration with workflows."""
        # Initialize nodes
        reasoning_node = ReasoningNode()
        decision_node = DecisionNode()
        action_node = ActionNode()
        
        await reasoning_node.initialize({})
        await decision_node.initialize({})
        await action_node.initialize({
            "available_actions": ["search", "calculate", "format"]
        })
        
        # Create context and state
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "Should I approve this request?"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute reasoning node
        reasoning_result = await reasoning_node.execute(initial_state, context)
        assert reasoning_result.state == AgentExecutionState.COMPLETED
        assert "reasoning" in reasoning_result.data
        
        # Execute decision node
        decision_result = await decision_node.execute(reasoning_result, context)
        assert decision_result.state == AgentExecutionState.COMPLETED
        assert "decision" in decision_result.data
        
        # Execute action node
        action_result = await action_node.execute(decision_result, context)
        assert action_result.state == AgentExecutionState.COMPLETED
        assert "action_result" in action_result.data
    
    async def test_end_to_end_rag_workflow(self):
        """Test end-to-end RAG workflow execution."""
        # Initialize workflow orchestrator
        workflow_orchestrator = AgentWorkflowOrchestrator()
        await workflow_orchestrator.initialize({})
        
        # Create and register RAG workflow
        rag_workflow = RAGWorkflow()
        await rag_workflow.initialize({
            "search_providers": ["vector"],
            "reranker": "bge",
            "llm_provider": "vllm"
        })
        
        rag_definition = rag_workflow.get_workflow_definition()
        await workflow_orchestrator.register_workflow(rag_definition)
        
        # Create context and state
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "What are the benefits of machine learning?"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute workflow
        result = await workflow_orchestrator.execute_workflow("RAG Workflow", initial_state)
        
        # Verify result
        assert result.state == AgentExecutionState.COMPLETED
        assert "answer" in result.data
        assert "retrieved_documents" in result.data
        assert "context" in result.data
        assert len(result.history) > 0
    
    async def test_end_to_end_multi_step_workflow(self):
        """Test end-to-end multi-step reasoning workflow execution."""
        # Initialize workflow orchestrator
        workflow_orchestrator = AgentWorkflowOrchestrator()
        await workflow_orchestrator.initialize({})
        
        # Create and register multi-step workflow
        multi_step_workflow = MultiStepReasoningWorkflow()
        await multi_step_workflow.initialize({
            "max_steps": 3,
            "reasoning_model": "default"
        })
        
        multi_step_definition = multi_step_workflow.get_workflow_definition()
        await workflow_orchestrator.register_workflow(multi_step_definition)
        
        # Create context and state
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
        
        # Execute workflow
        result = await workflow_orchestrator.execute_workflow("Multi-Step Reasoning Workflow", initial_state)
        
        # Verify result
        assert result.state == AgentExecutionState.COMPLETED
        assert "reasoning" in result.data
        assert "answer" in result.data
        assert len(result.history) > 0
    
    async def test_end_to_end_tool_workflow(self):
        """Test end-to-end tool usage workflow execution."""
        # Initialize workflow orchestrator
        workflow_orchestrator = AgentWorkflowOrchestrator()
        await workflow_orchestrator.initialize({})
        
        # Create and register tool workflow
        tool_workflow = ToolUsageWorkflow()
        await tool_workflow.initialize({
            "max_tools": 2,
            "tool_timeout": 30.0,
            "enable_parallel_execution": False
        })
        
        tool_definition = tool_workflow.get_workflow_definition()
        await workflow_orchestrator.register_workflow(tool_definition)
        
        # Create context and state
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "query": "Calculate 2 + 2 and search for information",
                "tools": ["calculator", "search"]
            },
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute workflow
        result = await workflow_orchestrator.execute_workflow("Tool Usage Workflow", initial_state)
        
        # Verify result
        assert result.state == AgentExecutionState.COMPLETED
        assert "tool_results" in result.data
        assert len(result.data["tool_results"]) == 2
        assert len(result.history) > 0
    
    async def test_end_to_end_conversation_workflow(self):
        """Test end-to-end conversation workflow execution."""
        # Initialize workflow orchestrator
        workflow_orchestrator = AgentWorkflowOrchestrator()
        await workflow_orchestrator.initialize({})
        
        # Create and register conversation workflow
        conversation_workflow = ConversationWorkflow()
        await conversation_workflow.initialize({
            "max_turns": 5,
            "memory_provider": "inmemory",
            "context_window": 2000,
            "enable_sentiment_analysis": True
        })
        
        conversation_definition = conversation_workflow.get_workflow_definition()
        await workflow_orchestrator.register_workflow(conversation_definition)
        
        # Create context and state
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"message": "Hello, how are you today?"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute workflow
        result = await workflow_orchestrator.execute_workflow("Conversation Workflow", initial_state)
        
        # Verify result
        assert result.state == AgentExecutionState.COMPLETED
        assert "response" in result.data
        assert "conversation_context" in result.data
        assert len(result.history) > 0
    
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Test workflow execution with error
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "This will cause an error"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock workflow orchestrator to simulate error
        with patch.object(orchestrator, '_workflow_orchestrator') as mock_workflow:
            mock_workflow.execute_workflow.side_effect = RuntimeError("Workflow execution failed")
            
            result = await orchestrator.execute_workflow(session_id, "test_workflow", {})
            
            assert result.state == AgentExecutionState.FAILED
            assert "Workflow execution failed" in result.error
        
        # Verify session can still be managed after error
        session_state = await orchestrator.get_session_state(session_id)
        assert session_state is not None
        
        # Test session termination after error
        terminated = await orchestrator.terminate_session(session_id)
        assert terminated is True
    
    async def test_concurrent_session_management(self):
        """Test concurrent session management."""
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({
            "max_sessions": 3,
            "session_timeout": 1800.0
        })
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            context = AgentContext(session_id=f"session_{i}", user_id=f"user_{i}")
            session_id = await orchestrator.create_session(context)
            sessions.append(session_id)
        
        # Verify all sessions created
        assert len(sessions) == 3
        for session_id in sessions:
            state = await orchestrator.get_session_state(session_id)
            assert state is not None
            assert state.state == AgentExecutionState.IDLE
        
        # Test max sessions limit
        context = AgentContext(session_id="session_4", user_id="user_4")
        with pytest.raises(RuntimeError, match="Maximum sessions reached"):
            await orchestrator.create_session(context)
        
        # Terminate one session
        await orchestrator.terminate_session("session_0")
        
        # Wait a moment for cleanup
        await asyncio.sleep(0.1)
        
        # Should be able to create new session now
        session_id = await orchestrator.create_session(context)
        assert session_id == "session_4"
    
    async def test_workflow_timeout_handling(self):
        """Test workflow timeout handling."""
        # Initialize workflow orchestrator with short timeout
        workflow_orchestrator = AgentWorkflowOrchestrator()
        await workflow_orchestrator.initialize({
            "workflow_timeout": 0.1  # 100ms timeout
        })
        
        # Create a slow workflow
        slow_workflow = AsyncMock()
        slow_workflow.execute.side_effect = lambda state, context: asyncio.sleep(1.0)
        slow_workflow.health_check.return_value = True
        
        # Create workflow definition for slow workflow
        slow_workflow_definition = WorkflowDefinition(
            workflow_id="slow_workflow",
            name="Slow Workflow",
            description="A slow workflow for testing",
            version="1.0.0",
            steps=[],
            config={},
            entry_point="start",
            exit_points=["end"]
        )
        await workflow_orchestrator.register_workflow(slow_workflow_definition)
        
        # Create context and state
        context = AgentContext(session_id="test_session", user_id="user123")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "slow query"},
            history=[],
            current_step="start",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Execute workflow (should timeout)
        result = await workflow_orchestrator.execute_workflow("Slow Workflow", initial_state)
        
        # Verify timeout handling
        assert result.state == AgentExecutionState.FAILED
        assert "timeout" in result.error.lower() or "timed out" in result.error.lower()
    
    async def test_memory_cleanup_and_persistence(self):
        """Test memory cleanup and persistence."""
        # Initialize memory with short timeout
        memory = AgentMemory()
        await memory.initialize({
            "provider": "inmemory",
            "session_timeout": 0.1  # 100ms timeout
        })
        
        # Store data
        context = AgentContext(session_id="test_session", user_id="user123")
        agent_state = AgentState(
            state=AgentExecutionState.COMPLETED,
            context=context,
            data={"result": "test result"},
            history=[],
            current_step="completed",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await memory.store_state("test_session", agent_state)
        await memory.store_context("test_session", context)
        
        # Verify data is stored
        retrieved_state = await memory.retrieve_state("test_session")
        retrieved_context = await memory.retrieve_context("test_session")
        assert retrieved_state is not None
        assert retrieved_context is not None
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        # Verify data is cleaned up
        retrieved_state = await memory.retrieve_state("test_session")
        retrieved_context = await memory.retrieve_context("test_session")
        assert retrieved_state is None
        assert retrieved_context is None
    
    async def test_tool_registry_health_monitoring(self):
        """Test tool registry health monitoring."""
        # Initialize tool registry
        tool_registry = ToolRegistry()
        await tool_registry.initialize({})
        
        # Create healthy and unhealthy tools that implement ToolInterface
        from src.interfaces.agent_interface import ToolInterface
        
        class HealthyTool(ToolInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
                return ToolResult(success=True, data="ok", error=None, metadata={}, execution_time=0.1)
            
            async def health_check(self) -> bool:
                return True
            
            def get_tool_info(self) -> Dict[str, Any]:
                return {"name": "healthy_tool"}
            
            def get_input_schema(self) -> Dict[str, Any]:
                return {"input": "str"}
            
            def get_output_schema(self) -> Dict[str, Any]:
                return {"output": "str"}
        
        class UnhealthyTool(ToolInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
                return ToolResult(success=False, data=None, error="tool failed", metadata={}, execution_time=0.1)
            
            async def health_check(self) -> bool:
                return False
            
            def get_tool_info(self) -> Dict[str, Any]:
                return {"name": "unhealthy_tool"}
            
            def get_input_schema(self) -> Dict[str, Any]:
                return {"input": "str"}
            
            def get_output_schema(self) -> Dict[str, Any]:
                return {"output": "str"}
        
        healthy_tool = HealthyTool()
        unhealthy_tool = UnhealthyTool()
        
        # Register tools
        await tool_registry.register_tool("healthy_tool", healthy_tool)
        await tool_registry.register_tool("unhealthy_tool", unhealthy_tool)
        
        # Check registry health
        registry_health = await tool_registry.health_check()
        assert registry_health is False  # Should be False due to unhealthy tool
        
        # Get registry info
        registry_info = tool_registry.get_registry_info()
        assert "healthy_tool" in registry_info["tools"]
        assert "unhealthy_tool" in registry_info["tools"]
        assert registry_info["total_tools"] == 2
        assert registry_info["healthy_tools"] == 1
        assert registry_info["unhealthy_tools"] == 1
    
    async def test_agent_system_shutdown(self):
        """Test agent system graceful shutdown."""
        # Initialize all components
        orchestrator = AgentOrchestrator()
        workflow_orchestrator = AgentWorkflowOrchestrator()
        memory = AgentMemory()
        state_manager = AgentStateManager()
        tool_registry = ToolRegistry()
        
        # Initialize components
        await orchestrator.initialize({})
        await workflow_orchestrator.initialize({})
        await memory.initialize({})
        await state_manager.initialize({})
        await tool_registry.initialize({})
        
        # Create some active sessions
        context = AgentContext(session_id="test_session", user_id="user123")
        await orchestrator.create_session(context)
        
        # Shutdown orchestrator
        await orchestrator.shutdown()
        
        # Verify shutdown
        assert orchestrator._initialized is False
        
        # Verify sessions are terminated
        session_state = await orchestrator.get_session_state("test_session")
        assert session_state is not None
        assert session_state.state == AgentExecutionState.TERMINATED


class TestAgentPerformanceIntegration:
    """Test agent system performance under load."""
    
    async def test_concurrent_workflow_execution(self):
        """Test concurrent workflow execution."""
        # Initialize workflow orchestrator
        workflow_orchestrator = AgentWorkflowOrchestrator()
        await workflow_orchestrator.initialize({
            "max_concurrent_workflows": 5
        })
        
        # Create simple workflow that actually executes
        class SimpleWorkflow:
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, initial_state: AgentState, context: AgentContext) -> AgentState:
                return AgentState(
                    state=AgentExecutionState.COMPLETED,
                    context=context,
                    data={"result": "success"},
                    history=[],
                    current_step="completed",
                    error=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            
            async def health_check(self) -> bool:
                return True
            
            def get_workflow_info(self) -> Dict[str, Any]:
                return {"name": "Simple Workflow"}
            
            def get_workflow_definition(self) -> WorkflowDefinition:
                return WorkflowDefinition(
                    workflow_id="simple_workflow",
                    name="Simple Workflow",
                    description="A simple workflow for testing",
                    version="1.0.0",
                    steps=[],
                    config={},
                    entry_point="start",
                    exit_points=["end"]
                )
        
        simple_workflow = SimpleWorkflow()
        
        # Create workflow definition for simple workflow
        simple_workflow_definition = WorkflowDefinition(
            workflow_id="simple_workflow",
            name="Simple Workflow",
            description="A simple workflow for testing",
            version="1.0.0",
            steps=[],
            config={},
            entry_point="start",
            exit_points=["end"]
        )
        await workflow_orchestrator.register_workflow(simple_workflow_definition)
        
        # Execute multiple workflows concurrently
        async def execute_workflow(session_id: str):
            context = AgentContext(session_id=session_id, user_id="user123")
            initial_state = AgentState(
                state=AgentExecutionState.IDLE,
                context=context,
                data={"query": f"query_{session_id}"},
                history=[],
                current_step="start",
                error=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            return await workflow_orchestrator.execute_workflow("Simple Workflow", initial_state)
        
        # Execute 10 workflows concurrently
        tasks = [execute_workflow(f"session_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all workflows completed successfully
        assert len(results) == 10
        for result in results:
            assert result.state == AgentExecutionState.COMPLETED
            assert result.data["result"] == "success"
    
    async def test_memory_stress_test(self):
        """Test memory system under stress."""
        # Initialize memory
        memory = AgentMemory()
        await memory.initialize({
            "provider": "inmemory",
            "session_timeout": 3600.0
        })
        
        # Create many sessions
        async def create_session(session_id: str):
            context = AgentContext(session_id=session_id, user_id="user123")
            agent_state = AgentState(
                state=AgentExecutionState.COMPLETED,
                context=context,
                data={"session_id": session_id},
                history=[],
                current_step="completed",
                error=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            await memory.store_state(session_id, agent_state)
            await memory.store_context(session_id, context)
            return session_id
        
        # Create 100 sessions concurrently
        tasks = [create_session(f"session_{i}") for i in range(100)]
        session_ids = await asyncio.gather(*tasks)
        
        # Verify all sessions are stored
        assert len(session_ids) == 100
        
        # Retrieve all sessions
        async def retrieve_session(session_id: str):
            state = await memory.retrieve_state(session_id)
            context = await memory.retrieve_context(session_id)
            return state, context
        
        retrieve_tasks = [retrieve_session(session_id) for session_id in session_ids]
        results = await asyncio.gather(*retrieve_tasks)
        
        # Verify all sessions can be retrieved
        assert len(results) == 100
        for state, context in results:
            assert state is not None
            assert context is not None
    
    async def test_tool_registry_stress_test(self):
        """Test tool registry under stress."""
        # Initialize tool registry
        tool_registry = ToolRegistry()
        await tool_registry.initialize({
            "max_tools": 50
        })
        
        # Create many tools
        async def create_tool(tool_id: str):
            from src.interfaces.agent_interface import ToolInterface
            
            class MockTool(ToolInterface):
                async def initialize(self, config: Dict[str, Any]) -> None:
                    pass
                
                async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
                    return ToolResult(
                        success=True,
                        data=f"result_{tool_id}",
                        error=None,
                        metadata={},
                        execution_time=0.1
                    )
                
                async def health_check(self) -> bool:
                    return True
                
                def get_tool_info(self) -> Dict[str, Any]:
                    return {"name": tool_id}
                
                def get_input_schema(self) -> Dict[str, Any]:
                    return {"input": "str"}
                
                def get_output_schema(self) -> Dict[str, Any]:
                    return {"output": "str"}
            
            tool = MockTool()
            await tool_registry.register_tool(tool_id, tool)
            return tool_id
        
        # Create 20 tools concurrently
        tasks = [create_tool(f"tool_{i}") for i in range(20)]
        tool_ids = await asyncio.gather(*tasks)
        
        # Verify all tools are registered
        assert len(tool_ids) == 20
        
        # Execute all tools concurrently
        async def execute_tool(tool_id: str):
            context = AgentContext(session_id="test_session", user_id="user123")
            return await tool_registry.execute_tool(tool_id, {"param": "value"}, context)
        
        execute_tasks = [execute_tool(tool_id) for tool_id in tool_ids]
        results = await asyncio.gather(*execute_tasks)
        
        # Verify all tools executed successfully
        assert len(results) == 20
        for result in results:
            assert result.success is True
            assert "result_" in result.data 
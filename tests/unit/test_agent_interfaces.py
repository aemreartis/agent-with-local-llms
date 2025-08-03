"""Unit tests for agent interfaces.

Tests the foundational interfaces and data structures for the agentic RAG system.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.interfaces.agent_interface import (
    AgentExecutionState, ToolType, AgentContext, AgentState, ToolResult,
    AgentNode, WorkflowStep, WorkflowDefinition,
    ToolInterface, AgentNodeInterface, AgentWorkflowInterface,
    AgentMemoryInterface, ToolRegistryInterface, AgentOrchestratorInterface,
    AgentStateManagerInterface
)


class TestAgentExecutionState:
    """Test agent execution state enum."""
    
    def test_agent_execution_state_values(self):
        """Test that all agent execution states have correct values."""
        assert AgentExecutionState.IDLE.value == "idle"
        assert AgentExecutionState.RUNNING.value == "running"
        assert AgentExecutionState.WAITING.value == "waiting"
        assert AgentExecutionState.COMPLETED.value == "completed"
        assert AgentExecutionState.FAILED.value == "failed"
        assert AgentExecutionState.PAUSED.value == "paused"
    
    def test_agent_execution_state_from_value(self):
        """Test creating agent execution state from value."""
        assert AgentExecutionState("idle") == AgentExecutionState.IDLE
        assert AgentExecutionState("running") == AgentExecutionState.RUNNING
        assert AgentExecutionState("waiting") == AgentExecutionState.WAITING
        assert AgentExecutionState("completed") == AgentExecutionState.COMPLETED
        assert AgentExecutionState("failed") == AgentExecutionState.FAILED
        assert AgentExecutionState("paused") == AgentExecutionState.PAUSED


class TestToolType:
    """Test tool type enum."""
    
    def test_tool_type_values(self):
        """Test that all tool types have correct values."""
        assert ToolType.SEARCH.value == "search"
        assert ToolType.CALCULATOR.value == "calculator"
        assert ToolType.WEB_BROWSER.value == "web_browser"
        assert ToolType.FILE_OPERATION.value == "file_operation"
        assert ToolType.DATABASE_QUERY.value == "database_query"
        assert ToolType.API_CALL.value == "api_call"
        assert ToolType.CUSTOM.value == "custom"
    
    def test_tool_type_from_value(self):
        """Test creating tool type from value."""
        assert ToolType("search") == ToolType.SEARCH
        assert ToolType("calculator") == ToolType.CALCULATOR
        assert ToolType("web_browser") == ToolType.WEB_BROWSER
        assert ToolType("file_operation") == ToolType.FILE_OPERATION
        assert ToolType("database_query") == ToolType.DATABASE_QUERY
        assert ToolType("api_call") == ToolType.API_CALL
        assert ToolType("custom") == ToolType.CUSTOM


class TestAgentContext:
    """Test agent context data structure."""
    
    def test_agent_context_creation(self):
        """Test creating agent context with required fields."""
        context = AgentContext(session_id="test_session")
        
        assert context.session_id == "test_session"
        assert context.user_id is None
        assert context.conversation_id is None
        assert context.metadata == {}
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.updated_at, datetime)
    
    def test_agent_context_with_optional_fields(self):
        """Test creating agent context with optional fields."""
        context = AgentContext(
            session_id="test_session",
            user_id="user123",
            conversation_id="conv456",
            metadata={"key": "value"}
        )
        
        assert context.session_id == "test_session"
        assert context.user_id == "user123"
        assert context.conversation_id == "conv456"
        assert context.metadata == {"key": "value"}
    
    def test_agent_context_default_metadata(self):
        """Test that agent context has default empty metadata."""
        context = AgentContext(session_id="test_session")
        assert context.metadata == {}


class TestAgentState:
    """Test agent state data structure."""
    
    def test_agent_state_creation(self):
        """Test creating agent state with default values."""
        state = AgentState()
        
        assert state.state == AgentExecutionState.IDLE
        assert state.context is None
        assert state.data == {}
        assert state.history == []
        assert state.current_step is None
        assert state.error is None
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)
    
    def test_agent_state_with_context(self):
        """Test creating agent state with context."""
        context = AgentContext(session_id="test_session")
        state = AgentState(context=context)
        
        assert state.context == context
        assert state.state == AgentExecutionState.IDLE
    
    def test_agent_state_with_data(self):
        """Test creating agent state with data."""
        data = {"key": "value", "number": 42}
        state = AgentState(data=data)
        
        assert state.data == data
    
    def test_agent_state_with_history(self):
        """Test creating agent state with history."""
        history = [{"step": "step1", "result": "success"}]
        state = AgentState(history=history)
        
        assert state.history == history


class TestToolResult:
    """Test tool result data structure."""
    
    def test_tool_result_creation_success(self):
        """Test creating successful tool result."""
        result = ToolResult(
            success=True,
            data={"result": "success"},
            execution_time=1.5
        )
        
        assert result.success is True
        assert result.data == {"result": "success"}
        assert result.error is None
        assert result.metadata == {}
        assert result.execution_time == 1.5
    
    def test_tool_result_creation_failure(self):
        """Test creating failed tool result."""
        result = ToolResult(
            success=False,
            data=None,
            error="Tool execution failed",
            metadata={"attempts": 3}
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error == "Tool execution failed"
        assert result.metadata == {"attempts": 3}
        assert result.execution_time == 0.0


class TestAgentNode:
    """Test agent node data structure."""
    
    def test_agent_node_creation(self):
        """Test creating agent node."""
        node = AgentNode(
            node_id="test_node",
            name="Test Node",
            description="A test node",
            input_schema={"type": "object"},
            output_schema={"type": "string"}
        )
        
        assert node.node_id == "test_node"
        assert node.name == "Test Node"
        assert node.description == "A test node"
        assert node.input_schema == {"type": "object"}
        assert node.output_schema == {"type": "string"}
        assert node.config == {}


class TestWorkflowStep:
    """Test workflow step data structure."""
    
    def test_workflow_step_creation(self):
        """Test creating workflow step."""
        step = WorkflowStep(
            step_id="step1",
            node_id="test_node",
            name="Test Step",
            description="A test step"
        )
        
        assert step.step_id == "step1"
        assert step.node_id == "test_node"
        assert step.name == "Test Step"
        assert step.description == "A test step"
        assert step.dependencies == []
        assert step.config == {}
        assert step.timeout is None
        assert step.retry_count == 0
        assert step.max_retries == 3
    
    def test_workflow_step_with_dependencies(self):
        """Test creating workflow step with dependencies."""
        step = WorkflowStep(
            step_id="step2",
            node_id="test_node",
            name="Test Step",
            description="A test step",
            dependencies=["step1"],
            timeout=30.0,
            max_retries=5
        )
        
        assert step.dependencies == ["step1"]
        assert step.timeout == 30.0
        assert step.max_retries == 5


class TestWorkflowDefinition:
    """Test workflow definition data structure."""
    
    def test_workflow_definition_creation(self):
        """Test creating workflow definition."""
        workflow = WorkflowDefinition(
            workflow_id="test_workflow",
            name="Test Workflow",
            description="A test workflow"
        )
        
        assert workflow.workflow_id == "test_workflow"
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.version == "1.0.0"
        assert workflow.steps == []
        assert workflow.config == {}
        assert workflow.entry_point is None
        assert workflow.exit_points == []
    
    def test_workflow_definition_with_steps(self):
        """Test creating workflow definition with steps."""
        step = WorkflowStep(
            step_id="step1",
            node_id="test_node",
            name="Test Step",
            description="A test step"
        )
        
        workflow = WorkflowDefinition(
            workflow_id="test_workflow",
            name="Test Workflow",
            description="A test workflow",
            steps=[step],
            entry_point="step1",
            exit_points=["step1"]
        )
        
        assert len(workflow.steps) == 1
        assert workflow.steps[0] == step
        assert workflow.entry_point == "step1"
        assert workflow.exit_points == ["step1"]


class TestToolInterface:
    """Test tool interface contract."""
    
    def test_tool_interface_methods_exist(self):
        """Test that tool interface has required methods."""
        # Create a mock tool that implements the interface
        class MockTool(ToolInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, input_data: Dict[str, Any], context) -> ToolResult:
                pass
            
            async def health_check(self) -> bool:
                return True
            
            def get_tool_info(self) -> Dict[str, Any]:
                return {}
            
            def get_input_schema(self) -> Dict[str, Any]:
                return {}
            
            def get_output_schema(self) -> Dict[str, Any]:
                return {}
        
        tool = MockTool()
        
        # Verify all required methods exist
        assert hasattr(tool, "initialize")
        assert hasattr(tool, "execute")
        assert hasattr(tool, "health_check")
        assert hasattr(tool, "get_tool_info")
        assert hasattr(tool, "get_input_schema")
        assert hasattr(tool, "get_output_schema")
    
    def test_tool_interface_contract(self):
        """Test that tool interface methods are callable."""
        class MockTool(ToolInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, input_data: Dict[str, Any], context) -> ToolResult:
                return ToolResult(success=True, data={})
            
            async def health_check(self) -> bool:
                return True
            
            def get_tool_info(self) -> Dict[str, Any]:
                return {"name": "mock_tool"}
            
            def get_input_schema(self) -> Dict[str, Any]:
                return {"type": "object"}
            
            def get_output_schema(self) -> Dict[str, Any]:
                return {"type": "object"}
        
        tool = MockTool()
        
        # Test that methods can be called
        assert tool.get_tool_info() == {"name": "mock_tool"}
        assert tool.get_input_schema() == {"type": "object"}
        assert tool.get_output_schema() == {"type": "object"}


class TestAgentNodeInterface:
    """Test agent node interface contract."""
    
    def test_agent_node_interface_methods_exist(self):
        """Test that agent node interface has required methods."""
        class MockAgentNode(AgentNodeInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, state, context) -> AgentState:
                pass
            
            async def health_check(self) -> bool:
                return True
            
            def get_node_info(self) -> Dict[str, Any]:
                return {}
            
            def get_input_schema(self) -> Dict[str, Any]:
                return {}
            
            def get_output_schema(self) -> Dict[str, Any]:
                return {}
        
        node = MockAgentNode()
        
        # Verify all required methods exist
        assert hasattr(node, "initialize")
        assert hasattr(node, "execute")
        assert hasattr(node, "health_check")
        assert hasattr(node, "get_node_info")
        assert hasattr(node, "get_input_schema")
        assert hasattr(node, "get_output_schema")


class TestAgentWorkflowInterface:
    """Test agent workflow interface contract."""
    
    def test_agent_workflow_interface_methods_exist(self):
        """Test that agent workflow interface has required methods."""
        class MockAgentWorkflow(AgentWorkflowInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def execute(self, initial_state, context) -> AgentState:
                pass
            
            async def execute_step(self, step_id: str, state, context) -> AgentState:
                pass
            
            async def health_check(self) -> bool:
                return True
            
            def get_workflow_info(self) -> Dict[str, Any]:
                return {}
            
            def get_workflow_definition(self) -> WorkflowDefinition:
                pass
            
            def get_available_steps(self) -> list:
                return []
        
        workflow = MockAgentWorkflow()
        
        # Verify all required methods exist
        assert hasattr(workflow, "initialize")
        assert hasattr(workflow, "execute")
        assert hasattr(workflow, "execute_step")
        assert hasattr(workflow, "health_check")
        assert hasattr(workflow, "get_workflow_info")
        assert hasattr(workflow, "get_workflow_definition")
        assert hasattr(workflow, "get_available_steps")


class TestAgentMemoryInterface:
    """Test agent memory interface contract."""
    
    def test_agent_memory_interface_methods_exist(self):
        """Test that agent memory interface has required methods."""
        class MockAgentMemory(AgentMemoryInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def store_state(self, session_id: str, state) -> bool:
                return True
            
            async def retrieve_state(self, session_id: str):
                return None
            
            async def store_context(self, session_id: str, context) -> bool:
                return True
            
            async def retrieve_context(self, session_id: str):
                return None
            
            async def clear_session(self, session_id: str) -> bool:
                return True
            
            async def health_check(self) -> bool:
                return True
            
            def get_memory_info(self) -> Dict[str, Any]:
                return {}
        
        memory = MockAgentMemory()
        
        # Verify all required methods exist
        assert hasattr(memory, "initialize")
        assert hasattr(memory, "store_state")
        assert hasattr(memory, "retrieve_state")
        assert hasattr(memory, "store_context")
        assert hasattr(memory, "retrieve_context")
        assert hasattr(memory, "clear_session")
        assert hasattr(memory, "health_check")
        assert hasattr(memory, "get_memory_info")


class TestToolRegistryInterface:
    """Test tool registry interface contract."""
    
    def test_tool_registry_interface_methods_exist(self):
        """Test that tool registry interface has required methods."""
        class MockToolRegistry(ToolRegistryInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def register_tool(self, tool_name: str, tool) -> bool:
                return True
            
            async def unregister_tool(self, tool_name: str) -> bool:
                return True
            
            async def get_tool(self, tool_name: str):
                return None
            
            async def list_tools(self) -> list:
                return []
            
            async def execute_tool(self, tool_name: str, input_data: Dict[str, Any], context):
                pass
            
            async def health_check(self) -> bool:
                return True
            
            def get_registry_info(self) -> Dict[str, Any]:
                return {}
        
        registry = MockToolRegistry()
        
        # Verify all required methods exist
        assert hasattr(registry, "initialize")
        assert hasattr(registry, "register_tool")
        assert hasattr(registry, "unregister_tool")
        assert hasattr(registry, "get_tool")
        assert hasattr(registry, "list_tools")
        assert hasattr(registry, "execute_tool")
        assert hasattr(registry, "health_check")
        assert hasattr(registry, "get_registry_info")


class TestAgentOrchestratorInterface:
    """Test agent orchestrator interface contract."""
    
    def test_agent_orchestrator_interface_methods_exist(self):
        """Test that agent orchestrator interface has required methods."""
        class MockAgentOrchestrator(AgentOrchestratorInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def create_session(self, context) -> str:
                return "session_id"
            
            async def execute_workflow(self, session_id: str, workflow_name: str, initial_data: Dict[str, Any]):
                pass
            
            async def get_session_state(self, session_id: str):
                return None
            
            async def pause_session(self, session_id: str) -> bool:
                return True
            
            async def resume_session(self, session_id: str) -> bool:
                return True
            
            async def terminate_session(self, session_id: str) -> bool:
                return True
            
            async def health_check(self) -> bool:
                return True
            
            def get_orchestrator_info(self) -> Dict[str, Any]:
                return {}
        
        orchestrator = MockAgentOrchestrator()
        
        # Verify all required methods exist
        assert hasattr(orchestrator, "initialize")
        assert hasattr(orchestrator, "create_session")
        assert hasattr(orchestrator, "execute_workflow")
        assert hasattr(orchestrator, "get_session_state")
        assert hasattr(orchestrator, "pause_session")
        assert hasattr(orchestrator, "resume_session")
        assert hasattr(orchestrator, "terminate_session")
        assert hasattr(orchestrator, "health_check")
        assert hasattr(orchestrator, "get_orchestrator_info")


class TestAgentStateManagerInterface:
    """Test agent state manager interface contract."""
    
    def test_agent_state_manager_interface_methods_exist(self):
        """Test that agent state manager interface has required methods."""
        class MockAgentStateManager(AgentStateManagerInterface):
            async def initialize(self, config: Dict[str, Any]) -> None:
                pass
            
            async def create_state(self, session_id: str, context) -> AgentState:
                return AgentState()
            
            async def get_state(self, session_id: str):
                return AgentState()
            
            async def update_state(self, session_id: str, state) -> bool:
                return True
            
            async def transition_state(self, session_id: str, new_state, data=None) -> bool:
                return True
            
            async def add_to_history(self, session_id: str, entry: Dict[str, Any]) -> bool:
                return True
            
            async def get_history(self, session_id: str) -> list:
                return []
            
            async def clear_history(self, session_id: str) -> bool:
                return True
            
            async def set_error(self, session_id: str, error: str) -> bool:
                return True
            
            async def clear_error(self, session_id: str) -> bool:
                return True
            
            async def delete_state(self, session_id: str) -> bool:
                return True
            
            async def list_sessions(self) -> list:
                return []
            
            async def health_check(self) -> bool:
                return True
            
            def get_state_manager_info(self) -> Dict[str, Any]:
                return {}
        
        state_manager = MockAgentStateManager()
        
        # Verify all required methods exist
        assert hasattr(state_manager, "initialize")
        assert hasattr(state_manager, "create_state")
        assert hasattr(state_manager, "get_state")
        assert hasattr(state_manager, "update_state")
        assert hasattr(state_manager, "transition_state")
        assert hasattr(state_manager, "add_to_history")
        assert hasattr(state_manager, "get_history")
        assert hasattr(state_manager, "clear_history")
        assert hasattr(state_manager, "set_error")
        assert hasattr(state_manager, "clear_error")
        assert hasattr(state_manager, "delete_state")
        assert hasattr(state_manager, "list_sessions")
        assert hasattr(state_manager, "health_check")
        assert hasattr(state_manager, "get_state_manager_info") 
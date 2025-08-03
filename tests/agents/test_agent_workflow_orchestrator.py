import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional

from src.interfaces.agent_interface import (
    AgentWorkflowOrchestratorInterface,
    AgentState,
    AgentContext,
    AgentExecutionState,
    WorkflowDefinition,
    WorkflowStep,
    AgentNodeInterface
)


class TestAgentWorkflowOrchestrator:
    """Test cases for Agent Workflow Orchestrator."""
    
    @pytest.fixture
    def mock_agent_node(self):
        """Create a mock agent node."""
        node = Mock(spec=AgentNodeInterface)
        node.initialize = AsyncMock()
        node.execute = AsyncMock()
        node.health_check = AsyncMock(return_value=True)
        node.get_node_info = AsyncMock(return_value={"name": "test_node", "type": "reasoning"})
        return node
    
    @pytest.fixture
    def sample_workflow_definition(self):
        """Create a sample workflow definition."""
        return WorkflowDefinition(
            workflow_id="test_workflow",
            name="test_workflow",
            description="Test workflow for unit testing",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    node_id="reasoning",
                    name="reasoning",
                    description="Reasoning step",
                    config={"model": "default", "max_steps": 3},
                    dependencies=[],
                    timeout=30.0
                ),
                WorkflowStep(
                    step_id="step2", 
                    node_id="decision",
                    name="decision",
                    description="Decision step",
                    config={"threshold": 0.7, "fallback_action": "request_clarification"},
                    dependencies=["step1"],
                    timeout=15.0
                ),
                WorkflowStep(
                    step_id="step3",
                    node_id="action",
                    name="action", 
                    description="Action step",
                    config={"available_actions": ["search", "calculate"], "timeout": 20.0},
                    dependencies=["step2"],
                    timeout=20.0
                )
            ],
            config={"max_execution_time": 120.0, "retry_config": {"max_retries": 3, "backoff_factor": 1.5}}
        )
    
    @pytest.fixture
    def sample_agent_context(self):
        """Create a sample agent context."""
        return AgentContext(
            session_id="test_session",
            user_id="test_user",
            metadata={"source": "test", "priority": "high", "query": "What is the capital of France?"}
        )
    
    @pytest.fixture
    def sample_agent_state(self, sample_agent_context):
        """Create a sample agent state."""
        return AgentState(
            state=AgentExecutionState.IDLE,
            context=sample_agent_context,
            data={"query": "What is the capital of France?"},
            history=[],
            error=None
        )
    
    async def test_workflow_orchestrator_initialization(self):
        """Test workflow orchestrator initialization."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        config = {
            "max_concurrent_workflows": 10,
            "default_timeout": 60.0,
            "enable_parallel_execution": True,
            "workflow_cache_size": 100
        }
        
        await orchestrator.initialize(config)
        
        assert orchestrator._initialized is True
        assert orchestrator._config == config
        assert orchestrator._max_concurrent_workflows == 10
        assert orchestrator._default_timeout == 60.0
        assert orchestrator._enable_parallel_execution is True
        assert orchestrator._workflow_cache_size == 100
    
    async def test_workflow_orchestrator_initialization_with_defaults(self):
        """Test workflow orchestrator initialization with default values."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        config = {}
        
        await orchestrator.initialize(config)
        
        assert orchestrator._initialized is True
        assert orchestrator._max_concurrent_workflows == 5  # default
        assert orchestrator._default_timeout == 30.0  # default
        assert orchestrator._enable_parallel_execution is False  # default
        assert orchestrator._workflow_cache_size == 50  # default
    
    async def test_workflow_orchestrator_register_workflow_success(self, sample_workflow_definition):
        """Test successful workflow registration."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        result = await orchestrator.register_workflow(sample_workflow_definition)
        
        assert result is True
        assert "test_workflow" in orchestrator._workflows
        assert orchestrator._workflows["test_workflow"] == sample_workflow_definition
    
    async def test_workflow_orchestrator_register_workflow_not_initialized(self, sample_workflow_definition):
        """Test workflow registration when not initialized."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        
        with pytest.raises(RuntimeError, match="Workflow orchestrator not initialized"):
            await orchestrator.register_workflow(sample_workflow_definition)
    
    async def test_workflow_orchestrator_register_duplicate_workflow(self, sample_workflow_definition):
        """Test registering a duplicate workflow."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        # Register first time
        result1 = await orchestrator.register_workflow(sample_workflow_definition)
        assert result1 is True
        
        # Register duplicate
        result2 = await orchestrator.register_workflow(sample_workflow_definition)
        assert result2 is False  # Should return False for duplicate
    
    async def test_workflow_orchestrator_get_workflow_success(self, sample_workflow_definition):
        """Test successful workflow retrieval."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(sample_workflow_definition)
        
        workflow = await orchestrator.get_workflow("test_workflow")
        
        assert workflow == sample_workflow_definition
    
    async def test_workflow_orchestrator_get_nonexistent_workflow(self):
        """Test retrieving a nonexistent workflow."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        workflow = await orchestrator.get_workflow("nonexistent")
        
        assert workflow is None
    
    async def test_workflow_orchestrator_list_workflows(self, sample_workflow_definition):
        """Test listing all registered workflows."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(sample_workflow_definition)
        
        workflows = await orchestrator.list_workflows()
        
        assert "test_workflow" in workflows
        assert len(workflows) == 1
    
    async def test_workflow_orchestrator_execute_workflow_success(self, sample_workflow_definition, sample_agent_state, mock_agent_node):
        """Test successful workflow execution."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(sample_workflow_definition)
        
        # Mock the node factory to return our mock node
        with patch.object(orchestrator, '_create_node', return_value=mock_agent_node):
            # Mock successful execution
            completed_state = AgentState(
                state=AgentExecutionState.COMPLETED,
                context=sample_agent_state.context,
                data=sample_agent_state.data,
                history=sample_agent_state.history,
                error=None
            )
            mock_agent_node.execute.return_value = completed_state
            
            result = await orchestrator.execute_workflow("test_workflow", sample_agent_state)
            
            assert result is not None
            assert result.state == AgentExecutionState.COMPLETED
            assert mock_agent_node.execute.call_count == 3  # 3 steps executed
    
    async def test_workflow_orchestrator_execute_nonexistent_workflow(self, sample_agent_state):
        """Test executing a nonexistent workflow."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        with pytest.raises(ValueError, match="Workflow 'nonexistent' not found"):
            await orchestrator.execute_workflow("nonexistent", sample_agent_state)
    
    async def test_workflow_orchestrator_execute_workflow_with_node_failure(self, sample_workflow_definition, sample_agent_state, mock_agent_node):
        """Test workflow execution with node failure."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(sample_workflow_definition)
        
        # Mock the node factory to return our mock node
        with patch.object(orchestrator, '_create_node', return_value=mock_agent_node):
            # Mock node failure
            mock_agent_node.execute.side_effect = Exception("Node execution failed")
            
            result = await orchestrator.execute_workflow("test_workflow", sample_agent_state)
            
            assert result is not None
            assert result.state == AgentExecutionState.FAILED
            assert result.error is not None
            assert "Node execution failed" in result.error
    
    async def test_workflow_orchestrator_execute_workflow_with_timeout(self, sample_workflow_definition, sample_agent_state, mock_agent_node):
        """Test workflow execution with timeout."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(sample_workflow_definition)
        
        # Mock the node factory to return our mock node
        with patch.object(orchestrator, '_create_node', return_value=mock_agent_node):
            # Mock slow execution
            async def slow_execute(state, context):
                await asyncio.sleep(0.1)  # Simulate slow execution
                return state
            
            mock_agent_node.execute.side_effect = slow_execute
            
            # Set very short timeout
            sample_workflow_definition.config["max_execution_time"] = 0.05
            
            result = await orchestrator.execute_workflow("test_workflow", sample_agent_state)
            
            assert result is not None
            assert result.state == AgentExecutionState.FAILED
            assert result.error is not None
            assert "timed out" in result.error.lower()
    
    async def test_workflow_orchestrator_execute_workflow_with_retry(self, sample_workflow_definition, sample_agent_state, mock_agent_node):
        """Test workflow execution with retry mechanism."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(sample_workflow_definition)
        
        # Mock the node factory to return our mock node
        with patch.object(orchestrator, '_create_node', return_value=mock_agent_node):
            # Mock failure then success
            call_count = 0
            async def failing_then_success(state, context):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Temporary failure")
                # Return a successful state on second attempt
                return AgentState(
                    state=AgentExecutionState.COMPLETED,
                    context=state.context,
                    data=state.data,
                    history=state.history,
                    error=None
                )
            
            mock_agent_node.execute.side_effect = failing_then_success
            
            result = await orchestrator.execute_workflow("test_workflow", sample_agent_state)
            
            assert result is not None
            assert result.state == AgentExecutionState.COMPLETED
            assert call_count == 4  # Should have retried 3 times (max_retries: 3) + 1 original
    
    async def test_workflow_orchestrator_health_check_success(self):
        """Test successful health check."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        health = await orchestrator.health_check()
        
        assert health is True
    
    async def test_workflow_orchestrator_health_check_not_initialized(self):
        """Test health check when not initialized."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        
        health = await orchestrator.health_check()
        
        assert health is False
    
    async def test_workflow_orchestrator_get_orchestrator_info(self, sample_workflow_definition):
        """Test getting orchestrator information."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(sample_workflow_definition)
        
        info = await orchestrator.get_orchestrator_info()
        
        assert info["initialized"] is True
        assert info["registered_workflows"] == 1
        assert info["max_concurrent_workflows"] == 5
        assert info["enable_parallel_execution"] is False
        assert "test_workflow" in info["workflow_names"]
    
    async def test_workflow_orchestrator_get_workflow_info(self, sample_workflow_definition):
        """Test getting workflow information."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(sample_workflow_definition)
        
        info = await orchestrator.get_workflow_info("test_workflow")
        
        assert info["name"] == "test_workflow"
        assert info["description"] == "Test workflow for unit testing"
        assert info["step_count"] == 3
        assert info["max_execution_time"] == 120.0
        assert len(info["steps"]) == 3
    
    async def test_workflow_orchestrator_get_nonexistent_workflow_info(self):
        """Test getting information for nonexistent workflow."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        info = await orchestrator.get_workflow_info("nonexistent")
        
        assert info is None
    
    async def test_workflow_orchestrator_validate_workflow_dependencies(self, sample_workflow_definition):
        """Test workflow dependency validation."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        # Test valid dependencies
        result = await orchestrator._validate_workflow_dependencies(sample_workflow_definition)
        assert result is True
        
        # Test invalid dependencies (circular dependency)
        invalid_workflow = WorkflowDefinition(
            workflow_id="invalid_workflow",
            name="invalid_workflow",
            description="Workflow with circular dependencies",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    node_id="reasoning",
                    name="step1",
                    description="Step 1",
                    config={},
                    dependencies=["step2"],
                    timeout=30.0
                ),
                WorkflowStep(
                    step_id="step2",
                    node_id="decision",
                    name="step2",
                    description="Step 2",
                    config={},
                    dependencies=["step1"],
                    timeout=30.0
                )
            ],
            config={"max_execution_time": 60.0, "retry_config": {"max_retries": 1, "backoff_factor": 1.0}}
        )
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            await orchestrator._validate_workflow_dependencies(invalid_workflow)
    
    async def test_workflow_orchestrator_create_node(self, sample_workflow_definition):
        """Test node creation from workflow step."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        step = sample_workflow_definition.steps[0]  # reasoning step
        
        # Mock the node registry
        with patch.object(orchestrator, '_provider_registry') as mock_registry:
            mock_node = Mock(spec=AgentNodeInterface)
            mock_registry.get_provider = AsyncMock(return_value=mock_node)
            
            node = await orchestrator._create_node(step)
            
            assert node is not None
            assert hasattr(node, 'execute')
            assert hasattr(node, 'health_check')
    
    async def test_workflow_orchestrator_execute_step_success(self, sample_agent_state, mock_agent_node):
        """Test successful step execution."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        step = WorkflowStep(
            step_id="test_step",
            name="test_step",
            node_id="reasoning",
            description="Test step",
            config={},
            dependencies=[],
            timeout=30.0
        )
        
        # Mock successful execution
        completed_state = AgentState(
            state=AgentExecutionState.COMPLETED,
            context=sample_agent_state.context,
            data=sample_agent_state.data,
            history=sample_agent_state.history,
            error=None
        )
        mock_agent_node.execute.return_value = completed_state
        
        result = await orchestrator._execute_step(step, sample_agent_state, mock_agent_node)
        
        assert result is not None
        assert result.state == AgentExecutionState.COMPLETED
        mock_agent_node.execute.assert_called_once()
    
    async def test_workflow_orchestrator_execute_step_with_timeout(self, sample_agent_state, mock_agent_node):
        """Test step execution with timeout."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        
        step = WorkflowStep(
            step_id="test_step",
            name="test_step",
            node_id="reasoning",
            description="Test step",
            config={},
            dependencies=[],
            timeout=0.01  # Very short timeout
        )
        
        # Mock slow execution
        async def slow_execute(state, context):
            await asyncio.sleep(0.1)
            return state
        
        mock_agent_node.execute.side_effect = slow_execute
        
        result = await orchestrator._execute_step(step, sample_agent_state, mock_agent_node)
        
        assert result is not None
        assert result.state == AgentExecutionState.FAILED
        assert result.error is not None
        assert "timed out" in result.error.lower()


class TestAgentWorkflowOrchestratorIntegration:
    """Integration tests for Agent Workflow Orchestrator."""
    
    @pytest.fixture
    def simple_workflow_definition(self):
        """Create a simple workflow for integration testing."""
        return WorkflowDefinition(
            workflow_id="simple_workflow",
            name="simple_workflow",
            description="Simple workflow for integration testing",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    node_id="reasoning",
                    name="reasoning",
                    description="Reasoning step",
                    config={"model": "default", "max_steps": 2},
                    dependencies=[],
                    timeout=30.0
                ),
                WorkflowStep(
                    step_id="step2",
                    node_id="action",
                    name="action",
                    description="Action step",
                    config={"available_actions": ["search"]},
                    dependencies=["step1"],
                    timeout=30.0
                )
            ],
            config={"max_execution_time": 60.0, "retry_config": {"max_retries": 1, "backoff_factor": 1.0}}
        )
    
    async def test_simple_workflow_execution(self, simple_workflow_definition):
        """Test execution of a simple workflow."""
        from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator
        
        orchestrator = AgentWorkflowOrchestrator()
        await orchestrator.initialize({})
        await orchestrator.register_workflow(simple_workflow_definition)
        
        context = AgentContext(
            session_id="integration_test",
            user_id="test_user",
            metadata={"test": True, "query": "What is the weather like?"}
        )
        
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "What is the weather like?"},
            history=[],
            error=None
        )
        
        # Mock the node creation to return mock nodes
        with patch.object(orchestrator, '_provider_registry') as mock_registry:
            # Create mock nodes for integration testing
            mock_reasoning_node = Mock(spec=AgentNodeInterface)
            mock_action_node = Mock(spec=AgentNodeInterface)
            
            # Mock successful execution for reasoning node
            async def reasoning_execute(state, context):
                completed_state = AgentState(
                    state=AgentExecutionState.COMPLETED,
                    context=state.context,
                    data={**state.data, "reasoning": "Mock reasoning completed"},
                    history=state.history,
                    error=None
                )
                return completed_state
            
            # Mock successful execution for action node
            async def action_execute(state, context):
                completed_state = AgentState(
                    state=AgentExecutionState.COMPLETED,
                    context=state.context,
                    data={**state.data, "action": "Mock action completed"},
                    history=state.history,
                    error=None
                )
                return completed_state
            
            mock_reasoning_node.execute = reasoning_execute
            mock_action_node.execute = action_execute
            
            async def get_provider(category, name):
                if name == "reasoning":
                    return mock_reasoning_node
                elif name == "action":
                    return mock_action_node
                else:
                    raise ValueError(f"Unknown provider: {name}")
            
            mock_registry.get_provider = get_provider
            
            result = await orchestrator.execute_workflow("simple_workflow", initial_state)
            
            assert result is not None
            assert result.state == AgentExecutionState.COMPLETED
            assert result.error is None
            assert len(result.history) >= 2  # At least 2 steps executed


# Add pytest mark for async tests
pytestmark = pytest.mark.asyncio 
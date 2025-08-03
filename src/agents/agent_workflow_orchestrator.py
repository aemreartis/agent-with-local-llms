import asyncio
import time
from typing import Dict, Any, List, Optional, Set
from abc import ABC, abstractmethod

from src.interfaces.agent_interface import (
    AgentWorkflowOrchestratorInterface,
    AgentState,
    AgentContext,
    AgentExecutionState,
    WorkflowDefinition,
    WorkflowStep,
    AgentNodeInterface
)
from src.registry.provider_registry import ProviderRegistry


class AgentWorkflowOrchestrator(AgentWorkflowOrchestratorInterface):
    """LangGraph-based workflow orchestrator for agent workflows."""
    
    def __init__(self):
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._max_concurrent_workflows: int = 5
        self._default_timeout: float = 30.0
        self._enable_parallel_execution: bool = False
        self._workflow_cache_size: int = 50
        self._active_workflows: Set[str] = set()
        self._provider_registry: Optional[ProviderRegistry] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the workflow orchestrator with configuration."""
        self._config = config.copy()
        self._max_concurrent_workflows = config.get("max_concurrent_workflows", 5)
        self._default_timeout = config.get("default_timeout", 30.0)
        self._enable_parallel_execution = config.get("enable_parallel_execution", False)
        self._workflow_cache_size = config.get("workflow_cache_size", 50)
        self._provider_registry = ProviderRegistry()
        self._initialized = True
    
    async def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Register a workflow definition."""
        if not self._initialized:
            raise RuntimeError("Workflow orchestrator not initialized")
        
        if workflow.name in self._workflows:
            return False  # Already registered
        
        # Validate workflow dependencies
        await self._validate_workflow_dependencies(workflow)
        
        self._workflows[workflow.name] = workflow
        return True
    
    async def get_workflow(self, workflow_name: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by name."""
        if not self._initialized:
            return None
        
        return self._workflows.get(workflow_name)
    
    async def list_workflows(self) -> List[str]:
        """List all registered workflow names."""
        if not self._initialized:
            return []
        
        return list(self._workflows.keys())
    
    async def execute_workflow(self, workflow_name: str, initial_state: AgentState) -> AgentState:
        """Execute a workflow with the given initial state."""
        if not self._initialized:
            raise RuntimeError("Workflow orchestrator not initialized")
        
        if workflow_name not in self._workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self._workflows[workflow_name]
        
        # Check if we can start a new workflow
        if len(self._active_workflows) >= self._max_concurrent_workflows:
            raise RuntimeError("Maximum concurrent workflows reached")
        
        workflow_id = f"{workflow_name}_{initial_state.context.session_id}_{int(time.time())}"
        self._active_workflows.add(workflow_id)
        
        try:
            return await self._execute_workflow_internal(workflow, initial_state)
        finally:
            self._active_workflows.discard(workflow_id)
    
    async def health_check(self) -> bool:
        """Check if the orchestrator is healthy."""
        return self._initialized
    
    async def get_orchestrator_info(self) -> Dict[str, Any]:
        """Get orchestrator information."""
        if not self._initialized:
            return {
                "initialized": False,
                "registered_workflows": 0,
                "active_workflows": 0,
                "max_concurrent_workflows": 0,
                "enable_parallel_execution": False,
                "workflow_names": []
            }
        
        return {
            "initialized": True,
            "registered_workflows": len(self._workflows),
            "active_workflows": len(self._active_workflows),
            "max_concurrent_workflows": self._max_concurrent_workflows,
            "enable_parallel_execution": self._enable_parallel_execution,
            "workflow_names": list(self._workflows.keys())
        }
    
    async def get_workflow_info(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a workflow."""
        if not self._initialized:
            return None
        
        workflow = self._workflows.get(workflow_name)
        if not workflow:
            return None
        
        return {
            "name": workflow.name,
            "description": workflow.description,
            "step_count": len(workflow.steps),
            "max_execution_time": workflow.config.get("max_execution_time"),
            "retry_config": workflow.config.get("retry_config"),
            "steps": [
                {
                    "id": step.step_id,
                    "name": step.name,
                    "node_type": step.node_id,
                    "dependencies": step.dependencies,
                    "timeout": step.timeout
                }
                for step in workflow.steps
            ]
        }
    
    async def _execute_workflow_internal(self, workflow: WorkflowDefinition, initial_state: AgentState) -> AgentState:
        """Internal workflow execution logic."""
        current_state = initial_state
        current_state.state = AgentExecutionState.RUNNING
        current_state.updated_at = int(time.time())
        
        start_time = time.time()
        max_execution_time = workflow.config.get("max_execution_time") or self._default_timeout
        
        try:
            # Create execution order based on dependencies
            execution_order = await self._create_execution_order(workflow.steps)
            
            # Execute steps in order
            for step_id in execution_order:
                step = next(s for s in workflow.steps if s.step_id == step_id)
                
                # Check timeout
                if time.time() - start_time > max_execution_time:
                    current_state.state = AgentExecutionState.FAILED
                    current_state.error = f"Workflow execution timed out after {max_execution_time}s"
                    current_state.updated_at = int(time.time())
                    return current_state
                
                # Execute step with retry logic
                step_result = await self._execute_step_with_retry(step, current_state, workflow.config.get("retry_config", {}))
                
                if step_result.state == AgentExecutionState.FAILED:
                    return step_result
                
                current_state = step_result
            
            # Workflow completed successfully
            current_state.state = AgentExecutionState.COMPLETED
            current_state.updated_at = int(time.time())
            return current_state
            
        except Exception as e:
            current_state.state = AgentExecutionState.FAILED
            current_state.error = f"Workflow execution failed: {str(e)}"
            current_state.updated_at = int(time.time())
            return current_state
    
    async def _create_execution_order(self, steps: List[WorkflowStep]) -> List[str]:
        """Create execution order based on dependencies (topological sort)."""
        # Build dependency graph
        graph = {step.step_id: set(step.dependencies) for step in steps}
        in_degree = {step.step_id: len(step.dependencies) for step in steps}
        
        # Find nodes with no dependencies
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        while queue:
            current = queue.pop(0)
            execution_order.append(current)
            
            # Update in-degrees of dependent nodes
            for step in steps:
                if current in step.dependencies:
                    in_degree[step.step_id] -= 1
                    if in_degree[step.step_id] == 0:
                        queue.append(step.step_id)
        
        # Check for circular dependencies
        if len(execution_order) != len(steps):
            raise ValueError("Circular dependency detected in workflow")
        
        return execution_order
    
    async def _execute_step_with_retry(self, step: WorkflowStep, state: AgentState, retry_config: Dict[str, Any]) -> AgentState:
        """Execute a step with retry logic."""
        max_retries = retry_config.get("max_retries", 1)
        backoff_factor = retry_config.get("backoff_factor", 1.0)
        
        for attempt in range(max_retries + 1):
            try:
                # Create node instance
                node = await self._create_node(step)
                
                # Execute step
                result = await self._execute_step(step, state, node)
                
                if result.state != AgentExecutionState.FAILED:
                    return result
                
                # If failed and we have retries left, wait and retry
                if attempt < max_retries:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                
                return result
                
            except Exception as e:
                if attempt < max_retries:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                
                # Final attempt failed
                state.state = AgentExecutionState.FAILED
                state.error = f"Step '{step.name}' failed after {max_retries + 1} attempts: {str(e)}"
                state.updated_at = int(time.time())
                return state
    
    async def _execute_step(self, step: WorkflowStep, state: AgentState, node: AgentNodeInterface) -> AgentState:
        """Execute a single workflow step."""
        try:
            # Execute with timeout
            if step.timeout:
                result = await asyncio.wait_for(
                    node.execute(state, state.context),
                    timeout=step.timeout
                )
            else:
                result = await node.execute(state, state.context)
            
            # Update state
            result.updated_at = int(time.time())
            
            # Add to history
            history_entry = {
                "step_id": step.step_id,
                "step_name": step.name,
                "node_type": step.node_id,
                "execution_state": result.state.value,
                "timestamp": result.updated_at,
                "data": result.data
            }
            
            if result.error:
                history_entry["error"] = result.error
            
            result.history.append(history_entry)
            
            return result
            
        except asyncio.TimeoutError:
            state.state = AgentExecutionState.FAILED
            state.error = f"Step '{step.name}' timed out after {step.timeout}s"
            state.updated_at = int(time.time())
            return state
        except Exception as e:
            state.state = AgentExecutionState.FAILED
            state.error = f"Step '{step.name}' failed: {str(e)}"
            state.updated_at = int(time.time())
            return state
    
    async def _create_node(self, step: WorkflowStep) -> AgentNodeInterface:
        """Create a node instance for the given step."""
        if not self._provider_registry:
            raise RuntimeError("Provider registry not initialized")
        
        # Get node from registry
        node = await self._provider_registry.get_provider("agent_node", step.node_id)
        
        # Initialize node with step configuration
        await node.initialize(step.config)
        
        return node
    
    async def _validate_workflow_dependencies(self, workflow: WorkflowDefinition) -> bool:
        """Validate workflow dependencies for circular references."""
        try:
            await self._create_execution_order(workflow.steps)
            return True
        except ValueError as e:
            raise ValueError(f"Invalid workflow dependencies: {str(e)}") 
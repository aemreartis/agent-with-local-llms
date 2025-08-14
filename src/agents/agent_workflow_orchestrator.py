import asyncio
import time
from typing import Dict, Any, List, Optional, Set, Callable
from abc import ABC, abstractmethod

from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph
from langchain_core.runnables import RunnableConfig

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


class LangGraphWorkflowOrchestrator(AgentWorkflowOrchestratorInterface):
    """LangGraph-based workflow orchestrator for agent workflows."""
    
    def __init__(self):
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._workflows: Dict[str, CompiledGraph] = {}
        self._workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self._max_concurrent_workflows: int = 5
        self._default_timeout: float = 30.0
        self._enable_parallel_execution: bool = False
        self._workflow_cache_size: int = 50
        self._active_workflows: Set[str] = set()
        self._provider_registry: Optional[ProviderRegistry] = None
        self._node_functions: Dict[str, Callable] = {}
    
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
        """Register a workflow definition and compile it to LangGraph."""
        if not self._initialized:
            raise RuntimeError("Workflow orchestrator not initialized")
        
        if workflow.name in self._workflows:
            return False  # Already registered
        
        # Validate workflow dependencies
        await self._validate_workflow_dependencies(workflow)
        
        # Create LangGraph StateGraph
        graph = StateGraph(dict)  # Using dict as state type for flexibility
        
        # Register node functions
        for step in workflow.steps:
            node_func = await self._create_node_function(step)
            self._node_functions[step.step_id] = node_func
            graph.add_node(step.step_id, node_func)
        
        # Add edges based on dependencies
        if workflow.entry_point:
            graph.set_entry_point(workflow.entry_point)
        
        # Add edges from workflow steps
        for step in workflow.steps:
            if step.dependencies:
                for dep in step.dependencies:
                    graph.add_edge(dep, step.step_id)
            
            # If no dependencies and not entry point, connect to entry point
            if not step.dependencies and step.step_id != workflow.entry_point:
                if workflow.entry_point:
                    graph.add_edge(workflow.entry_point, step.step_id)
        
        # Connect to END for exit points
        for exit_point in workflow.exit_points:
            graph.add_edge(exit_point, END)
        
        # If no explicit exit points, add END edge from last step
        if not workflow.exit_points and workflow.steps:
            # Find steps with no dependents
            all_deps = set()
            for step in workflow.steps:
                all_deps.update(step.dependencies)
            
            for step in workflow.steps:
                if step.step_id not in all_deps:
                    graph.add_edge(step.step_id, END)
        
        # Compile the graph
        compiled_graph = graph.compile()
        
        self._workflows[workflow.name] = compiled_graph
        self._workflow_definitions[workflow.name] = workflow
        return True
    
    async def get_workflow(self, workflow_name: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by name."""
        if not self._initialized:
            return None
        
        return self._workflow_definitions.get(workflow_name)
    
    async def list_workflows(self) -> List[str]:
        """List all registered workflow names."""
        if not self._initialized:
            return []
        
        return list(self._workflows.keys())
    
    async def execute_workflow(self, workflow_name: str, initial_state: AgentState) -> AgentState:
        """Execute a workflow with the given initial state using LangGraph."""
        if not self._initialized:
            raise RuntimeError("Workflow orchestrator not initialized")
        
        if workflow_name not in self._workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        graph = self._workflows[workflow_name]
        workflow_def = self._workflow_definitions[workflow_name]
        
        # Check if we can start a new workflow
        if len(self._active_workflows) >= self._max_concurrent_workflows:
            raise RuntimeError("Maximum concurrent workflows reached")
        
        workflow_id = f"{workflow_name}_{initial_state.context.session_id}_{int(time.time())}"
        self._active_workflows.add(workflow_id)
        
        try:
            # Convert AgentState to LangGraph state format
            langgraph_state = self._agent_state_to_langgraph_state(initial_state)
            
            # Create config with timeout
            config = RunnableConfig(
                configurable={
                    "workflow_id": workflow_id,
                    "timeout": workflow_def.config.get("max_execution_time", self._default_timeout)
                }
            )
            
            # Execute the workflow
            result_state = await graph.ainvoke(langgraph_state, config=config)
            
            # Convert back to AgentState
            final_agent_state = self._langgraph_state_to_agent_state(result_state, initial_state)
            final_agent_state.state = AgentExecutionState.COMPLETED
            final_agent_state.updated_at = time.time()
            
            return final_agent_state
            
        except Exception as e:
            # Handle workflow execution errors
            initial_state.state = AgentExecutionState.FAILED
            initial_state.error = str(e)
            initial_state.updated_at = time.time()
            return initial_state
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
            "workflow_names": list(self._workflows.keys()),
            "langgraph_version": "enabled"
        }
    
    async def get_workflow_info(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a workflow."""
        if not self._initialized:
            return None
        
        workflow = self._workflow_definitions.get(workflow_name)
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
            ],
            "engine": "langgraph"
        }
    
    async def _create_node_function(self, step: WorkflowStep) -> Callable:
        """Create a LangGraph node function from a workflow step."""
        async def node_function(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Create agent node instance
                node = await self._create_node(step)
                
                # Convert LangGraph state to AgentState
                agent_state = self._langgraph_state_to_agent_state(state)
                
                # Execute the node
                if step.timeout:
                    result = await asyncio.wait_for(
                        node.execute(agent_state, agent_state.context),
                        timeout=step.timeout
                    )
                else:
                    result = await node.execute(agent_state, agent_state.context)
                
                # Update state and return
                updated_state = self._agent_state_to_langgraph_state(result)
                
                # Add execution metadata
                updated_state["_step_metadata"] = {
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "execution_state": result.state.value,
                    "timestamp": result.updated_at,
                    "error": result.error
                }
                
                return updated_state
                
            except asyncio.TimeoutError:
                state["_error"] = f"Step '{step.name}' timed out after {step.timeout}s"
                state["_execution_state"] = AgentExecutionState.FAILED.value
                return state
            except Exception as e:
                state["_error"] = f"Step '{step.name}' failed: {str(e)}"
                state["_execution_state"] = AgentExecutionState.FAILED.value
                return state
        
        return node_function
    
    async def _create_node(self, step: WorkflowStep) -> AgentNodeInterface:
        """Create a node instance for the given step."""
        if not self._provider_registry:
            raise RuntimeError("Provider registry not initialized")
        
        # Get node from registry
        node = await self._provider_registry.get_provider("agent_node", step.node_id)
        
        # Initialize node with step configuration
        await node.initialize(step.config)
        
        return node
    
    def _agent_state_to_langgraph_state(self, agent_state: AgentState) -> Dict[str, Any]:
        """Convert AgentState to LangGraph state format."""
        return {
            "agent_state": agent_state,
            "data": agent_state.data,
            "context": agent_state.context,
            "execution_state": agent_state.state.value,
            "current_step": agent_state.current_step,
            "error": agent_state.error,
            "history": agent_state.history,
            "created_at": agent_state.created_at,
            "updated_at": agent_state.updated_at
        }
    
    def _langgraph_state_to_agent_state(self, langgraph_state: Dict[str, Any], 
                                       original_state: Optional[AgentState] = None) -> AgentState:
        """Convert LangGraph state back to AgentState."""
        if "agent_state" in langgraph_state and isinstance(langgraph_state["agent_state"], AgentState):
            # Update the existing agent state with new data
            agent_state = langgraph_state["agent_state"]
            agent_state.data.update(langgraph_state.get("data", {}))
            agent_state.error = langgraph_state.get("_error") or agent_state.error
            if langgraph_state.get("_execution_state"):
                agent_state.state = AgentExecutionState(langgraph_state["_execution_state"])
            return agent_state
        
        # Create new AgentState from LangGraph state
        if original_state:
            agent_state = AgentState(
                state=AgentExecutionState(langgraph_state.get("execution_state", "idle")),
                context=langgraph_state.get("context", original_state.context),
                data=langgraph_state.get("data", {}),
                history=langgraph_state.get("history", []),
                current_step=langgraph_state.get("current_step"),
                error=langgraph_state.get("_error"),
                created_at=langgraph_state.get("created_at", original_state.created_at),
                updated_at=langgraph_state.get("updated_at", original_state.updated_at)
            )
        else:
            agent_state = AgentState(
                state=AgentExecutionState(langgraph_state.get("execution_state", "idle")),
                context=langgraph_state.get("context"),
                data=langgraph_state.get("data", {}),
                history=langgraph_state.get("history", []),
                current_step=langgraph_state.get("current_step"),
                error=langgraph_state.get("_error")
            )
        
        return agent_state
    
    async def _validate_workflow_dependencies(self, workflow: WorkflowDefinition) -> bool:
        """Validate workflow dependencies for circular references."""
        try:
            # Build dependency graph for validation
            graph = {step.step_id: set(step.dependencies) for step in workflow.steps}
            in_degree = {step.step_id: len(step.dependencies) for step in workflow.steps}
            
            # Find nodes with no dependencies
            queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
            execution_order = []
            
            while queue:
                current = queue.pop(0)
                execution_order.append(current)
                
                # Update in-degrees of dependent nodes
                for step in workflow.steps:
                    if current in step.dependencies:
                        in_degree[step.step_id] -= 1
                        if in_degree[step.step_id] == 0:
                            queue.append(step.step_id)
            
            # Check for circular dependencies
            if len(execution_order) != len(workflow.steps):
                raise ValueError("Circular dependency detected in workflow")
            
            return True
        except ValueError as e:
            raise ValueError(f"Invalid workflow dependencies: {str(e)}")


# Keep the old class for backward compatibility
AgentWorkflowOrchestrator = LangGraphWorkflowOrchestrator 
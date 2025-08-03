"""Agent Interface - Abstract base classes for all agent components.

This module defines the foundational interfaces for the agentic RAG system,
including agent state management, workflow orchestration, tool integration,
and node-based reasoning.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
import asyncio
from dataclasses import dataclass, field
from datetime import datetime


class AgentExecutionState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ToolType(Enum):
    """Types of tools that can be used by agents."""
    SEARCH = "search"
    CALCULATOR = "calculator"
    WEB_BROWSER = "web_browser"
    FILE_OPERATION = "file_operation"
    DATABASE_QUERY = "database_query"
    API_CALL = "api_call"
    CUSTOM = "custom"


@dataclass
class AgentContext:
    """Context information for agent execution."""
    session_id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentState:
    """Agent execution state."""
    state: AgentExecutionState = AgentExecutionState.IDLE
    context: Optional[AgentContext] = None
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    current_step: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


@dataclass
class AgentNode:
    """Individual agent node for workflow execution."""
    node_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """Single step in an agent workflow."""
    step_id: str
    node_id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    workflow_id: str
    name: str
    description: str
    version: str = "1.0.0"
    steps: List[WorkflowStep] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    entry_point: Optional[str] = None
    exit_points: List[str] = field(default_factory=list)


class ToolInterface(ABC):
    """Abstract interface for all agent tools."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the tool with configuration."""
        pass
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
        """Execute the tool with input data and context."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the tool is healthy and available."""
        pass
    
    @abstractmethod
    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about the tool."""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for the tool."""
        pass


class AgentNodeInterface(ABC):
    """Abstract interface for agent nodes."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent node with configuration."""
        pass
    
    @abstractmethod
    async def execute(self, state: AgentState, context: AgentContext) -> AgentState:
        """Execute the agent node logic."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent node is healthy."""
        pass
    
    @abstractmethod
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about the agent node."""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the node."""
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for the node."""
        pass


class AgentWorkflowInterface(ABC):
    """Abstract interface for agent workflows."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent workflow with configuration."""
        pass
    
    @abstractmethod
    async def execute(self, initial_state: AgentState, context: AgentContext) -> AgentState:
        """Execute the complete agent workflow."""
        pass
    
    @abstractmethod
    async def execute_step(self, step_id: str, state: AgentState, context: AgentContext) -> AgentState:
        """Execute a specific step in the workflow."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent workflow is healthy."""
        pass
    
    @abstractmethod
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the agent workflow."""
        pass
    
    @abstractmethod
    def get_workflow_definition(self) -> WorkflowDefinition:
        """Get the workflow definition."""
        pass
    
    @abstractmethod
    def get_available_steps(self) -> List[str]:
        """Get list of available steps in the workflow."""
        pass


class AgentMemoryInterface(ABC):
    """Abstract interface for agent-specific memory."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent memory with configuration."""
        pass
    
    @abstractmethod
    async def store_state(self, session_id: str, state: AgentState) -> bool:
        """Store agent state in memory."""
        pass
    
    @abstractmethod
    async def retrieve_state(self, session_id: str) -> Optional[AgentState]:
        """Retrieve agent state from memory."""
        pass
    
    @abstractmethod
    async def store_context(self, session_id: str, context: AgentContext) -> bool:
        """Store agent context in memory."""
        pass
    
    @abstractmethod
    async def retrieve_context(self, session_id: str) -> Optional[AgentContext]:
        """Retrieve agent context from memory."""
        pass
    
    @abstractmethod
    async def clear_session(self, session_id: str) -> bool:
        """Clear all data for a session."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent memory is healthy."""
        pass
    
    @abstractmethod
    def get_memory_info(self) -> Dict[str, Any]:
        """Get information about the agent memory."""
        pass


class ToolRegistryInterface(ABC):
    """Abstract interface for tool registry."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the tool registry with configuration."""
        pass
    
    @abstractmethod
    async def register_tool(self, tool_name: str, tool: ToolInterface) -> bool:
        """Register a tool in the registry."""
        pass
    
    @abstractmethod
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool from the registry."""
        pass
    
    @abstractmethod
    async def get_tool(self, tool_name: str) -> Optional[ToolInterface]:
        """Get a tool from the registry."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[str]:
        """List all registered tools."""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
        """Execute a tool by name."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the tool registry is healthy."""
        pass
    
    @abstractmethod
    def get_registry_info(self) -> Dict[str, Any]:
        """Get information about the tool registry."""
        pass


class AgentOrchestratorInterface(ABC):
    """Abstract interface for agent orchestration."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent orchestrator with configuration."""
        pass
    
    @abstractmethod
    async def create_session(self, context: AgentContext) -> str:
        """Create a new agent session."""
        pass
    
    @abstractmethod
    async def execute_workflow(self, session_id: str, workflow_name: str, initial_data: Dict[str, Any]) -> AgentState:
        """Execute a workflow for a session."""
        pass
    
    @abstractmethod
    async def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Get the current state of a session."""
        pass
    
    @abstractmethod
    async def pause_session(self, session_id: str) -> bool:
        """Pause a running session."""
        pass
    
    @abstractmethod
    async def resume_session(self, session_id: str) -> bool:
        """Resume a paused session."""
        pass
    
    @abstractmethod
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a session."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent orchestrator is healthy."""
        pass
    
    @abstractmethod
    def get_orchestrator_info(self) -> Dict[str, Any]:
        """Get information about the agent orchestrator."""
        pass 
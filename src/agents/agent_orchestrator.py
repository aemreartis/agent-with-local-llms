"""Agent Orchestrator.

High-level agent coordination and session management with LangGraph integration.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from src.interfaces.agent_interface import (
    AgentOrchestratorInterface,
    AgentState,
    AgentContext,
    AgentExecutionState,
    WorkflowDefinition,
    WorkflowStep,
    AgentNodeInterface
)
from src.agents.agent_workflow_orchestrator import LangGraphWorkflowOrchestrator
from src.agents.langchain_workflows import (
    LangGraphToolUsageWorkflow, 
    LangGraphRAGWorkflow, 
    LangGraphConversationWorkflow,
    create_default_langgraph_state
)
from src.agents.langchain_nodes import create_langchain_tools_from_registry
from src.agents.tool_registry import ToolRegistry


class AgentOrchestrator(AgentOrchestratorInterface):
    """High-level agent orchestrator with LangGraph integration."""
    
    def __init__(self):
        """Initialize the agent orchestrator."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._sessions: Dict[str, AgentState] = {}
        self._max_sessions: int = 5
        self._session_timeout: float = 1800.0  # 30 minutes
        self._default_workflow: str = "tool_usage_workflow"
        self._enable_parallel_execution: bool = False
        self._session_cleanup_interval: float = 300.0  # 5 minutes
        self._workflow_orchestrator: Optional[LangGraphWorkflowOrchestrator] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # LangGraph workflows
        self._langgraph_workflows: Dict[str, Any] = {}
        self._tool_registry: Optional[ToolRegistry] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent orchestrator with configuration."""
        self._config = config.copy()
        self._max_sessions = config.get("max_sessions", 5)
        self._session_timeout = config.get("session_timeout", 1800.0)
        self._default_workflow = config.get("default_workflow", "tool_usage_workflow")
        self._enable_parallel_execution = config.get("enable_parallel_execution", False)
        self._session_cleanup_interval = config.get("session_cleanup_interval", 300.0)
        
        # Initialize workflow orchestrator (for backward compatibility)
        self._workflow_orchestrator = LangGraphWorkflowOrchestrator()
        workflow_config = config.get("workflow_orchestrator", {})
        await self._workflow_orchestrator.initialize(workflow_config)
        
        # Initialize tool registry
        self._tool_registry = ToolRegistry()
        tool_config = config.get("tool_registry", {})
        await self._tool_registry.initialize(tool_config)
        
        # Initialize LangGraph workflows
        await self._initialize_langgraph_workflows()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self._initialized = True
    
    async def _initialize_langgraph_workflows(self) -> None:
        """Initialize LangGraph workflows."""
        # Create default workflows
        self._langgraph_workflows["rag_workflow"] = LangGraphRAGWorkflow()
        self._langgraph_workflows["conversation_workflow"] = LangGraphConversationWorkflow()
        
        # Tool usage workflow will be created dynamically based on available tools
        # since it requires the tool registry to be populated
    
    async def create_session(self, context: AgentContext) -> str:
        """Create a new agent session."""
        if not self._initialized:
            raise RuntimeError("Agent orchestrator not initialized")
        
        # Check if session already exists
        if context.session_id in self._sessions:
            raise ValueError("Session already exists")
        
        # Check if max sessions reached
        if len(self._sessions) >= self._max_sessions:
            raise RuntimeError("Maximum sessions reached")
        
        # Create initial session state
        session_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={},
            history=[],
            current_step="created",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self._sessions[context.session_id] = session_state
        return context.session_id
    
    async def execute_workflow(self, session_id: str, workflow_name: str, initial_data: Dict[str, Any]) -> AgentState:
        """Execute a workflow for a session using LangGraph."""
        if not self._initialized:
            raise RuntimeError("Agent orchestrator not initialized")
        
        # Check if session exists
        if session_id not in self._sessions:
            raise ValueError("Session not found")
        
        session_state = self._sessions[session_id]
        
        # Check if session is terminated
        if session_state.state == AgentExecutionState.TERMINATED:
            raise RuntimeError("Session is terminated")
        
        # Use default workflow if none specified
        if workflow_name is None:
            workflow_name = self._default_workflow
        
        # Update session state to running
        session_state.state = AgentExecutionState.RUNNING
        session_state.data.update(initial_data)
        session_state.current_step = "workflow_started"
        session_state.updated_at = datetime.now()
        
        try:
            # Execute LangGraph workflow
            result = await self._execute_langgraph_workflow(workflow_name, session_state)
            
            # Update session with result
            self._sessions[session_id] = result
            return result
            
        except Exception as e:
            # Handle workflow execution errors
            session_state.state = AgentExecutionState.FAILED
            session_state.error = str(e)
            session_state.updated_at = datetime.now()
            return session_state
    
    async def _execute_langgraph_workflow(self, workflow_name: str, session_state: AgentState) -> AgentState:
        """Execute a LangGraph workflow."""
        query = session_state.data.get("query", "")
        
        if workflow_name == "tool_usage_workflow":
            # Create tool usage workflow with current tools
            if self._tool_registry:
                langchain_tools = await create_langchain_tools_from_registry(
                    self._tool_registry, session_state.context
                )
                workflow = LangGraphToolUsageWorkflow(tools=langchain_tools)
            else:
                # Fallback to empty tool list
                workflow = LangGraphToolUsageWorkflow(tools=[])
        
        elif workflow_name == "rag_workflow":
            workflow = self._langgraph_workflows.get("rag_workflow")
            if not workflow:
                raise ValueError(f"RAG workflow not initialized")
        
        elif workflow_name == "conversation_workflow":
            workflow = self._langgraph_workflows.get("conversation_workflow")
            if not workflow:
                raise ValueError(f"Conversation workflow not initialized")
        
        else:
            # Try to execute via the legacy workflow orchestrator
            return await self._workflow_orchestrator.execute_workflow(workflow_name, session_state)
        
        # Compile and execute LangGraph workflow
        compiled_workflow = workflow.compile()
        
        # Create LangGraph state
        langgraph_state = create_default_langgraph_state(query, session_state.context)
        langgraph_state["agent_state"] = session_state
        
        # Execute workflow
        result_state = await compiled_workflow.ainvoke(langgraph_state)
        
        # Extract AgentState from LangGraph result
        if "agent_state" in result_state:
            final_state = result_state["agent_state"]
            # Update with LangGraph execution data
            final_state.data.update({
                "langgraph_execution": True,
                "tools_used": result_state.get("tools_used", []),
                "reasoning_steps": result_state.get("reasoning_steps", []),
                "final_answer": result_state.get("final_answer"),
                "messages": [msg.content for msg in result_state.get("messages", [])]
            })
            final_state.state = AgentExecutionState.COMPLETED
            final_state.updated_at = datetime.now()
            return final_state
        else:
            # Fallback: create new state from result
            session_state.data.update({
                "langgraph_result": result_state,
                "final_answer": result_state.get("final_answer"),
                "tools_used": result_state.get("tools_used", [])
            })
            session_state.state = AgentExecutionState.COMPLETED
            session_state.updated_at = datetime.now()
            return session_state
    
    async def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Get the current state of a session."""
        if not self._initialized:
            return None
        
        return self._sessions.get(session_id)
    
    async def pause_session(self, session_id: str) -> bool:
        """Pause a running session."""
        if not self._initialized:
            return False
        
        if session_id not in self._sessions:
            return False
        
        session_state = self._sessions[session_id]
        
        # Only pause if not already paused or terminated
        if session_state.state not in [AgentExecutionState.PAUSED, AgentExecutionState.TERMINATED]:
            session_state.state = AgentExecutionState.PAUSED
            session_state.current_step = "paused"
            session_state.updated_at = datetime.now()
            return True
        
        return False
    
    async def resume_session(self, session_id: str) -> bool:
        """Resume a paused session."""
        if not self._initialized:
            return False
        
        if session_id not in self._sessions:
            return False
        
        session_state = self._sessions[session_id]
        
        # Only resume if paused
        if session_state.state == AgentExecutionState.PAUSED:
            session_state.state = AgentExecutionState.IDLE
            session_state.current_step = "resumed"
            session_state.updated_at = datetime.now()
            return True
        
        return False
    
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a session."""
        if not self._initialized:
            return False
        
        if session_id not in self._sessions:
            return False
        
        session_state = self._sessions[session_id]
        
        # Only terminate if not already terminated
        if session_state.state != AgentExecutionState.TERMINATED:
            session_state.state = AgentExecutionState.TERMINATED
            session_state.current_step = "terminated"
            session_state.updated_at = datetime.now()
            return True
        
        return False
    
    async def health_check(self) -> bool:
        """Check if the agent orchestrator is healthy."""
        if not self._initialized:
            return False
        
        # Check workflow orchestrator health
        if self._workflow_orchestrator:
            try:
                workflow_health = await self._workflow_orchestrator.health_check()
                if not workflow_health:
                    return False
            except Exception:
                return False
        
        # Check tool registry health
        if self._tool_registry:
            try:
                tool_health = await self._tool_registry.health_check()
                if not tool_health:
                    return False
            except Exception:
                return False
        
        return True
    
    def get_orchestrator_info(self) -> Dict[str, Any]:
        """Get information about the agent orchestrator."""
        return {
            "type": "AgentOrchestrator",
            "initialized": self._initialized,
            "max_sessions": self._max_sessions,
            "active_sessions": len(self._sessions),
            "session_timeout": self._session_timeout,
            "default_workflow": self._default_workflow,
            "enable_parallel_execution": self._enable_parallel_execution,
            "session_cleanup_interval": self._session_cleanup_interval,
            "sessions": list(self._sessions.keys()),
            "langgraph_integration": True,
            "available_workflows": list(self._langgraph_workflows.keys()) + ["tool_usage_workflow"],
            "tool_registry_initialized": self._tool_registry is not None
        }
    
    def list_sessions(self) -> List[str]:
        """List all session IDs."""
        if not self._initialized:
            return []
        
        return list(self._sessions.keys())
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a session."""
        if not self._initialized or session_id not in self._sessions:
            return None
        
        session_state = self._sessions[session_id]
        
        return {
            "session_id": session_state.context.session_id,
            "user_id": session_state.context.user_id,
            "state": session_state.state.value,
            "current_step": session_state.current_step,
            "created_at": session_state.created_at.isoformat(),
            "updated_at": session_state.updated_at.isoformat(),
            "error": session_state.error,
            "metadata": session_state.context.metadata,
            "langgraph_execution": session_state.data.get("langgraph_execution", False),
            "tools_used": session_state.data.get("tools_used", []),
            "final_answer": session_state.data.get("final_answer")
        }
    
    async def register_tool(self, tool_name: str, tool_instance) -> bool:
        """Register a tool in the tool registry."""
        if not self._tool_registry:
            return False
        return await self._tool_registry.register_tool(tool_name, tool_instance)
    
    async def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        if not self._tool_registry:
            return []
        return await self._tool_registry.list_tools()
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up expired sessions."""
        while self._initialized:
            try:
                await asyncio.sleep(self._session_cleanup_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue cleanup loop
                print(f"Session cleanup error: {e}")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        if not self._initialized:
            return
        
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_state in self._sessions.items():
            # Skip terminated sessions (they should be cleaned up immediately)
            if session_state.state == AgentExecutionState.TERMINATED:
                expired_sessions.append(session_id)
                continue
            
            # Check if session has expired
            session_age = current_time - session_state.created_at.timestamp()
            if session_age > self._session_timeout:
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            del self._sessions[session_id]
    
    async def shutdown(self) -> None:
        """Shutdown the agent orchestrator."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Terminate all active sessions
        for session_id in list(self._sessions.keys()):
            await self.terminate_session(session_id)
        
        self._initialized = False 
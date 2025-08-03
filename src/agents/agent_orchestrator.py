"""Agent Orchestrator.

High-level agent coordination and session management.
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
from src.agents.agent_workflow_orchestrator import AgentWorkflowOrchestrator


class AgentOrchestrator(AgentOrchestratorInterface):
    """High-level agent orchestrator for session management and workflow coordination."""
    
    def __init__(self):
        """Initialize the agent orchestrator."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._sessions: Dict[str, AgentState] = {}
        self._max_sessions: int = 5
        self._session_timeout: float = 1800.0  # 30 minutes
        self._default_workflow: str = "default_workflow"
        self._enable_parallel_execution: bool = False
        self._session_cleanup_interval: float = 300.0  # 5 minutes
        self._workflow_orchestrator: Optional[AgentWorkflowOrchestrator] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent orchestrator with configuration."""
        self._config = config.copy()
        self._max_sessions = config.get("max_sessions", 5)
        self._session_timeout = config.get("session_timeout", 1800.0)
        self._default_workflow = config.get("default_workflow", "default_workflow")
        self._enable_parallel_execution = config.get("enable_parallel_execution", False)
        self._session_cleanup_interval = config.get("session_cleanup_interval", 300.0)
        
        # Initialize workflow orchestrator
        self._workflow_orchestrator = AgentWorkflowOrchestrator()
        workflow_config = config.get("workflow_orchestrator", {})
        await self._workflow_orchestrator.initialize(workflow_config)
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self._initialized = True
    
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
        """Execute a workflow for a session."""
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
            # Execute workflow
            result = await self._workflow_orchestrator.execute_workflow(workflow_name, session_state)
            
            # Update session with result
            self._sessions[session_id] = result
            return result
            
        except Exception as e:
            # Handle workflow execution errors
            session_state.state = AgentExecutionState.FAILED
            session_state.error = str(e)
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
            "sessions": list(self._sessions.keys())
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
            "metadata": session_state.context.metadata
        }
    
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
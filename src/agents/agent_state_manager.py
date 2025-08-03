"""Agent State Manager Implementation.

Manages agent state transitions, history, and error handling for the agentic RAG system.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.interfaces.agent_interface import (
    AgentExecutionState, AgentContext, AgentState, AgentStateManagerInterface
)


class AgentStateManager(AgentStateManagerInterface):
    """Agent state manager implementation."""
    
    def __init__(self):
        """Initialize the agent state manager."""
        self._states: Dict[str, AgentState] = {}
        self._histories: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent state manager with configuration."""
        self._config = config.copy()
        self._states = {}
        self._histories = {}
        self._initialized = True
    
    async def create_state(self, session_id: str, context: AgentContext) -> AgentState:
        """Create a new agent state for a session."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={},
            history=[],
            current_step=None,
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self._states[session_id] = state
        self._histories[session_id] = []
        
        return state
    
    async def get_state(self, session_id: str) -> Optional[AgentState]:
        """Get the current state for a session."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        return self._states.get(session_id)
    
    async def update_state(self, session_id: str, state: AgentState) -> bool:
        """Update the state for a session."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        if session_id not in self._states:
            return False
        
        state.updated_at = datetime.now()
        self._states[session_id] = state
        return True
    
    async def transition_state(self, session_id: str, new_state: AgentExecutionState, data: Optional[Dict[str, Any]] = None) -> bool:
        """Transition the agent state to a new execution state."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        if session_id not in self._states:
            return False
        
        state = self._states[session_id]
        state.state = new_state
        state.updated_at = datetime.now()
        
        if data:
            state.data.update(data)
        
        return True
    
    async def add_to_history(self, session_id: str, entry: Dict[str, Any]) -> bool:
        """Add an entry to the agent's execution history."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        if session_id not in self._states:
            return False
        
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()
        
        self._histories[session_id].append(entry)
        
        # Enforce max history size if configured
        max_history_size = self._config.get("max_history_size")
        if max_history_size and len(self._histories[session_id]) > max_history_size:
            # Keep only the latest entries
            self._histories[session_id] = self._histories[session_id][-max_history_size:]
        
        # Update the state's history as well
        state = self._states[session_id]
        state.history = self._histories[session_id].copy()
        state.updated_at = datetime.now()
        
        return True
    
    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the execution history for a session."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        return self._histories.get(session_id, [])
    
    async def clear_history(self, session_id: str) -> bool:
        """Clear the execution history for a session."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        if session_id not in self._states:
            return False
        
        self._histories[session_id] = []
        
        # Update the state's history as well
        state = self._states[session_id]
        state.history = []
        state.updated_at = datetime.now()
        
        return True
    
    async def set_error(self, session_id: str, error: str) -> bool:
        """Set an error state for a session."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        if session_id not in self._states:
            return False
        
        state = self._states[session_id]
        state.state = AgentExecutionState.FAILED
        state.error = error
        state.updated_at = datetime.now()
        
        return True
    
    async def clear_error(self, session_id: str) -> bool:
        """Clear the error state for a session."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        if session_id not in self._states:
            return False
        
        state = self._states[session_id]
        state.error = None
        state.updated_at = datetime.now()
        
        return True
    
    async def delete_state(self, session_id: str) -> bool:
        """Delete the state for a session."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        if session_id not in self._states:
            return False
        
        del self._states[session_id]
        del self._histories[session_id]
        
        return True
    
    async def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        if not self._initialized:
            raise RuntimeError("Agent state manager not initialized")
        
        return list(self._states.keys())
    
    async def health_check(self) -> bool:
        """Check if the agent state manager is healthy."""
        return self._initialized
    
    def get_state_manager_info(self) -> Dict[str, Any]:
        """Get information about the agent state manager."""
        return {
            "type": "AgentStateManager",
            "initialized": self._initialized,
            "active_sessions": len(self._states) if self._initialized else 0,
            "config": self._config.copy() if self._initialized else {}
        } 
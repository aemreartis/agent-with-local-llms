"""Unit tests for Agent State Manager.

Tests the agent state management functionality including state transitions,
history management, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from typing import Dict, Any

from src.interfaces.agent_interface import (
    AgentExecutionState, AgentContext, AgentState, AgentStateManagerInterface
)
from src.agents.agent_state_manager import AgentStateManager


pytestmark = pytest.mark.asyncio


class TestAgentStateManager:
    """Test agent state manager implementation."""
    
    async def test_agent_state_manager_initialization(self):
        """Test agent state manager initialization."""
        state_manager = AgentStateManager()
        config = {"max_history_size": 100, "session_ttl": 3600}
        
        await state_manager.initialize(config)
        
        assert state_manager._initialized is True
        assert state_manager._config == config
        assert state_manager._states == {}
        assert state_manager._histories == {}
    
    async def test_agent_state_manager_create_state(self):
        """Test creating a new agent state."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        state = await state_manager.create_state("test_session", context)
        
        assert isinstance(state, AgentState)
        assert state.state == AgentExecutionState.IDLE
        assert state.context == context
        assert state.data == {}
        assert state.history == []
        assert state.current_step is None
        assert state.error is None
        assert "test_session" in state_manager._states
    
    async def test_agent_state_manager_get_state(self):
        """Test retrieving an agent state."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        created_state = await state_manager.create_state("test_session", context)
        retrieved_state = await state_manager.get_state("test_session")
        
        assert retrieved_state == created_state
        assert retrieved_state.context == context
    
    async def test_agent_state_manager_get_nonexistent_state(self):
        """Test retrieving a non-existent state returns None."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        state = await state_manager.get_state("nonexistent_session")
        assert state is None
    
    async def test_agent_state_manager_update_state(self):
        """Test updating an agent state."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        state = await state_manager.create_state("test_session", context)
        
        # Update the state
        state.state = AgentExecutionState.RUNNING
        state.data = {"key": "value"}
        success = await state_manager.update_state("test_session", state)
        
        assert success is True
        
        # Verify the update
        updated_state = await state_manager.get_state("test_session")
        assert updated_state.state == AgentExecutionState.RUNNING
        assert updated_state.data == {"key": "value"}
    
    async def test_agent_state_manager_update_nonexistent_state(self):
        """Test updating a non-existent state returns False."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        state = AgentState()
        success = await state_manager.update_state("nonexistent_session", state)
        assert success is False
    
    async def test_agent_state_manager_transition_state(self):
        """Test transitioning agent state."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        # Transition to running state
        success = await state_manager.transition_state(
            "test_session", 
            AgentExecutionState.RUNNING,
            {"step": "processing"}
        )
        
        assert success is True
        
        state = await state_manager.get_state("test_session")
        assert state.state == AgentExecutionState.RUNNING
        assert state.data == {"step": "processing"}
    
    async def test_agent_state_manager_transition_nonexistent_state(self):
        """Test transitioning non-existent state returns False."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        success = await state_manager.transition_state(
            "nonexistent_session",
            AgentExecutionState.RUNNING
        )
        assert success is False
    
    async def test_agent_state_manager_add_to_history(self):
        """Test adding entry to agent history."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        entry = {"action": "search", "timestamp": datetime.now().isoformat()}
        success = await state_manager.add_to_history("test_session", entry)
        
        assert success is True
        
        history = await state_manager.get_history("test_session")
        assert len(history) == 1
        assert history[0] == entry
    
    async def test_agent_state_manager_add_to_history_nonexistent_session(self):
        """Test adding to history for non-existent session returns False."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        entry = {"action": "search"}
        success = await state_manager.add_to_history("nonexistent_session", entry)
        assert success is False
    
    async def test_agent_state_manager_get_history(self):
        """Test retrieving agent history."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        entries = [
            {"action": "search", "timestamp": "2024-01-01T10:00:00"},
            {"action": "process", "timestamp": "2024-01-01T10:01:00"}
        ]
        
        for entry in entries:
            await state_manager.add_to_history("test_session", entry)
        
        history = await state_manager.get_history("test_session")
        assert len(history) == 2
        assert history == entries
    
    async def test_agent_state_manager_get_history_nonexistent_session(self):
        """Test getting history for non-existent session returns empty list."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        history = await state_manager.get_history("nonexistent_session")
        assert history == []
    
    async def test_agent_state_manager_clear_history(self):
        """Test clearing agent history."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        # Add some history
        await state_manager.add_to_history("test_session", {"action": "search"})
        await state_manager.add_to_history("test_session", {"action": "process"})
        
        # Clear history
        success = await state_manager.clear_history("test_session")
        assert success is True
        
        history = await state_manager.get_history("test_session")
        assert history == []
    
    async def test_agent_state_manager_clear_history_nonexistent_session(self):
        """Test clearing history for non-existent session returns False."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        success = await state_manager.clear_history("nonexistent_session")
        assert success is False
    
    async def test_agent_state_manager_set_error(self):
        """Test setting error state."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        error_message = "Something went wrong"
        success = await state_manager.set_error("test_session", error_message)
        
        assert success is True
        
        state = await state_manager.get_state("test_session")
        assert state.state == AgentExecutionState.FAILED
        assert state.error == error_message
    
    async def test_agent_state_manager_set_error_nonexistent_session(self):
        """Test setting error for non-existent session returns False."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        success = await state_manager.set_error("nonexistent_session", "error")
        assert success is False
    
    async def test_agent_state_manager_clear_error(self):
        """Test clearing error state."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        # Set an error first
        await state_manager.set_error("test_session", "Something went wrong")
        
        # Clear the error
        success = await state_manager.clear_error("test_session")
        assert success is True
        
        state = await state_manager.get_state("test_session")
        assert state.error is None
    
    async def test_agent_state_manager_clear_error_nonexistent_session(self):
        """Test clearing error for non-existent session returns False."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        success = await state_manager.clear_error("nonexistent_session")
        assert success is False
    
    async def test_agent_state_manager_delete_state(self):
        """Test deleting agent state."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        # Verify state exists
        state = await state_manager.get_state("test_session")
        assert state is not None
        
        # Delete the state
        success = await state_manager.delete_state("test_session")
        assert success is True
        
        # Verify state is deleted
        state = await state_manager.get_state("test_session")
        assert state is None
    
    async def test_agent_state_manager_delete_nonexistent_state(self):
        """Test deleting non-existent state returns False."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        success = await state_manager.delete_state("nonexistent_session")
        assert success is False
    
    async def test_agent_state_manager_list_sessions(self):
        """Test listing all active sessions."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        # Create multiple sessions
        context1 = AgentContext(session_id="session1")
        context2 = AgentContext(session_id="session2")
        context3 = AgentContext(session_id="session3")
        
        await state_manager.create_state("session1", context1)
        await state_manager.create_state("session2", context2)
        await state_manager.create_state("session3", context3)
        
        sessions = await state_manager.list_sessions()
        assert len(sessions) == 3
        assert "session1" in sessions
        assert "session2" in sessions
        assert "session3" in sessions
    
    async def test_agent_state_manager_list_sessions_empty(self):
        """Test listing sessions when none exist returns empty list."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        sessions = await state_manager.list_sessions()
        assert sessions == []
    
    async def test_agent_state_manager_health_check(self):
        """Test health check functionality."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        health = await state_manager.health_check()
        assert health is True
    
    async def test_agent_state_manager_health_check_not_initialized(self):
        """Test health check when not initialized returns False."""
        state_manager = AgentStateManager()
        
        health = await state_manager.health_check()
        assert health is False
    
    async def test_agent_state_manager_get_info(self):
        """Test getting state manager information."""
        state_manager = AgentStateManager()
        await state_manager.initialize({"max_history_size": 100})
        
        info = state_manager.get_state_manager_info()
        
        assert "type" in info
        assert info["type"] == "AgentStateManager"
        assert "initialized" in info
        assert info["initialized"] is True
        assert "active_sessions" in info
        assert info["active_sessions"] == 0
        assert "config" in info
        assert info["config"]["max_history_size"] == 100
    
    async def test_agent_state_manager_get_info_not_initialized(self):
        """Test getting info when not initialized."""
        state_manager = AgentStateManager()
        
        info = state_manager.get_state_manager_info()
        
        assert "type" in info
        assert info["type"] == "AgentStateManager"
        assert "initialized" in info
        assert info["initialized"] is False
        assert "active_sessions" in info
        assert info["active_sessions"] == 0
    
    async def test_agent_state_manager_max_history_size_limit(self):
        """Test that history respects max size limit."""
        state_manager = AgentStateManager()
        await state_manager.initialize({"max_history_size": 2})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        # Add more entries than the limit
        for i in range(5):
            await state_manager.add_to_history("test_session", {"entry": i})
        
        history = await state_manager.get_history("test_session")
        assert len(history) == 2  # Should be limited to max_history_size
        assert history[0]["entry"] == 3  # Should keep the latest entries
        assert history[1]["entry"] == 4
    
    async def test_agent_state_manager_state_transition_validation(self):
        """Test that state transitions are properly validated."""
        state_manager = AgentStateManager()
        await state_manager.initialize({})
        
        context = AgentContext(session_id="test_session")
        await state_manager.create_state("test_session", context)
        
        # Test valid transitions
        valid_transitions = [
            (AgentExecutionState.IDLE, AgentExecutionState.RUNNING),
            (AgentExecutionState.RUNNING, AgentExecutionState.WAITING),
            (AgentExecutionState.WAITING, AgentExecutionState.RUNNING),
            (AgentExecutionState.RUNNING, AgentExecutionState.COMPLETED),
            (AgentExecutionState.RUNNING, AgentExecutionState.FAILED),
            (AgentExecutionState.RUNNING, AgentExecutionState.PAUSED),
            (AgentExecutionState.PAUSED, AgentExecutionState.RUNNING),
        ]
        
        for from_state, to_state in valid_transitions:
            # Set initial state
            await state_manager.transition_state("test_session", from_state)
            
            # Transition to new state
            success = await state_manager.transition_state("test_session", to_state)
            assert success is True
            
            current_state = await state_manager.get_state("test_session")
            assert current_state.state == to_state 
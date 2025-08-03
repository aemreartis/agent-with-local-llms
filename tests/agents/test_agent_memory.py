"""Unit tests for Agent Memory.

Tests the agent memory functionality including state and context storage,
retrieval, and session management.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.agents.agent_memory import AgentMemory
from src.interfaces.agent_interface import (
    AgentState, AgentContext, AgentExecutionState
)


pytestmark = pytest.mark.asyncio


class TestAgentMemory:
    """Test suite for Agent Memory implementation."""
    
    @pytest.fixture
    def agent_memory(self):
        """Create an agent memory instance."""
        return AgentMemory()
    
    @pytest.fixture
    def sample_state(self):
        """Create a sample agent state."""
        return AgentState(
            state=AgentExecutionState.RUNNING,
            data={"key": "value"},
            current_step="test_step"
        )
    
    @pytest.fixture
    def sample_context(self):
        """Create a sample agent context."""
        return AgentContext(
            session_id="test_session",
            user_id="user123",
            conversation_id="conv456",
            metadata={"key": "value"}
        )
    
    async def test_agent_memory_initialization(self, agent_memory):
        """Test agent memory initialization."""
        config = {
            "max_sessions": 500,
            "session_ttl": 1800,
            "cleanup_interval": 600,
            "storage_backend": "memory"
        }
        
        await agent_memory.initialize(config)
        
        info = agent_memory.get_memory_info()
        assert info["initialized"] is True
        assert info["total_sessions"] == 0
        assert info["config"]["max_sessions"] == 500
        assert info["config"]["session_ttl"] == 1800
        assert info["config"]["cleanup_interval"] == 600
        assert info["config"]["storage_backend"] == "memory"
    
    async def test_agent_memory_initialization_with_defaults(self, agent_memory):
        """Test agent memory initialization with default values."""
        await agent_memory.initialize({})
        
        info = agent_memory.get_memory_info()
        assert info["initialized"] is True
        assert info["config"]["max_sessions"] == 1000
        assert info["config"]["session_ttl"] == 3600
        assert info["config"]["cleanup_interval"] == 300
        assert info["config"]["storage_backend"] == "memory"
    
    async def test_agent_memory_store_state_success(self, agent_memory, sample_state):
        """Test successful state storage."""
        await agent_memory.initialize({})
        
        result = await agent_memory.store_state("test_session", sample_state)
        
        assert result is True
        
        # Verify state was stored
        stored_state = await agent_memory.retrieve_state("test_session")
        assert stored_state is not None
        assert stored_state.state == AgentExecutionState.RUNNING
        assert stored_state.data == {"key": "value"}
        assert stored_state.current_step == "test_step"
    
    async def test_agent_memory_store_state_not_initialized(self, agent_memory, sample_state):
        """Test state storage when memory is not initialized."""
        result = await agent_memory.store_state("test_session", sample_state)
        
        assert result is False
    
    async def test_agent_memory_store_invalid_state(self, agent_memory):
        """Test storing invalid state type."""
        await agent_memory.initialize({})
        
        invalid_state = {"invalid": "state"}
        result = await agent_memory.store_state("test_session", invalid_state)
        
        assert result is False
    
    async def test_agent_memory_retrieve_state_success(self, agent_memory, sample_state):
        """Test successful state retrieval."""
        await agent_memory.initialize({})
        await agent_memory.store_state("test_session", sample_state)
        
        retrieved_state = await agent_memory.retrieve_state("test_session")
        
        assert retrieved_state is not None
        assert retrieved_state.state == sample_state.state
        assert retrieved_state.data == sample_state.data
        assert retrieved_state.current_step == sample_state.current_step
    
    async def test_agent_memory_retrieve_nonexistent_state(self, agent_memory):
        """Test retrieving non-existent state."""
        await agent_memory.initialize({})
        
        retrieved_state = await agent_memory.retrieve_state("nonexistent_session")
        
        assert retrieved_state is None
    
    async def test_agent_memory_retrieve_state_not_initialized(self, agent_memory):
        """Test state retrieval when memory is not initialized."""
        retrieved_state = await agent_memory.retrieve_state("test_session")
        
        assert retrieved_state is None
    
    async def test_agent_memory_store_context_success(self, agent_memory, sample_context):
        """Test successful context storage."""
        await agent_memory.initialize({})
        
        result = await agent_memory.store_context("test_session", sample_context)
        
        assert result is True
        
        # Verify context was stored
        stored_context = await agent_memory.retrieve_context("test_session")
        assert stored_context is not None
        assert stored_context.session_id == "test_session"
        assert stored_context.user_id == "user123"
        assert stored_context.conversation_id == "conv456"
        assert stored_context.metadata == {"key": "value"}
    
    async def test_agent_memory_store_context_not_initialized(self, agent_memory, sample_context):
        """Test context storage when memory is not initialized."""
        result = await agent_memory.store_context("test_session", sample_context)
        
        assert result is False
    
    async def test_agent_memory_store_invalid_context(self, agent_memory):
        """Test storing invalid context type."""
        await agent_memory.initialize({})
        
        invalid_context = {"invalid": "context"}
        result = await agent_memory.store_context("test_session", invalid_context)
        
        assert result is False
    
    async def test_agent_memory_retrieve_context_success(self, agent_memory, sample_context):
        """Test successful context retrieval."""
        await agent_memory.initialize({})
        await agent_memory.store_context("test_session", sample_context)
        
        retrieved_context = await agent_memory.retrieve_context("test_session")
        
        assert retrieved_context is not None
        assert retrieved_context.session_id == sample_context.session_id
        assert retrieved_context.user_id == sample_context.user_id
        assert retrieved_context.conversation_id == sample_context.conversation_id
        assert retrieved_context.metadata == sample_context.metadata
    
    async def test_agent_memory_retrieve_nonexistent_context(self, agent_memory):
        """Test retrieving non-existent context."""
        await agent_memory.initialize({})
        
        retrieved_context = await agent_memory.retrieve_context("nonexistent_session")
        
        assert retrieved_context is None
    
    async def test_agent_memory_retrieve_context_not_initialized(self, agent_memory):
        """Test context retrieval when memory is not initialized."""
        retrieved_context = await agent_memory.retrieve_context("test_session")
        
        assert retrieved_context is None
    
    async def test_agent_memory_clear_session_success(self, agent_memory, sample_state, sample_context):
        """Test successful session clearing."""
        await agent_memory.initialize({})
        await agent_memory.store_state("test_session", sample_state)
        await agent_memory.store_context("test_session", sample_context)
        
        result = await agent_memory.clear_session("test_session")
        
        assert result is True
        
        # Verify session was cleared
        assert await agent_memory.retrieve_state("test_session") is None
        assert await agent_memory.retrieve_context("test_session") is None
    
    async def test_agent_memory_clear_nonexistent_session(self, agent_memory):
        """Test clearing non-existent session."""
        await agent_memory.initialize({})
        
        result = await agent_memory.clear_session("nonexistent_session")
        
        assert result is False
    
    async def test_agent_memory_clear_session_not_initialized(self, agent_memory):
        """Test session clearing when memory is not initialized."""
        result = await agent_memory.clear_session("test_session")
        
        assert result is False
    
    async def test_agent_memory_health_check_success(self, agent_memory):
        """Test successful health check."""
        await agent_memory.initialize({})
        
        health_status = await agent_memory.health_check()
        
        assert health_status is True
    
    async def test_agent_memory_health_check_not_initialized(self, agent_memory):
        """Test health check when memory is not initialized."""
        health_status = await agent_memory.health_check()
        
        assert health_status is False
    
    async def test_agent_memory_get_memory_info(self, agent_memory, sample_state, sample_context):
        """Test getting memory information."""
        await agent_memory.initialize({"max_sessions": 500})
        await agent_memory.store_state("session1", sample_state)
        await agent_memory.store_context("session2", sample_context)
        
        info = agent_memory.get_memory_info()
        
        assert info["name"] == "agent_memory"
        assert info["type"] == "agent_memory"
        assert info["version"] == "1.0.0"
        assert info["initialized"] is True
        assert info["total_sessions"] == 2
        assert info["sessions_with_state"] == 1
        assert info["sessions_with_context"] == 1
        assert info["config"]["max_sessions"] == 500
    
    async def test_agent_memory_list_sessions(self, agent_memory, sample_state, sample_context):
        """Test listing active sessions."""
        await agent_memory.initialize({})
        
        # Initially empty
        sessions = await agent_memory.list_sessions()
        assert sessions == []
        
        # After storing data
        await agent_memory.store_state("session1", sample_state)
        await agent_memory.store_context("session2", sample_context)
        
        sessions = await agent_memory.list_sessions()
        assert len(sessions) == 2
        assert "session1" in sessions
        assert "session2" in sessions
    
    async def test_agent_memory_get_session_info(self, agent_memory, sample_state, sample_context):
        """Test getting session information."""
        await agent_memory.initialize({})
        await agent_memory.store_state("test_session", sample_state)
        await agent_memory.store_context("test_session", sample_context)
        
        session_info = await agent_memory.get_session_info("test_session")
        
        assert session_info is not None
        assert session_info["session_id"] == "test_session"
        assert session_info["has_state"] is True
        assert session_info["has_context"] is True
        assert session_info["expired"] is False
        assert "last_updated" in session_info
        assert "state_size" in session_info
    
    async def test_agent_memory_get_nonexistent_session_info(self, agent_memory):
        """Test getting information for non-existent session."""
        await agent_memory.initialize({})
        
        session_info = await agent_memory.get_session_info("nonexistent_session")
        
        assert session_info is None
    
    async def test_agent_memory_session_expiration(self, agent_memory, sample_state):
        """Test session expiration functionality."""
        # Initialize with short TTL
        await agent_memory.initialize({"session_ttl": 1})  # 1 second TTL
        
        # Store state
        await agent_memory.store_state("test_session", sample_state)
        
        # Verify state exists
        assert await agent_memory.retrieve_state("test_session") is not None
        
        # Wait for expiration (simulate by manipulating metadata)
        # In a real scenario, this would happen naturally over time
        # For testing, we'll manually trigger the expiration check
        agent_memory._session_metadata["test_session"]["last_updated"] = datetime.now() - timedelta(seconds=2)
        
        # Verify state is expired and removed
        assert await agent_memory.retrieve_state("test_session") is None
    
    async def test_agent_memory_multiple_sessions(self, agent_memory, sample_state, sample_context):
        """Test managing multiple sessions."""
        await agent_memory.initialize({})
        
        # Store multiple sessions
        await agent_memory.store_state("session1", sample_state)
        await agent_memory.store_context("session2", sample_context)
        await agent_memory.store_state("session3", sample_state)
        await agent_memory.store_context("session3", sample_context)
        
        # Verify all sessions exist
        sessions = await agent_memory.list_sessions()
        assert len(sessions) == 3
        assert "session1" in sessions
        assert "session2" in sessions
        assert "session3" in sessions
        
        # Verify memory info
        info = agent_memory.get_memory_info()
        assert info["total_sessions"] == 3
        assert info["sessions_with_state"] == 2
        assert info["sessions_with_context"] == 2
        
        # Clear one session
        await agent_memory.clear_session("session2")
        
        sessions = await agent_memory.list_sessions()
        assert len(sessions) == 2
        assert "session1" in sessions
        assert "session3" in sessions
        assert "session2" not in sessions
    
    async def test_agent_memory_state_and_context_separation(self, agent_memory, sample_state, sample_context):
        """Test that state and context are stored separately."""
        await agent_memory.initialize({})
        
        # Store only state
        await agent_memory.store_state("test_session", sample_state)
        
        # Verify state exists but context doesn't
        assert await agent_memory.retrieve_state("test_session") is not None
        assert await agent_memory.retrieve_context("test_session") is None
        
        # Store only context
        await agent_memory.clear_session("test_session")
        await agent_memory.store_context("test_session", sample_context)
        
        # Verify context exists but state doesn't
        assert await agent_memory.retrieve_state("test_session") is None
        assert await agent_memory.retrieve_context("test_session") is not None
    
    async def test_agent_memory_timestamp_updates(self, agent_memory, sample_state, sample_context):
        """Test that timestamps are updated on storage."""
        await agent_memory.initialize({})
        
        # Store state and context
        await agent_memory.store_state("test_session", sample_state)
        await agent_memory.store_context("test_session", sample_context)
        
        # Get session info
        session_info = await agent_memory.get_session_info("test_session")
        assert session_info is not None
        
        # Verify timestamps are recent
        last_updated = session_info["last_updated"]
        assert isinstance(last_updated, datetime)
        assert datetime.now() - last_updated < timedelta(seconds=1)
    
    async def test_agent_memory_storage_backend_initialization(self, agent_memory):
        """Test storage backend initialization."""
        # Test with unsupported backend
        config = {"storage_backend": "unsupported_backend"}
        await agent_memory.initialize(config)
        
        info = agent_memory.get_memory_info()
        assert info["config"]["storage_backend"] == "memory"  # Should fallback to memory
        
        # Test with supported backend
        config = {"storage_backend": "redis"}
        await agent_memory.initialize(config)
        
        info = agent_memory.get_memory_info()
        assert info["config"]["storage_backend"] == "redis" 
"""Unit tests for Agent Orchestrator.

Tests high-level agent coordination and session management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, ANY
from datetime import datetime
from typing import Dict, Any, Optional

from src.interfaces.agent_interface import (
    AgentOrchestratorInterface,
    AgentState,
    AgentContext,
    AgentExecutionState,
    WorkflowDefinition,
    WorkflowStep,
    AgentNodeInterface
)
from src.agents.agent_orchestrator import AgentOrchestrator


pytestmark = pytest.mark.asyncio


class TestAgentOrchestrator:
    """Test agent orchestrator implementation."""
    
    async def test_agent_orchestrator_initialization(self):
        """Test agent orchestrator initialization."""
        orchestrator = AgentOrchestrator()
        config = {
            "max_sessions": 10,
            "session_timeout": 3600,
            "default_workflow": "rag_workflow",
            "enable_parallel_execution": True,
            "session_cleanup_interval": 300
        }
        
        await orchestrator.initialize(config)
        
        assert orchestrator._initialized is True
        assert orchestrator._config == config
        assert orchestrator._max_sessions == 10
        assert orchestrator._session_timeout == 3600
        assert orchestrator._default_workflow == "rag_workflow"
        assert orchestrator._enable_parallel_execution is True
    
    async def test_agent_orchestrator_initialization_with_defaults(self):
        """Test agent orchestrator initialization with default values."""
        orchestrator = AgentOrchestrator()
        config = {}
        
        await orchestrator.initialize(config)
        
        assert orchestrator._initialized is True
        assert orchestrator._config == config
        assert orchestrator._max_sessions == 5
        assert orchestrator._session_timeout == 1800
        assert orchestrator._default_workflow == "default_workflow"
        assert orchestrator._enable_parallel_execution is False
    
    async def test_create_session_success(self):
        """Test successful session creation."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        context = AgentContext(
            session_id="test_session",
            user_id="user123",
            metadata={"source": "test"}
        )
        
        session_id = await orchestrator.create_session(context)
        
        assert session_id == "test_session"
        assert session_id in orchestrator._sessions
        assert orchestrator._sessions[session_id].context == context
        assert orchestrator._sessions[session_id].state == AgentExecutionState.IDLE
    
    async def test_create_session_max_sessions_reached(self):
        """Test session creation when max sessions reached."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({"max_sessions": 1})
        
        # Create first session
        context1 = AgentContext(session_id="session1", user_id="user1")
        await orchestrator.create_session(context1)
        
        # Try to create second session
        context2 = AgentContext(session_id="session2", user_id="user2")
        
        with pytest.raises(RuntimeError, match="Maximum sessions reached"):
            await orchestrator.create_session(context2)
    
    async def test_create_session_duplicate_session_id(self):
        """Test session creation with duplicate session ID."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        context = AgentContext(session_id="test_session", user_id="user123")
        
        # Create first session
        await orchestrator.create_session(context)
        
        # Try to create duplicate session
        with pytest.raises(ValueError, match="Session already exists"):
            await orchestrator.create_session(context)
    
    async def test_execute_workflow_success(self):
        """Test successful workflow execution."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Mock workflow orchestrator
        mock_workflow_orchestrator = AsyncMock()
        mock_workflow_orchestrator.execute_workflow.return_value = AgentState(
            state=AgentExecutionState.COMPLETED,
            context=context,
            data={"result": "success"},
            history=[],
            current_step="complete",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        orchestrator._workflow_orchestrator = mock_workflow_orchestrator
        
        # Execute workflow
        initial_data = {"query": "test query"}
        result = await orchestrator.execute_workflow(session_id, "test_workflow", initial_data)
        
        assert result.state == AgentExecutionState.COMPLETED
        assert result.data["result"] == "success"
        assert mock_workflow_orchestrator.execute_workflow.called
    
    async def test_execute_workflow_session_not_found(self):
        """Test workflow execution with non-existent session."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        with pytest.raises(ValueError, match="Session not found"):
            await orchestrator.execute_workflow("non_existent", "test_workflow", {})
    
    async def test_execute_workflow_session_terminated(self):
        """Test workflow execution on terminated session."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create and terminate session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        await orchestrator.terminate_session(session_id)
        
        with pytest.raises(RuntimeError, match="Session is terminated"):
            await orchestrator.execute_workflow(session_id, "test_workflow", {})
    
    async def test_get_session_state_success(self):
        """Test successful session state retrieval."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Get session state
        state = await orchestrator.get_session_state(session_id)
        
        assert state is not None
        assert state.context.session_id == "test_session"
        assert state.state == AgentExecutionState.IDLE
    
    async def test_get_session_state_not_found(self):
        """Test session state retrieval for non-existent session."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        state = await orchestrator.get_session_state("non_existent")
        assert state is None
    
    async def test_pause_session_success(self):
        """Test successful session pause."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Pause session
        result = await orchestrator.pause_session(session_id)
        
        assert result is True
        assert orchestrator._sessions[session_id].state == AgentExecutionState.PAUSED
    
    async def test_pause_session_not_found(self):
        """Test session pause for non-existent session."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        result = await orchestrator.pause_session("non_existent")
        assert result is False
    
    async def test_pause_session_already_paused(self):
        """Test session pause when already paused."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create and pause session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        await orchestrator.pause_session(session_id)
        
        # Try to pause again
        result = await orchestrator.pause_session(session_id)
        assert result is False
    
    async def test_resume_session_success(self):
        """Test successful session resume."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create and pause session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        await orchestrator.pause_session(session_id)
        
        # Resume session
        result = await orchestrator.resume_session(session_id)
        
        assert result is True
        assert orchestrator._sessions[session_id].state == AgentExecutionState.IDLE
    
    async def test_resume_session_not_found(self):
        """Test session resume for non-existent session."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        result = await orchestrator.resume_session("non_existent")
        assert result is False
    
    async def test_resume_session_not_paused(self):
        """Test session resume when not paused."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session (not paused)
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Try to resume
        result = await orchestrator.resume_session(session_id)
        assert result is False
    
    async def test_terminate_session_success(self):
        """Test successful session termination."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Terminate session
        result = await orchestrator.terminate_session(session_id)
        
        assert result is True
        assert orchestrator._sessions[session_id].state == AgentExecutionState.TERMINATED
    
    async def test_terminate_session_not_found(self):
        """Test session termination for non-existent session."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        result = await orchestrator.terminate_session("non_existent")
        assert result is False
    
    async def test_terminate_session_already_terminated(self):
        """Test session termination when already terminated."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create and terminate session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        await orchestrator.terminate_session(session_id)
        
        # Try to terminate again
        result = await orchestrator.terminate_session(session_id)
        assert result is False
    
    async def test_health_check_success(self):
        """Test successful health check."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        result = await orchestrator.health_check()
        assert result is True
    
    async def test_health_check_not_initialized(self):
        """Test health check when not initialized."""
        orchestrator = AgentOrchestrator()
        
        result = await orchestrator.health_check()
        assert result is False
    
    async def test_get_orchestrator_info(self):
        """Test orchestrator information retrieval."""
        orchestrator = AgentOrchestrator()
        config = {
            "max_sessions": 10,
            "session_timeout": 3600,
            "default_workflow": "rag_workflow"
        }
        await orchestrator.initialize(config)
        
        # Create a session
        context = AgentContext(session_id="test_session", user_id="user123")
        await orchestrator.create_session(context)
        
        info = orchestrator.get_orchestrator_info()
        
        assert info["type"] == "AgentOrchestrator"
        assert info["initialized"] is True
        assert info["max_sessions"] == 10
        assert info["active_sessions"] == 1
        assert info["session_timeout"] == 3600
        assert info["default_workflow"] == "rag_workflow"
        assert "sessions" in info
    
    async def test_session_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({"session_timeout": 1})  # 1 second timeout
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Wait for session to expire
        import asyncio
        await asyncio.sleep(1.1)
        
        # Run cleanup
        await orchestrator._cleanup_expired_sessions()
        
        # Session should be removed
        assert session_id not in orchestrator._sessions
    
    async def test_session_cleanup_active_sessions_preserved(self):
        """Test that active sessions are preserved during cleanup."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({"session_timeout": 10})  # 10 second timeout
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Run cleanup immediately (session should not be expired)
        await orchestrator._cleanup_expired_sessions()
        
        # Session should still exist
        assert session_id in orchestrator._sessions
    
    async def test_execute_workflow_with_default_workflow(self):
        """Test workflow execution using default workflow."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({"default_workflow": "default_workflow"})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Mock workflow orchestrator
        mock_workflow_orchestrator = AsyncMock()
        mock_workflow_orchestrator.execute_workflow.return_value = AgentState(
            state=AgentExecutionState.COMPLETED,
            context=context,
            data={"result": "success"},
            history=[],
            current_step="complete",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        orchestrator._workflow_orchestrator = mock_workflow_orchestrator
        
        # Execute workflow without specifying workflow name
        initial_data = {"query": "test query"}
        result = await orchestrator.execute_workflow(session_id, None, initial_data)
        
        assert result.state == AgentExecutionState.COMPLETED
        mock_workflow_orchestrator.execute_workflow.assert_called_with("default_workflow", ANY)
    
    async def test_execute_workflow_session_state_transition(self):
        """Test session state transition during workflow execution."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Mock workflow orchestrator
        mock_workflow_orchestrator = AsyncMock()
        mock_workflow_orchestrator.execute_workflow.return_value = AgentState(
            state=AgentExecutionState.COMPLETED,
            context=context,
            data={"result": "success"},
            history=[],
            current_step="complete",
            error=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        orchestrator._workflow_orchestrator = mock_workflow_orchestrator
        
        # Execute workflow
        initial_data = {"query": "test query"}
        result = await orchestrator.execute_workflow(session_id, "test_workflow", initial_data)
        
        # Session should be updated with result
        session_state = await orchestrator.get_session_state(session_id)
        assert session_state.data["result"] == "success"
        assert session_state.state == AgentExecutionState.COMPLETED
    
    async def test_execute_workflow_error_handling(self):
        """Test workflow execution error handling."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        # Mock workflow orchestrator to raise exception
        mock_workflow_orchestrator = AsyncMock()
        mock_workflow_orchestrator.execute_workflow.side_effect = RuntimeError("Workflow failed")
        orchestrator._workflow_orchestrator = mock_workflow_orchestrator
        
        # Execute workflow
        initial_data = {"query": "test query"}
        result = await orchestrator.execute_workflow(session_id, "test_workflow", initial_data)
        
        # Should handle error gracefully
        assert result.state == AgentExecutionState.FAILED
        assert "Workflow failed" in result.error
    
    async def test_list_sessions(self):
        """Test listing all sessions."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create multiple sessions
        context1 = AgentContext(session_id="session1", user_id="user1")
        context2 = AgentContext(session_id="session2", user_id="user2")
        
        await orchestrator.create_session(context1)
        await orchestrator.create_session(context2)
        
        sessions = orchestrator.list_sessions()
        
        assert len(sessions) == 2
        assert "session1" in sessions
        assert "session2" in sessions
    
    async def test_get_session_info(self):
        """Test getting detailed session information."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        # Create session
        context = AgentContext(session_id="test_session", user_id="user123")
        session_id = await orchestrator.create_session(context)
        
        info = orchestrator.get_session_info(session_id)
        
        assert info["session_id"] == "test_session"
        assert info["user_id"] == "user123"
        assert info["state"] == AgentExecutionState.IDLE.value
        assert "created_at" in info
        assert "updated_at" in info
    
    async def test_get_session_info_not_found(self):
        """Test getting session info for non-existent session."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize({})
        
        info = orchestrator.get_session_info("non_existent")
        assert info is None 
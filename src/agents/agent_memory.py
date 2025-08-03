"""Agent Memory - Memory management for agent states and contexts.

This module provides the implementation of agent memory that manages
agent state and context storage, retrieval, and lifecycle management.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.interfaces.agent_interface import (
    AgentMemoryInterface, AgentState, AgentContext
)

logger = logging.getLogger(__name__)


class AgentMemory(AgentMemoryInterface):
    """Memory management for agent states and contexts.
    
    Provides persistent storage and retrieval of agent states and contexts
    with support for session management and cleanup.
    """
    
    def __init__(self):
        """Initialize the agent memory."""
        self._states: Dict[str, AgentState] = {}
        self._contexts: Dict[str, AgentContext] = {}
        self._session_metadata: Dict[str, Dict[str, Any]] = {}
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent memory with configuration.
        
        Args:
            config: Configuration dictionary containing:
                - max_sessions: Maximum number of sessions to store (optional, default 1000)
                - session_ttl: Time-to-live for sessions in seconds (optional, default 3600)
                - cleanup_interval: Interval for cleanup in seconds (optional, default 300)
                - storage_backend: Storage backend type (optional, default "memory")
        """
        try:
            logger.info("Initializing agent memory")
            
            self._config = config.copy()
            self._config.setdefault("max_sessions", 1000)
            self._config.setdefault("session_ttl", 3600)  # 1 hour
            self._config.setdefault("cleanup_interval", 300)  # 5 minutes
            self._config.setdefault("storage_backend", "memory")
            
            # Initialize storage backend if specified
            if self._config["storage_backend"] != "memory":
                await self._initialize_storage_backend()
            
            self._initialized = True
            logger.info(f"Agent memory initialized with backend: {self._config['storage_backend']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent memory: {str(e)}")
            raise
    
    async def store_state(self, session_id: str, state: AgentState) -> bool:
        """Store agent state in memory.
        
        Args:
            session_id: Unique session identifier
            state: Agent state to store
            
        Returns:
            True if state was stored successfully, False otherwise
        """
        try:
            if not self._initialized:
                logger.error("Agent memory not initialized")
                return False
            
            if not isinstance(state, AgentState):
                logger.error(f"Invalid state type for session {session_id}")
                return False
            
            # Update state timestamp
            state.updated_at = datetime.now()
            
            # Store state
            self._states[session_id] = state
            
            # Update session metadata
            self._session_metadata[session_id] = {
                "last_updated": datetime.now(),
                "state_size": len(str(state)),
                "has_context": session_id in self._contexts
            }
            
            # Check if we need to cleanup old sessions
            await self._cleanup_old_sessions()
            
            logger.debug(f"Stored state for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store state for session {session_id}: {str(e)}")
            return False
    
    async def retrieve_state(self, session_id: str) -> Optional[AgentState]:
        """Retrieve agent state from memory.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Agent state if found, None otherwise
        """
        try:
            if not self._initialized:
                logger.error("Agent memory not initialized")
                return None
            
            state = self._states.get(session_id)
            if not state:
                logger.debug(f"State not found for session: {session_id}")
                return None
            
            # Check if session has expired
            if await self._is_session_expired(session_id):
                logger.info(f"Session {session_id} has expired, removing")
                await self.clear_session(session_id)
                return None
            
            logger.debug(f"Retrieved state for session: {session_id}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to retrieve state for session {session_id}: {str(e)}")
            return None
    
    async def store_context(self, session_id: str, context: AgentContext) -> bool:
        """Store agent context in memory.
        
        Args:
            session_id: Unique session identifier
            context: Agent context to store
            
        Returns:
            True if context was stored successfully, False otherwise
        """
        try:
            if not self._initialized:
                logger.error("Agent memory not initialized")
                return False
            
            if not isinstance(context, AgentContext):
                logger.error(f"Invalid context type for session {session_id}")
                return False
            
            # Update context timestamp
            context.updated_at = datetime.now()
            
            # Store context
            self._contexts[session_id] = context
            
            # Update session metadata
            if session_id in self._session_metadata:
                self._session_metadata[session_id]["has_context"] = True
            else:
                self._session_metadata[session_id] = {
                    "last_updated": datetime.now(),
                    "state_size": 0,
                    "has_context": True
                }
            
            logger.debug(f"Stored context for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store context for session {session_id}: {str(e)}")
            return False
    
    async def retrieve_context(self, session_id: str) -> Optional[AgentContext]:
        """Retrieve agent context from memory.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Agent context if found, None otherwise
        """
        try:
            if not self._initialized:
                logger.error("Agent memory not initialized")
                return None
            
            context = self._contexts.get(session_id)
            if not context:
                logger.debug(f"Context not found for session: {session_id}")
                return None
            
            # Check if session has expired
            if await self._is_session_expired(session_id):
                logger.info(f"Session {session_id} has expired, removing")
                await self.clear_session(session_id)
                return None
            
            logger.debug(f"Retrieved context for session: {session_id}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to retrieve context for session {session_id}: {str(e)}")
            return None
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear all data for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session was cleared successfully, False otherwise
        """
        try:
            if not self._initialized:
                logger.error("Agent memory not initialized")
                return False
            
            # Remove state and context
            state_removed = session_id in self._states
            context_removed = session_id in self._contexts
            metadata_removed = session_id in self._session_metadata
            
            if state_removed:
                del self._states[session_id]
            if context_removed:
                del self._contexts[session_id]
            if metadata_removed:
                del self._session_metadata[session_id]
            
            if state_removed or context_removed or metadata_removed:
                logger.info(f"Cleared session: {session_id}")
                return True
            else:
                logger.debug(f"Session not found: {session_id}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to clear session {session_id}: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """Check if the agent memory is healthy.
        
        Returns:
            True if memory is healthy, False otherwise
        """
        try:
            if not self._initialized:
                return False
            
            # Check if we can perform basic operations
            test_session_id = "_health_check_test"
            test_state = AgentState()
            test_context = AgentContext(session_id=test_session_id)
            
            # Test state operations
            state_stored = await self.store_state(test_session_id, test_state)
            state_retrieved = await self.retrieve_state(test_session_id)
            state_cleared = await self.clear_session(test_session_id)
            
            # Test context operations
            context_stored = await self.store_context(test_session_id, test_context)
            context_retrieved = await self.retrieve_context(test_session_id)
            context_cleared = await self.clear_session(test_session_id)
            
            return (state_stored and state_retrieved is not None and state_cleared and
                    context_stored and context_retrieved is not None and context_cleared)
            
        except Exception as e:
            logger.error(f"Agent memory health check failed: {str(e)}")
            return False
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get information about the agent memory.
        
        Returns:
            Dictionary containing memory information
        """
        return {
            "name": "agent_memory",
            "type": "agent_memory",
            "version": "1.0.0",
            "description": "Memory management for agent states and contexts",
            "initialized": self._initialized,
            "total_sessions": len(self._session_metadata),
            "sessions_with_state": len(self._states),
            "sessions_with_context": len(self._contexts),
            "config": self._config,
            "metadata": {
                "created_at": min([meta["last_updated"] for meta in self._session_metadata.values()]) if self._session_metadata else None,
                "last_updated": max([meta["last_updated"] for meta in self._session_metadata.values()]) if self._session_metadata else None
            }
        }
    
    async def list_sessions(self) -> List[str]:
        """List all active sessions.
        
        Returns:
            List of active session IDs
        """
        try:
            if not self._initialized:
                return []
            
            # Filter out expired sessions
            active_sessions = []
            for session_id in self._session_metadata.keys():
                if not await self._is_session_expired(session_id):
                    active_sessions.append(session_id)
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {str(e)}")
            return []
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session information dictionary if found, None otherwise
        """
        try:
            if not self._initialized:
                return None
            
            if session_id not in self._session_metadata:
                return None
            
            metadata = self._session_metadata[session_id].copy()
            metadata["session_id"] = session_id
            metadata["has_state"] = session_id in self._states
            metadata["has_context"] = session_id in self._contexts
            metadata["expired"] = await self._is_session_expired(session_id)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get session info for {session_id}: {str(e)}")
            return None
    
    async def _initialize_storage_backend(self) -> None:
        """Initialize storage backend if not using memory."""
        try:
            backend_type = self._config["storage_backend"]
            logger.info(f"Initializing storage backend: {backend_type}")
            
            # This would typically involve connecting to external storage
            # For now, we'll just log that this would happen
            if backend_type not in ["memory", "redis", "postgresql"]:
                logger.warning(f"Unsupported storage backend: {backend_type}, using memory")
                self._config["storage_backend"] = "memory"
            
        except Exception as e:
            logger.error(f"Failed to initialize storage backend: {str(e)}")
            raise
    
    async def _is_session_expired(self, session_id: str) -> bool:
        """Check if a session has expired.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session has expired, False otherwise
        """
        try:
            if session_id not in self._session_metadata:
                return True
            
            last_updated = self._session_metadata[session_id]["last_updated"]
            ttl_seconds = self._config["session_ttl"]
            
            return datetime.now() - last_updated > timedelta(seconds=ttl_seconds)
            
        except Exception as e:
            logger.error(f"Failed to check session expiration for {session_id}: {str(e)}")
            return True
    
    async def _cleanup_old_sessions(self) -> None:
        """Clean up expired sessions."""
        try:
            if len(self._session_metadata) <= self._config["max_sessions"]:
                return
            
            # Find expired sessions
            expired_sessions = []
            for session_id in self._session_metadata.keys():
                if await self._is_session_expired(session_id):
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                await self.clear_session(session_id)
            
            # If still over limit, remove oldest sessions
            if len(self._session_metadata) > self._config["max_sessions"]:
                sessions_by_age = sorted(
                    self._session_metadata.items(),
                    key=lambda x: x[1]["last_updated"]
                )
                
                sessions_to_remove = len(self._session_metadata) - self._config["max_sessions"]
                for session_id, _ in sessions_by_age[:sessions_to_remove]:
                    await self.clear_session(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {str(e)}") 
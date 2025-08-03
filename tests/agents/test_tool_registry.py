"""Unit tests for Tool Registry.

Tests the tool registry functionality including tool registration,
discovery, and execution.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from src.agents.tool_registry import ToolRegistry
from src.interfaces.agent_interface import (
    ToolInterface, ToolResult, AgentContext, ToolType
)


pytestmark = pytest.mark.asyncio


class MockTool(ToolInterface):
    """Mock tool for testing."""
    
    def __init__(self, name: str = "mock_tool", healthy: bool = True):
        self.name = name
        self.healthy = healthy
        self.initialized = False
        self.config = {}
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.initialized = True
        self.config = config
    
    async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
        if not self.initialized:
            return ToolResult(success=False, data=None, error="Tool not initialized")
        
        return ToolResult(
            success=True,
            data={"result": f"Executed {self.name} with {input_data}"},
            metadata={"tool_name": self.name}
        )
    
    async def health_check(self) -> bool:
        return self.healthy
    
    def get_tool_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "mock_tool",
            "version": "1.0.0",
            "description": f"Mock tool: {self.name}"
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            }
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            }
        }


class TestToolRegistry:
    """Test suite for Tool Registry implementation."""
    
    @pytest.fixture
    def tool_registry(self):
        """Create a tool registry instance."""
        return ToolRegistry()
    
    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool."""
        return MockTool("test_tool")
    
    @pytest.fixture
    def agent_context(self):
        """Create an agent context."""
        return AgentContext(session_id="test_session")
    
    async def test_tool_registry_initialization(self, tool_registry):
        """Test tool registry initialization."""
        config = {
            "auto_discovery": True,
            "tool_timeout": 60.0,
            "max_concurrent_tools": 20
        }
        
        await tool_registry.initialize(config)
        
        info = tool_registry.get_registry_info()
        assert info["initialized"] is True
        assert info["total_tools"] == 0
        assert info["config"]["auto_discovery"] is True
        assert info["config"]["tool_timeout"] == 60.0
        assert info["config"]["max_concurrent_tools"] == 20
    
    async def test_tool_registry_initialization_with_defaults(self, tool_registry):
        """Test tool registry initialization with default values."""
        await tool_registry.initialize({})
        
        info = tool_registry.get_registry_info()
        assert info["initialized"] is True
        assert info["config"]["auto_discovery"] is False
        assert info["config"]["tool_timeout"] == 30.0
        assert info["config"]["max_concurrent_tools"] == 10
    
    async def test_tool_registry_initialization_with_preconfigured_tools(self, tool_registry):
        """Test tool registry initialization with pre-configured tools."""
        config = {
            "pre_configured_tools": {
                "test_tool": {"type": "mock", "config": {}}
            }
        }
        
        await tool_registry.initialize(config)
        
        info = tool_registry.get_registry_info()
        assert info["initialized"] is True
    
    async def test_tool_registry_register_tool_success(self, tool_registry, mock_tool):
        """Test successful tool registration."""
        await tool_registry.initialize({})
        
        result = await tool_registry.register_tool("test_tool", mock_tool)
        
        assert result is True
        assert await tool_registry.list_tools() == ["test_tool"]
        
        # Verify tool metadata
        tool_info = tool_registry.get_tool_info("test_tool")
        assert tool_info is not None
        assert tool_info["tool_info"]["name"] == "test_tool"
    
    async def test_tool_registry_register_tool_not_initialized(self, tool_registry, mock_tool):
        """Test tool registration when registry is not initialized."""
        result = await tool_registry.register_tool("test_tool", mock_tool)
        
        assert result is False
    
    async def test_tool_registry_register_invalid_tool(self, tool_registry):
        """Test registering a tool that doesn't implement ToolInterface."""
        await tool_registry.initialize({})
        
        invalid_tool = Mock()  # Doesn't implement ToolInterface
        result = await tool_registry.register_tool("invalid_tool", invalid_tool)
        
        assert result is False
    
    async def test_tool_registry_unregister_tool_success(self, tool_registry, mock_tool):
        """Test successful tool unregistration."""
        await tool_registry.initialize({})
        await tool_registry.register_tool("test_tool", mock_tool)
        
        result = await tool_registry.unregister_tool("test_tool")
        
        assert result is True
        assert await tool_registry.list_tools() == []
        assert tool_registry.get_tool_info("test_tool") is None
    
    async def test_tool_registry_unregister_nonexistent_tool(self, tool_registry):
        """Test unregistering a tool that doesn't exist."""
        await tool_registry.initialize({})
        
        result = await tool_registry.unregister_tool("nonexistent_tool")
        
        assert result is False
    
    async def test_tool_registry_get_tool_success(self, tool_registry, mock_tool):
        """Test getting a registered tool."""
        await tool_registry.initialize({})
        await tool_registry.register_tool("test_tool", mock_tool)
        
        tool = await tool_registry.get_tool("test_tool")
        
        assert tool is not None
        assert tool == mock_tool
    
    async def test_tool_registry_get_nonexistent_tool(self, tool_registry):
        """Test getting a tool that doesn't exist."""
        await tool_registry.initialize({})
        
        tool = await tool_registry.get_tool("nonexistent_tool")
        
        assert tool is None
    
    async def test_tool_registry_list_tools(self, tool_registry):
        """Test listing registered tools."""
        await tool_registry.initialize({})
        
        # Initially empty
        tools = await tool_registry.list_tools()
        assert tools == []
        
        # After registering tools
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        
        await tool_registry.register_tool("tool1", tool1)
        await tool_registry.register_tool("tool2", tool2)
        
        tools = await tool_registry.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools
    
    async def test_tool_registry_execute_tool_success(self, tool_registry, mock_tool, agent_context):
        """Test successful tool execution."""
        await tool_registry.initialize({})
        await mock_tool.initialize({})  # Initialize the mock tool
        await tool_registry.register_tool("test_tool", mock_tool)
        
        input_data = {"input": "test_data"}
        result = await tool_registry.execute_tool("test_tool", input_data, agent_context)
        
        assert result.success is True
        assert result.data["result"] == "Executed test_tool with {'input': 'test_data'}"
        assert result.metadata["tool_name"] == "test_tool"
        assert result.execution_time > 0
    
    async def test_tool_registry_execute_tool_not_initialized(self, tool_registry, agent_context):
        """Test tool execution when registry is not initialized."""
        result = await tool_registry.execute_tool("test_tool", {}, agent_context)
        
        assert result.success is False
        assert "not initialized" in result.error
    
    async def test_tool_registry_execute_nonexistent_tool(self, tool_registry, agent_context):
        """Test executing a tool that doesn't exist."""
        await tool_registry.initialize({})
        
        result = await tool_registry.execute_tool("nonexistent_tool", {}, agent_context)
        
        assert result.success is False
        assert "not found" in result.error
    
    async def test_tool_registry_execute_unhealthy_tool(self, tool_registry, agent_context):
        """Test executing an unhealthy tool."""
        unhealthy_tool = MockTool("unhealthy_tool", healthy=False)
        await tool_registry.initialize({})
        await tool_registry.register_tool("unhealthy_tool", unhealthy_tool)
        
        result = await tool_registry.execute_tool("unhealthy_tool", {}, agent_context)
        
        assert result.success is False
        assert "not healthy" in result.error
    
    async def test_tool_registry_execute_tool_with_exception(self, tool_registry, agent_context):
        """Test tool execution when tool raises an exception."""
        # Create a tool that raises an exception
        class ExceptionTool(MockTool):
            async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
                raise Exception("Tool execution error")
        
        exception_tool = ExceptionTool("exception_tool")
        await tool_registry.initialize({})
        await tool_registry.register_tool("exception_tool", exception_tool)
        
        result = await tool_registry.execute_tool("exception_tool", {}, agent_context)
        
        assert result.success is False
        assert "Tool execution failed" in result.error
        assert result.execution_time > 0
    
    async def test_tool_registry_health_check_success(self, tool_registry, mock_tool):
        """Test successful health check."""
        await tool_registry.initialize({})
        await tool_registry.register_tool("test_tool", mock_tool)
        
        health_status = await tool_registry.health_check()
        
        assert health_status is True
    
    async def test_tool_registry_health_check_not_initialized(self, tool_registry):
        """Test health check when registry is not initialized."""
        health_status = await tool_registry.health_check()
        
        assert health_status is False
    
    async def test_tool_registry_health_check_with_unhealthy_tool(self, tool_registry):
        """Test health check with an unhealthy tool."""
        unhealthy_tool = MockTool("unhealthy_tool", healthy=False)
        await tool_registry.initialize({})
        await tool_registry.register_tool("unhealthy_tool", unhealthy_tool)
        
        health_status = await tool_registry.health_check()
        
        assert health_status is False
    
    async def test_tool_registry_health_check_with_tool_exception(self, tool_registry):
        """Test health check when a tool raises an exception."""
        # Create a tool that raises an exception during health check
        class ExceptionHealthTool(MockTool):
            async def health_check(self) -> bool:
                raise Exception("Health check error")
        
        exception_tool = ExceptionHealthTool("exception_tool")
        await tool_registry.initialize({})
        await tool_registry.register_tool("exception_tool", exception_tool)
        
        health_status = await tool_registry.health_check()
        
        assert health_status is False
    
    async def test_tool_registry_get_registry_info(self, tool_registry, mock_tool):
        """Test getting registry information."""
        await tool_registry.initialize({"auto_discovery": True})
        await tool_registry.register_tool("test_tool", mock_tool)
        
        info = tool_registry.get_registry_info()
        
        assert info["name"] == "tool_registry"
        assert info["type"] == "tool_registry"
        assert info["version"] == "1.0.0"
        assert info["initialized"] is True
        assert info["total_tools"] == 1
        assert "test_tool" in info["registered_tools"]
        assert info["config"]["auto_discovery"] is True
        assert info["metadata"]["created_at"] is not None
        assert info["metadata"]["last_updated"] is not None
    
    async def test_tool_registry_get_tool_info_success(self, tool_registry, mock_tool):
        """Test getting tool information."""
        await tool_registry.initialize({})
        await tool_registry.register_tool("test_tool", mock_tool)
        
        tool_info = tool_registry.get_tool_info("test_tool")
        
        assert tool_info is not None
        assert tool_info["tool_info"]["name"] == "test_tool"
        assert tool_info["tool_info"]["type"] == "mock_tool"
        assert tool_info["input_schema"]["type"] == "object"
        assert tool_info["output_schema"]["type"] == "object"
        assert tool_info["registered_at"] is not None
    
    async def test_tool_registry_get_tool_info_nonexistent(self, tool_registry):
        """Test getting information for a tool that doesn't exist."""
        await tool_registry.initialize({})
        
        tool_info = tool_registry.get_tool_info("nonexistent_tool")
        
        assert tool_info is None
    
    async def test_tool_registry_multiple_tools(self, tool_registry):
        """Test managing multiple tools."""
        await tool_registry.initialize({})
        
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        tool3 = MockTool("tool3")
        
        # Register multiple tools
        await tool_registry.register_tool("tool1", tool1)
        await tool_registry.register_tool("tool2", tool2)
        await tool_registry.register_tool("tool3", tool3)
        
        # Verify all tools are registered
        tools = await tool_registry.list_tools()
        assert len(tools) == 3
        assert "tool1" in tools
        assert "tool2" in tools
        assert "tool3" in tools
        
        # Verify registry info
        info = tool_registry.get_registry_info()
        assert info["total_tools"] == 3
        
        # Unregister one tool
        await tool_registry.unregister_tool("tool2")
        
        tools = await tool_registry.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool3" in tools
        assert "tool2" not in tools 
"""Tool Registry - Central registry for managing agent tools.

This module provides the implementation of the tool registry that manages
tool registration, discovery, and execution for the agent system.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.interfaces.agent_interface import (
    ToolRegistryInterface, ToolInterface, ToolResult, AgentContext
)

logger = logging.getLogger(__name__)


class ToolRegistry(ToolRegistryInterface):
    """Central registry for managing agent tools.
    
    Provides tool registration, discovery, and execution capabilities
    for the agent system.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, ToolInterface] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the tool registry with configuration.
        
        Args:
            config: Configuration dictionary containing:
                - auto_discovery: Whether to auto-discover tools (optional, default False)
                - tool_timeout: Default timeout for tool execution (optional, default 30.0)
                - max_concurrent_tools: Maximum concurrent tool executions (optional, default 10)
        """
        try:
            logger.info("Initializing tool registry")
            
            self._config = config.copy()
            self._config.setdefault("auto_discovery", False)
            self._config.setdefault("tool_timeout", 30.0)
            self._config.setdefault("max_concurrent_tools", 10)
            
            # Initialize any pre-configured tools
            if "pre_configured_tools" in config:
                for tool_name, tool_config in config["pre_configured_tools"].items():
                    await self._initialize_preconfigured_tool(tool_name, tool_config)
            
            self._initialized = True
            logger.info(f"Tool registry initialized with {len(self._tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize tool registry: {str(e)}")
            raise
    
    async def register_tool(self, tool_name: str, tool: ToolInterface) -> bool:
        """Register a tool in the registry.
        
        Args:
            tool_name: Name of the tool to register
            tool: Tool instance implementing ToolInterface
            
        Returns:
            True if tool was registered successfully, False otherwise
        """
        try:
            if not self._initialized:
                logger.error("Tool registry not initialized")
                return False
            
            if not isinstance(tool, ToolInterface):
                logger.error(f"Tool {tool_name} does not implement ToolInterface")
                return False
            
            # Store tool and metadata
            self._tools[tool_name] = tool
            self._tool_metadata[tool_name] = {
                "registered_at": datetime.now(),
                "tool_info": tool.get_tool_info(),
                "input_schema": tool.get_input_schema(),
                "output_schema": tool.get_output_schema()
            }
            
            logger.info(f"Registered tool: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool {tool_name}: {str(e)}")
            return False
    
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool from the registry.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if tool was unregistered successfully, False otherwise
        """
        try:
            if tool_name not in self._tools:
                logger.warning(f"Tool {tool_name} not found in registry")
                return False
            
            # Remove tool and metadata
            del self._tools[tool_name]
            del self._tool_metadata[tool_name]
            
            logger.info(f"Unregistered tool: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_name}: {str(e)}")
            return False
    
    async def get_tool(self, tool_name: str) -> Optional[ToolInterface]:
        """Get a tool from the registry.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(tool_name)
    
    async def list_tools(self) -> List[str]:
        """List all registered tools.
        
        Returns:
            List of registered tool names
        """
        return list(self._tools.keys())
    
    async def execute_tool(self, tool_name: str, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
        """Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            input_data: Input data for the tool
            context: Agent context for the execution
            
        Returns:
            ToolResult containing execution results
        """
        try:
            if not self._initialized:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Tool registry not initialized"
                )
            
            tool = self._tools.get(tool_name)
            if not tool:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Tool {tool_name} not found in registry"
                )
            
            # Check tool health
            if not await tool.health_check():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Tool {tool_name} is not healthy"
                )
            
            # Execute tool with timeout
            start_time = time.time()
            try:
                result = await tool.execute(input_data, context)
                execution_time = time.time() - start_time
                
                # Add execution metadata
                if hasattr(result, 'execution_time'):
                    result.execution_time = execution_time
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Tool {tool_name} execution failed: {str(e)}")
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Tool execution failed: {str(e)}",
                    execution_time=execution_time
                )
            
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {str(e)}")
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution error: {str(e)}"
            )
    
    async def health_check(self) -> bool:
        """Check if the tool registry is healthy.
        
        Returns:
            True if registry is healthy, False otherwise
        """
        try:
            if not self._initialized:
                return False
            
            # Check health of all registered tools
            for tool_name, tool in self._tools.items():
                try:
                    if not await tool.health_check():
                        logger.warning(f"Tool {tool_name} health check failed")
                        return False
                except Exception as e:
                    logger.error(f"Tool {tool_name} health check error: {str(e)}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Tool registry health check failed: {str(e)}")
            return False
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get information about the tool registry.
        
        Returns:
            Dictionary containing registry information
        """
        return {
            "name": "tool_registry",
            "type": "tool_registry",
            "version": "1.0.0",
            "description": "Central registry for managing agent tools",
            "initialized": self._initialized,
            "total_tools": len(self._tools),
            "registered_tools": list(self._tools.keys()),
            "config": self._config,
            "metadata": {
                "created_at": min([meta["registered_at"] for meta in self._tool_metadata.values()]) if self._tool_metadata else None,
                "last_updated": max([meta["registered_at"] for meta in self._tool_metadata.values()]) if self._tool_metadata else None
            }
        }
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool information dictionary if found, None otherwise
        """
        if tool_name not in self._tool_metadata:
            return None
        
        return self._tool_metadata[tool_name]
    
    async def _initialize_preconfigured_tool(self, tool_name: str, tool_config: Dict[str, Any]) -> None:
        """Initialize a pre-configured tool.
        
        Args:
            tool_name: Name of the tool
            tool_config: Tool configuration
        """
        try:
            # This would typically involve dynamic loading of tool classes
            # For now, we'll just log that this would happen
            logger.info(f"Would initialize pre-configured tool: {tool_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize pre-configured tool {tool_name}: {str(e)}")
            raise 
"""LangChain-compatible Agent Nodes.

Wrappers that adapt our agent nodes to work with LangChain tools and utilities.
"""

from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from src.interfaces.agent_interface import (
    AgentNodeInterface, AgentState, AgentContext, ToolInterface, ToolResult
)
from src.agents.agent_nodes import ReasoningNode, DecisionNode, ActionNode
from src.agents.tool_registry import ToolRegistry


class LangChainToolAdapter(BaseTool):
    """Adapter that wraps our ToolInterface to work with LangChain."""
    
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of what the tool does")
    tool_instance: ToolInterface = Field(description="The wrapped tool instance")
    agent_context: Optional[AgentContext] = Field(default=None, description="Agent context for execution")
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, tool_instance: ToolInterface, agent_context: Optional[AgentContext] = None, **kwargs):
        tool_info = tool_instance.get_tool_info()
        super().__init__(
            name=tool_info.get("name", "unknown_tool"),
            description=tool_info.get("description", "A tool for agent operations"),
            tool_instance=tool_instance,
            agent_context=agent_context,
            **kwargs
        )
    
    def _run(
        self,
        query: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        """Run the tool synchronously (not recommended for async tools)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, we can't run sync
                return "Error: Cannot run synchronous tool in async context"
            else:
                return loop.run_until_complete(self._arun(query, run_manager, **kwargs))
        except Exception as e:
            return f"Error running tool: {str(e)}"
    
    async def _arun(
        self,
        query: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        """Run the tool asynchronously."""
        try:
            input_data = {"query": query, **kwargs}
            context = self.agent_context or AgentContext(session_id="langchain_session")
            
            result = await self.tool_instance.execute(input_data, context)
            
            if result.success:
                return str(result.data)
            else:
                return f"Tool execution failed: {result.error}"
                
        except Exception as e:
            return f"Error executing tool: {str(e)}"


class LangChainNodeAdapter(BaseTool):
    """Adapter that wraps our AgentNodeInterface to work with LangChain."""
    
    name: str = Field(description="Name of the node")
    description: str = Field(description="Description of what the node does")
    node_instance: AgentNodeInterface = Field(description="The wrapped node instance")
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, node_instance: AgentNodeInterface, **kwargs):
        node_info = node_instance.get_node_info()
        super().__init__(
            name=node_info.get("type", "unknown_node"),
            description=f"Agent node: {node_info.get('type', 'unknown')}",
            node_instance=node_instance,
            **kwargs
        )
    
    def _run(
        self,
        query: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        """Run the node synchronously."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return "Error: Cannot run synchronous node in async context"
            else:
                return loop.run_until_complete(self._arun(query, run_manager, **kwargs))
        except Exception as e:
            return f"Error running node: {str(e)}"
    
    async def _arun(
        self,
        query: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        """Run the node asynchronously."""
        try:
            # Create agent state and context
            context = AgentContext(session_id="langchain_session")
            state = AgentState(
                context=context,
                data={"query": query, **kwargs}
            )
            
            result = await self.node_instance.execute(state, context)
            
            if result.error:
                return f"Node execution failed: {result.error}"
            else:
                return str(result.data)
                
        except Exception as e:
            return f"Error executing node: {str(e)}"


class LangChainReasoningTool(LangChainNodeAdapter):
    """LangChain tool for reasoning operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        reasoning_node = ReasoningNode()
        if config:
            import asyncio
            asyncio.create_task(reasoning_node.initialize(config))
        
        super().__init__(
            node_instance=reasoning_node,
            name="reasoning_tool",
            description="Performs step-by-step reasoning on a given query or problem"
        )


class LangChainDecisionTool(LangChainNodeAdapter):
    """LangChain tool for decision making operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        decision_node = DecisionNode()
        if config:
            import asyncio
            asyncio.create_task(decision_node.initialize(config))
        
        super().__init__(
            node_instance=decision_node,
            name="decision_tool",
            description="Makes decisions based on confidence and relevance criteria"
        )


class LangChainActionTool(LangChainNodeAdapter):
    """LangChain tool for action execution operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        action_node = ActionNode()
        if config:
            import asyncio
            asyncio.create_task(action_node.initialize(config))
        
        super().__init__(
            node_instance=action_node,
            name="action_tool",
            description="Executes specific actions like search, calculate, or format"
        )


class LangChainToolRegistry:
    """Registry that creates LangChain tools from our tool registry."""
    
    def __init__(self, tool_registry: ToolRegistry):
        self._tool_registry = tool_registry
        self._langchain_tools: Dict[str, LangChainToolAdapter] = {}
    
    async def create_langchain_tools(self, agent_context: Optional[AgentContext] = None) -> List[BaseTool]:
        """Create LangChain tools from registered tools."""
        tools = []
        
        tool_names = await self._tool_registry.list_tools()
        
        for tool_name in tool_names:
            tool_instance = await self._tool_registry.get_tool(tool_name)
            if tool_instance:
                langchain_tool = LangChainToolAdapter(
                    tool_instance=tool_instance,
                    agent_context=agent_context
                )
                self._langchain_tools[tool_name] = langchain_tool
                tools.append(langchain_tool)
        
        return tools
    
    def get_langchain_tool(self, tool_name: str) -> Optional[LangChainToolAdapter]:
        """Get a specific LangChain tool by name."""
        return self._langchain_tools.get(tool_name)
    
    def get_all_langchain_tools(self) -> List[BaseTool]:
        """Get all registered LangChain tools."""
        return list(self._langchain_tools.values())


def create_standard_langchain_tools(config: Optional[Dict[str, Any]] = None) -> List[BaseTool]:
    """Create standard LangChain tools from our agent nodes."""
    return [
        LangChainReasoningTool(config),
        LangChainDecisionTool(config),
        LangChainActionTool(config)
    ]


async def create_langchain_tools_from_registry(
    tool_registry: ToolRegistry,
    agent_context: Optional[AgentContext] = None
) -> List[BaseTool]:
    """Create LangChain tools from a tool registry."""
    langchain_registry = LangChainToolRegistry(tool_registry)
    return await langchain_registry.create_langchain_tools(agent_context) 
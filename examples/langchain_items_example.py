"""LangChain/LangGraph Items Example.

Demonstrates the migrated agent system using LangChain tools and LangGraph workflows
with the items price and quantity tools.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import subprocess
import sys
from typing import Any, Dict, List

# Ensure project root is on sys.path for 'src.*' imports when running as a script
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from langchain_core.messages import HumanMessage

from src.interfaces.agent_interface import AgentContext
from src.agents.tool_registry import ToolRegistry
from src.tools.items_price_tool import ItemsPriceTool
from src.tools.items_quantity_tool import ItemsQuantityTool
from src.agents.langchain_nodes import LangChainToolRegistry, create_langchain_tools_from_registry
from src.agents.langchain_workflows import (
    LangGraphToolUsageWorkflow, 
    LangGraphConversationWorkflow,
    create_default_langgraph_state
)


DB_URL = "sqlite+aiosqlite:///./items.db"
MOCK_API_CMD = [
    "python",
    os.path.join(os.path.dirname(__file__), "mock_quantity_api.py"),
]


async def setup_db() -> None:
    """Set up the SQLite database with sample data."""
    engine = create_async_engine(DB_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL
                )
                """
            )
        )
        await conn.execute(text("DELETE FROM items"))
        await conn.execute(
            text("INSERT INTO items(name, price) VALUES (:name, :price)"),
            [
                {"name": "alpha", "price": 100_000},
                {"name": "beta", "price": 750_000},
                {"name": "gamma", "price": 1_250_000},
                {"name": "delta", "price": 20_000},
            ],
        )


@contextlib.asynccontextmanager
async def start_mock_api():
    """Start the mock quantity API server."""
    proc = subprocess.Popen(MOCK_API_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        await asyncio.sleep(0.8)
        yield proc
    finally:
        with contextlib.suppress(ProcessLookupError):
            proc.send_signal(signal.SIGINT)
        with contextlib.suppress(Exception):
            proc.terminate()


async def demo_langchain_tool_usage_workflow():
    """Demonstrate LangGraph tool usage workflow with LangChain tools."""
    print("\n🔧 === LangGraph Tool Usage Workflow Demo ===")
    
    await setup_db()
    
    async with start_mock_api():
        # Set up tool registry
        registry = ToolRegistry()
        await registry.initialize({})
        
        # Register our custom tools
        price_tool = ItemsPriceTool()
        await price_tool.initialize({"database_url": DB_URL})
        await registry.register_tool("items_price", price_tool)
        
        quantity_tool = ItemsQuantityTool()
        await quantity_tool.initialize({"base_url": "http://127.0.0.1:8099"})
        await registry.register_tool("items_quantity", quantity_tool)
        
        # Create LangChain tools from registry
        context = AgentContext(session_id="langchain-demo", user_id="demo-user")
        langchain_tools = await create_langchain_tools_from_registry(registry, context)
        
        print(f"📋 Created {len(langchain_tools)} LangChain tools:")
        for tool in langchain_tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Create and compile LangGraph workflow
        workflow = LangGraphToolUsageWorkflow(tools=langchain_tools)
        compiled_workflow = workflow.compile()
        
        # Test queries
        test_queries = [
            "give me my items that price is over 500k",
            "show me quantity of items over 100",
            "find items with price greater than 1000000"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            
            # Create initial state
            initial_state = create_default_langgraph_state(query, context)
            
            # Execute workflow
            result = await compiled_workflow.ainvoke(initial_state)
            
            print(f"🎯 Final Answer: {result.get('final_answer', 'No answer generated')}")
            print(f"🔧 Tools Used: {', '.join(result.get('tools_used', []))}")
            
            reasoning_steps = result.get('reasoning_steps', [])
            if reasoning_steps:
                print("🧠 Reasoning Steps:")
                for step in reasoning_steps:
                    print(f"  - {step['step']}: {step.get('data', {})}")


async def demo_langchain_conversation_workflow():
    """Demonstrate LangGraph conversation workflow."""
    print("\n💬 === LangGraph Conversation Workflow Demo ===")
    
    # Create conversation workflow
    workflow = LangGraphConversationWorkflow()
    compiled_workflow = workflow.compile()
    
    context = AgentContext(session_id="conversation-demo", user_id="demo-user")
    
    # Simulate a conversation
    conversation_queries = [
        "Hello there!",
        "Can you help me find some information?",
        "What can you do?",
        "Goodbye!"
    ]
    
    messages = []
    
    for query in conversation_queries:
        print(f"\n👤 User: {query}")
        
        # Create state with conversation history
        state = create_default_langgraph_state(query, context)
        state["messages"] = messages + [HumanMessage(content=query)]
        
        # Execute workflow
        result = await compiled_workflow.ainvoke(state)
        
        response = result.get('final_answer', 'No response generated')
        print(f"🤖 Assistant: {response}")
        
        # Update conversation history
        messages = result.get('messages', [])
        
        reasoning_steps = result.get('reasoning_steps', [])
        if reasoning_steps:
            latest_step = reasoning_steps[-1]
            print(f"🧠 Intent: {latest_step.get('data', {}).get('intent', 'unknown')}")


async def demo_comparison_with_original():
    """Compare new LangGraph implementation with original custom implementation."""
    print("\n⚖️  === Comparison: LangGraph vs Original Implementation ===")
    
    await setup_db()
    
    async with start_mock_api():
        # Original implementation
        print("\n📜 Original Custom Implementation:")
        registry = ToolRegistry()
        await registry.initialize({})
        
        price_tool = ItemsPriceTool()
        await price_tool.initialize({"database_url": DB_URL})
        await registry.register_tool("items_price", price_tool)
        
        context = AgentContext(session_id="comparison-demo", user_id="demo-user")
        query = "give me my items that price is over 500k"
        
        result = await registry.execute_tool("items_price", {"query": query}, context)
        print(f"  Result: {result.data}")
        print(f"  Success: {result.success}")
        
        # LangGraph implementation
        print("\n🔗 LangGraph Implementation:")
        langchain_tools = await create_langchain_tools_from_registry(registry, context)
        workflow = LangGraphToolUsageWorkflow(tools=langchain_tools)
        compiled_workflow = workflow.compile()
        
        initial_state = create_default_langgraph_state(query, context)
        result = await compiled_workflow.ainvoke(initial_state)
        
        print(f"  Final Answer: {result.get('final_answer', 'No answer')}")
        print(f"  Tools Used: {result.get('tools_used', [])}")
        print(f"  Reasoning Steps: {len(result.get('reasoning_steps', []))}")
        
        print("\n📊 Benefits of LangGraph Migration:")
        print("  ✅ Native LangChain tool compatibility")
        print("  ✅ Built-in state management with message history")
        print("  ✅ Standardized workflow patterns")
        print("  ✅ Better observability and debugging")
        print("  ✅ Integration with LangChain ecosystem")
        print("  ✅ Automatic retry and error handling")


async def main():
    """Main demo function."""
    print("🚀 LangChain/LangGraph Migration Demo")
    print("=" * 50)
    
    try:
        await demo_langchain_tool_usage_workflow()
        await demo_langchain_conversation_workflow()
        await demo_comparison_with_original()
        
        print("\n✅ Migration demo completed successfully!")
        print("\n📝 Summary:")
        print("  - Migrated custom workflows to LangGraph StateGraph")
        print("  - Adapted custom tools to LangChain BaseTool interface")
        print("  - Maintained backward compatibility with existing interfaces")
        print("  - Enhanced with native LangChain features (messages, state management)")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 
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

from src.interfaces.agent_interface import AgentContext
from src.agents.tool_registry import ToolRegistry
from src.tools.items_price_tool import ItemsPriceTool
from src.tools.items_quantity_tool import ItemsQuantityTool


DB_URL = "sqlite+aiosqlite:///./items.db"
MOCK_API_CMD = [
    "python",
    os.path.join(os.path.dirname(__file__), "mock_quantity_api.py"),
]


async def setup_db() -> None:
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
    proc = subprocess.Popen(MOCK_API_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        await asyncio.sleep(0.8)
        yield proc
    finally:
        with contextlib.suppress(ProcessLookupError):
            proc.send_signal(signal.SIGINT)
        with contextlib.suppress(Exception):
            proc.terminate()


async def main() -> None:
    await setup_db()

    async with start_mock_api():
        # Build tool registry and register both tools
        registry = ToolRegistry()
        await registry.initialize({})

        price_tool = ItemsPriceTool()
        await price_tool.initialize({"database_url": DB_URL})
        await registry.register_tool("items_price", price_tool)

        quantity_tool = ItemsQuantityTool()
        await quantity_tool.initialize({"base_url": "http://127.0.0.1:8099"})
        await registry.register_tool("items_quantity", quantity_tool)

        # Build a simple agent context
        ctx = AgentContext(session_id="demo-session", user_id="demo-user")

        # Query 1: price over 500k (DB)
        q1 = "give me my items that price is over 500k"
        res1 = await registry.execute_tool("items_price", {"query": q1}, ctx)

        # Query 2: quantity over 100 (API)
        q2 = "give me quantity of items over 100"
        res2 = await registry.execute_tool("items_quantity", {"query": q2}, ctx)

        print("\n=== Price query result (DB) ===")
        print(res1.data)
        print("\n=== Quantity query result (API) ===")
        print(res2.data)


if __name__ == "__main__":
    asyncio.run(main()) 
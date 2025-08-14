from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import subprocess
import sys
import argparse
from typing import Any, Dict, List, Tuple

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Items query example with auto routing")
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="User query, e.g. 'give me my items that price is over 500k' or 'give me quantity of items over 100'",
    )
    return parser.parse_args()


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


def decide_tool(query: str) -> Tuple[str, str]:
    ql = (query or "").lower()
    if "quantity" in ql:
        return "items_quantity", "Detected 'quantity' → using API tool"
    if "price" in ql:
        return "items_price", "Detected 'price' → using DB tool"
    # Fallback heuristics: numbers with 'over' or '>' often imply thresholds; prefer price tool
    if ">" in ql or "over" in ql:
        return "items_price", "Heuristic threshold detected → defaulting to DB tool"
    return "items_quantity", "No explicit signal → defaulting to API tool"


async def main() -> None:
    args = parse_args()
    user_query = args.query or input("Enter your query: ").strip()

    await setup_db()

    async with start_mock_api():
        registry = ToolRegistry()
        await registry.initialize({})

        price_tool = ItemsPriceTool()
        await price_tool.initialize({"database_url": DB_URL})
        await registry.register_tool("items_price", price_tool)

        quantity_tool = ItemsQuantityTool()
        await quantity_tool.initialize({"base_url": "http://127.0.0.1:8099"})
        await registry.register_tool("items_quantity", quantity_tool)

        ctx = AgentContext(session_id="demo-session", user_id="demo-user")

        tool_name, reason = decide_tool(user_query)
        result = await registry.execute_tool(tool_name, {"query": user_query}, ctx)

        print("\n=== Router ===")
        print({"chosen_tool": tool_name, "reason": reason})
        print("\n=== Result ===")
        print(result.data if result.success else {"error": result.error})


if __name__ == "__main__":
    asyncio.run(main()) 
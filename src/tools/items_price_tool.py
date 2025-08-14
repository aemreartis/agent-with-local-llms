from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text

from src.interfaces.agent_interface import ToolInterface, ToolResult, AgentContext


class ItemsPriceTool(ToolInterface):
    """Tool that retrieves item prices from a database.

    Expects a SQLite/SQLAlchemy async database URL in configuration.
    Query parsing supports patterns like 'price ... over 500k' or 'price ... > 500000'.
    """

    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._db_url: Optional[str] = None
        self._initialized: bool = False

    async def initialize(self, config: Dict[str, Any]) -> None:
        self._db_url = config.get("database_url")
        if not self._db_url:
            raise ValueError("ItemsPriceTool requires 'database_url' in config")
        self._engine = create_async_engine(self._db_url, echo=False, future=True)
        self._initialized = True

    async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
        if not self._initialized or not self._engine:
            return ToolResult(success=False, data=None, error="Tool not initialized")

        query_text = (input_data or {}).get("query", "")
        threshold = self._parse_threshold(query_text)

        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(
                    text(
                        """
                        SELECT name, price
                        FROM items
                        WHERE price > :threshold
                        ORDER BY price DESC
                        """
                    ),
                    {"threshold": threshold},
                )
                rows = result.mappings().all()
                items: List[Dict[str, Any]] = [
                    {"name": row["name"], "price": row["price"]} for row in rows
                ]
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"DB error: {str(e)}")

        return ToolResult(success=True, data={"items": items, "threshold": threshold})

    async def health_check(self) -> bool:
        if not self._initialized or not self._engine:
            return False
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_tool_info(self) -> Dict[str, Any]:
        return {
            "name": "ItemsPriceTool",
            "description": "Retrieve item prices from a database filtered by threshold",
            "initialized": self._initialized,
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language query"},
            },
            "required": ["query"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                        },
                        "required": ["name", "price"],
                    },
                },
                "threshold": {"type": "number"},
            },
            "required": ["items", "threshold"],
        }

    def _parse_threshold(self, text_query: str) -> float:
        """Parse price threshold from query text.

        Supports 'over 500k', 'over 1.2m', 'over 500000', '> 500000'. Defaults to 0.
        """
        if not text_query:
            return 0.0

        m = re.search(r">\s*([\d.,]+)\s*", text_query)
        if m:
            return self._normalize_number(m.group(1))

        m = re.search(r"over\s+([\d.,]+)\s*([kKmM])?", text_query)
        if m:
            number = self._normalize_number(m.group(1))
            suffix = m.group(2)
            if suffix:
                if suffix.lower() == "k":
                    number *= 1_000
                elif suffix.lower() == "m":
                    number *= 1_000_000
            return number

        return 0.0

    def _normalize_number(self, s: str) -> float:
        clean = s.replace(",", "")
        try:
            return float(clean)
        except ValueError:
            return 0.0 
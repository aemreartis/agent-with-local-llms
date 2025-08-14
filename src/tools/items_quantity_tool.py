from __future__ import annotations

import re
from typing import Any, Dict, Optional

import httpx

from src.interfaces.agent_interface import ToolInterface, ToolResult, AgentContext


class ItemsQuantityTool(ToolInterface):
    """Tool that retrieves item quantity information via HTTP API.

    Expects 'base_url' in config. The tool will call `{base_url}/items/quantity` with
    query parameters parsed from the user query (e.g., item name filters or thresholds).
    """

    def __init__(self) -> None:
        self._base_url: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized: bool = False

    async def initialize(self, config: Dict[str, Any]) -> None:
        self._base_url = config.get("base_url")
        if not self._base_url:
            raise ValueError("ItemsQuantityTool requires 'base_url' in config")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=10.0)
        self._initialized = True

    async def execute(self, input_data: Dict[str, Any], context: AgentContext) -> ToolResult:
        if not self._initialized or not self._client:
            return ToolResult(success=False, data=None, error="Tool not initialized")

        query_text = (input_data or {}).get("query", "")
        params: Dict[str, Any] = self._parse_query_params(query_text)

        try:
            resp = await self._client.get("/items/quantity", params=params)
            resp.raise_for_status()
            data = resp.json()
            return ToolResult(success=True, data=data)
        except httpx.HTTPError as e:
            return ToolResult(success=False, data=None, error=f"HTTP error: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"API error: {str(e)}")

    async def health_check(self) -> bool:
        if not self._initialized or not self._client:
            return False
        try:
            resp = await self._client.get("/health")
            return resp.status_code == 200
        except Exception:
            return False

    def get_tool_info(self) -> Dict[str, Any]:
        return {
            "name": "ItemsQuantityTool",
            "description": "Retrieve item quantities from an external API",
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
                            "quantity": {"type": "integer"},
                        },
                        "required": ["name", "quantity"],
                    },
                },
            },
            "required": ["items"],
        }

    def _parse_query_params(self, query: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if not query:
            return params

        # If specific item name appears like 'quantity of items <item>' capture it
        m = re.search(r"quantity\s+of\s+items\s+([\w\s-]+)", query, flags=re.IGNORECASE)
        if m:
            params["name"] = m.group(1).strip()

        # Threshold like 'quantity over 100' or '> 100'
        m = re.search(r"(over|>)+\s*([\d]+)", query, flags=re.IGNORECASE)
        if m:
            params["min_quantity"] = int(m.group(2))

        return params 
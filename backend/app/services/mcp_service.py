"""Model Context Protocol (MCP) JSON-RPC 2.0 bridge for local tools and resources."""

import ast
import operator
from typing import Any

from app.core.config import get_settings
from app.services.rag_service import rag_service

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def safe_eval_math(expression: str) -> float:
    """Safely evaluate basic arithmetic expressions without arbitrary code execution."""

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError("Unsupported arithmetic expression")

    tree = ast.parse(expression.strip(), mode="eval")
    return _eval(tree.body)


class McpService:
    """Handle standard MCP JSON-RPC methods (`initialize`, `tools/list`, `tools/call`)."""

    def handle_rpc(
        self,
        rpc_id: str | int | None,
        method: str,
        params: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Dispatch an MCP JSON-RPC 2.0 request."""
        if method == "initialize":
            return self._ok(
                rpc_id,
                {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "offline-ai-mcp", "version": "1.0.0"},
                    "capabilities": {"tools": {}, "resources": {}},
                },
            )

        if method == "tools/list":
            return self._ok(
                rpc_id,
                {
                    "tools": [
                        {
                            "name": "search_documents",
                            "description": "Search the user's indexed PDF/text knowledge base.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"},
                                    "top_k": {"type": "integer", "default": 3},
                                },
                                "required": ["query"],
                            },
                        },
                        {
                            "name": "calculate",
                            "description": "Evaluate an arithmetic expression safely.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"expression": {"type": "string"}},
                                "required": ["expression"],
                            },
                        },
                        {
                            "name": "platform_config",
                            "description": "Inspect active default LLM and resource profile.",
                            "inputSchema": {"type": "object", "properties": {}},
                        },
                    ]
                },
            )

        if method == "tools/call":
            return self._call_tool(rpc_id, params, user_id)

        if method == "resources/list":
            return self._ok(
                rpc_id,
                {
                    "resources": [
                        {
                            "uri": "offline-ai://knowledge-base",
                            "name": "User Uploaded Documents",
                            "mimeType": "text/plain",
                        }
                    ]
                },
            )

        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    def _call_tool(
        self, rpc_id: str | int | None, params: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name == "search_documents":
            query = str(arguments.get("query", ""))
            top_k = int(arguments.get("top_k", 3))
            hits = rag_service.query(user_id=user_id, query_text=query, top_k=top_k)
            return self._ok(rpc_id, {"content": [{"type": "json", "json": hits}]})

        if tool_name == "calculate":
            try:
                value = safe_eval_math(str(arguments.get("expression", "")))
                return self._ok(rpc_id, {"content": [{"type": "text", "text": str(value)}]})
            except ValueError as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32602, "message": str(exc)},
                }

        if tool_name == "platform_config":
            settings = get_settings()
            return self._ok(
                rpc_id,
                {
                    "content": [
                        {
                            "type": "json",
                            "json": {
                                "default_model": settings.default_model,
                                "allowed_models": settings.allowed_models,
                                "rag_enabled": settings.rag_enabled,
                            },
                        }
                    ]
                },
            )

        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"},
        }

    @staticmethod
    def _ok(rpc_id: str | int | None, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": rpc_id, "result": result}


mcp_service = McpService()

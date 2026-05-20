"""Document search tool - semantic search over uploaded documents."""

from typing import Any

from app.tools.base import BaseTool, ToolResult


class DocumentSearchTool(BaseTool):
    name = "document_search"
    description = (
        "Search uploaded documents for relevant information. "
        "Use when answering questions about uploaded files or knowledge base."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 3,
            },
        },
        "required": ["query"],
    }

    def __init__(self, rag_service=None) -> None:
        self._rag_service = rag_service

    async def run(self, query: str, top_k: int = 3, **kwargs: Any) -> ToolResult:
        if not self._rag_service:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="RAG service not configured",
            )
        try:
            results = await self._rag_service.retrieve(query=query, top_k=top_k)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "query": query,
                    "results": [
                        {"content": r.content, "source": r.source, "score": r.score}
                        for r in results
                    ],
                },
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=None, error=str(e))

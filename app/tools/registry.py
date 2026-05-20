"""Tool registry - manages available tools and their instantiation."""

from typing import Any

from app.providers.base import ToolDefinition
from app.tools.base import BaseTool
from app.tools.calculator import CalculatorTool
from app.tools.datetime_tool import CurrentDateTimeTool
from app.tools.document_search import DocumentSearchTool
from app.tools.url_fetcher import URLFetcherTool
from app.tools.web_search import WebSearchTool


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self, rag_service=None) -> None:
        self._tools: dict[str, BaseTool] = {
            "web_search": WebSearchTool(),
            "document_search": DocumentSearchTool(rag_service=rag_service),
            "calculator": CalculatorTool(),
            "current_datetime": CurrentDateTimeTool(),
            "url_fetcher": URLFetcherTool(),
        }

    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_tools_by_names(self, names: list[str]) -> list[BaseTool]:
        return [self._tools[n] for n in names if n in self._tools]

    def to_provider_definitions(self, tool_names: list[str] | None = None) -> list[ToolDefinition]:
        tools = (
            self.get_tools_by_names(tool_names) if tool_names else self.get_all_tools()
        )
        return [
            ToolDefinition(
                name=t.name,
                description=t.description,
                parameters=t.parameters_schema,
            )
            for t in tools
        ]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry")
        result = await tool.run(**arguments)
        return result

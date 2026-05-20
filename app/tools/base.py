"""Abstract base tool class."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: Any
    error: str | None = None


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters_schema: dict[str, Any] = {}

    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        ...

    def to_definition(self) -> dict[str, Any]:
        """Return OpenAI-compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

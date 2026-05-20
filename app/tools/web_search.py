"""Web search tool using DuckDuckGo (no API key required) or Bing."""

import json
from typing import Any

import httpx

from app.tools.base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for current information. Use for news, recent events, or facts."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def run(self, query: str, max_results: int = 5, **kwargs: Any) -> ToolResult:
        try:
            # DuckDuckGo Instant Answer API
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                    },
                )
                data = response.json()

            results = []
            # Abstract answer
            if data.get("Abstract"):
                results.append(
                    {
                        "title": data.get("Heading", query),
                        "snippet": data["Abstract"],
                        "url": data.get("AbstractURL", ""),
                        "source": data.get("AbstractSource", ""),
                    }
                )
            # Related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(
                        {
                            "title": topic.get("Text", "")[:100],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo",
                        }
                    )

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={"query": query, "results": results[:max_results]},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=None, error=str(e))

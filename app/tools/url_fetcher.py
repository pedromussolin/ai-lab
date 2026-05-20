"""URL fetcher tool - fetch and extract content from a URL."""

from typing import Any

import httpx

from app.tools.base import BaseTool, ToolResult

# Blocked domains for security
_BLOCKED_DOMAINS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254"}


class URLFetcherTool(BaseTool):
    name = "url_fetcher"
    description = "Fetch the text content of a URL. Use to read web pages, docs, or articles."
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to fetch"},
            "max_chars": {
                "type": "integer",
                "description": "Maximum characters to return",
                "default": 5000,
            },
        },
        "required": ["url"],
    }

    def _is_blocked(self, url: str) -> bool:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.hostname in _BLOCKED_DOMAINS

    async def run(self, url: str, max_chars: int = 5000, **kwargs: Any) -> ToolResult:
        if self._is_blocked(url):
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="URL is blocked for security reasons",
            )
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "AI-Lab-Bot/1.0"},
                )
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if "text" in content_type or "json" in content_type:
                    text = response.text[:max_chars]
                else:
                    text = f"[Binary content, type: {content_type}]"

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={"url": url, "content": text, "status_code": response.status_code},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=None, error=str(e))

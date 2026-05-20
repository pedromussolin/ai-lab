"""Current date/time tool."""

from datetime import datetime, timezone
from typing import Any

from app.tools.base import BaseTool, ToolResult


class CurrentDateTimeTool(BaseTool):
    name = "current_datetime"
    description = "Get the current date and time in UTC and optionally in a specific timezone."
    parameters_schema = {
        "type": "object",
        "properties": {
            "timezone_name": {
                "type": "string",
                "description": "Timezone name (e.g., 'America/New_York'). Defaults to UTC.",
                "default": "UTC",
            }
        },
        "required": [],
    }

    async def run(self, timezone_name: str = "UTC", **kwargs: Any) -> ToolResult:
        try:
            now_utc = datetime.now(timezone.utc)
            result = {
                "utc": now_utc.isoformat(),
                "date": now_utc.strftime("%Y-%m-%d"),
                "time": now_utc.strftime("%H:%M:%S"),
                "day_of_week": now_utc.strftime("%A"),
                "timestamp": int(now_utc.timestamp()),
            }
            if timezone_name and timezone_name != "UTC":
                try:
                    from zoneinfo import ZoneInfo
                    local_time = now_utc.astimezone(ZoneInfo(timezone_name))
                    result["local"] = local_time.isoformat()
                    result["timezone"] = timezone_name
                except Exception:
                    result["timezone_error"] = f"Unknown timezone: {timezone_name}"
            return ToolResult(tool_name=self.name, success=True, output=result)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=None, error=str(e))

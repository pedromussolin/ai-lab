"""Unit tests for tool calling."""

import pytest

from app.tools.calculator import CalculatorTool
from app.tools.datetime_tool import CurrentDateTimeTool
from app.tools.registry import ToolRegistry


class TestCalculatorTool:
    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        tool = CalculatorTool()
        result = await tool.run(expression="2 + 3 * 4")
        assert result.success
        assert result.output["result"] == 14.0

    @pytest.mark.asyncio
    async def test_division(self):
        tool = CalculatorTool()
        result = await tool.run(expression="10 / 4")
        assert result.success
        assert result.output["result"] == 2.5

    @pytest.mark.asyncio
    async def test_invalid_expression(self):
        tool = CalculatorTool()
        result = await tool.run(expression="import os")
        assert not result.success
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_power(self):
        tool = CalculatorTool()
        result = await tool.run(expression="2 ** 10")
        assert result.success
        assert result.output["result"] == 1024.0


class TestDateTimeTool:
    @pytest.mark.asyncio
    async def test_returns_utc(self):
        tool = CurrentDateTimeTool()
        result = await tool.run()
        assert result.success
        assert "utc" in result.output
        assert "date" in result.output
        assert "day_of_week" in result.output


class TestToolRegistry:
    def test_registry_has_default_tools(self):
        registry = ToolRegistry()
        tools = registry.get_all_tools()
        names = [t.name for t in tools]
        assert "calculator" in names
        assert "current_datetime" in names
        assert "web_search" in names

    def test_tool_definitions_have_correct_structure(self):
        registry = ToolRegistry()
        defs = registry.to_provider_definitions()
        for d in defs:
            assert d.name
            assert d.description
            assert "type" in d.parameters

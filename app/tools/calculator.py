"""Calculator tool - safe arithmetic expression evaluator."""

import ast
import operator
from typing import Any

from app.tools.base import BaseTool, ToolResult

# Safe operators for the calculator
_SAFE_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    elif isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    else:
        raise ValueError(f"Unsafe expression: {ast.dump(node)}")


class CalculatorTool(BaseTool):
    name = "calculator"
    description = (
        "Perform mathematical calculations. Supports +, -, *, /, **, %, //. "
        "Use for arithmetic, percentages, and numeric computations."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')",
            }
        },
        "required": ["expression"],
    }

    async def run(self, expression: str, **kwargs: Any) -> ToolResult:
        try:
            tree = ast.parse(expression, mode="eval")
            result = _safe_eval(tree.body)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={"expression": expression, "result": result},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, output=None, error=str(e))

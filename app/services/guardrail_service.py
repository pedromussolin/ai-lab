"""Guardrail service."""

from app.guardrails.engine import GuardrailEngine


class GuardrailService:
    def __init__(self, config_slug: str = "default") -> None:
        self._engine = GuardrailEngine(config_slug)

    def validate_input(self, text: str) -> str:
        return self._engine.validate_input(text)

    def validate_output(self, text: str) -> str:
        return self._engine.validate_output(text)

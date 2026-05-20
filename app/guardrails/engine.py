"""Guardrail engine - input/output validation and content policy enforcement."""

import re
from pathlib import Path
from typing import Any

import yaml

from app.core.exceptions import GuardrailViolationError

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class GuardrailConfig:
    def __init__(self, data: dict[str, Any]) -> None:
        self.input_validation = data.get("input_validation", {})
        self.jailbreak_detection = data.get("jailbreak_detection", {})
        self.toxicity = data.get("toxicity", {})
        self.pii_masking = data.get("pii_masking", {})
        self.allowed_topics: list[str] = data.get("allowed_topics", [])
        self.blocked_topics: list[str] = data.get("blocked_topics", [])
        self.hallucination_reduction = data.get("hallucination_reduction", {})


class GuardrailEngine:
    def __init__(self, config_slug: str = "default") -> None:
        config_path = _TEMPLATES_DIR / f"{config_slug}.yaml"
        with config_path.open() as f:
            self._config = GuardrailConfig(yaml.safe_load(f))

    def validate_input(self, text: str) -> str:
        """Validate and optionally transform input. Returns (possibly modified) text."""
        cfg = self._config.input_validation
        if not text or not text.strip():
            raise GuardrailViolationError("empty_input", "Input cannot be empty")

        max_len = cfg.get("max_length", 32000)
        if len(text) > max_len:
            raise GuardrailViolationError(
                "input_too_long", f"Input exceeds maximum length of {max_len} characters"
            )

        if cfg.get("strip_html"):
            text = re.sub(r"<[^>]+>", "", text)

        self._check_jailbreak(text)
        self._check_blocked_topics(text)

        if self._config.pii_masking.get("enabled"):
            text = self._mask_pii(text)

        return text

    def validate_output(self, text: str) -> str:
        """Validate LLM output. Returns (possibly modified) text."""
        return text

    def _check_jailbreak(self, text: str) -> None:
        cfg = self._config.jailbreak_detection
        if not cfg.get("enabled"):
            return
        text_lower = text.lower()
        for pattern in cfg.get("patterns", []):
            if re.search(pattern, text_lower, re.IGNORECASE):
                raise GuardrailViolationError(
                    "jailbreak_attempt", "Your message contains content that violates our usage policy."
                )

    def _check_blocked_topics(self, text: str) -> None:
        text_lower = text.lower()
        for topic in self._config.blocked_topics:
            if topic.replace("_", " ") in text_lower:
                raise GuardrailViolationError(
                    "blocked_topic",
                    "Your message contains content that is not allowed on this platform.",
                )

    def _mask_pii(self, text: str) -> str:
        pii_cfg = self._config.pii_masking
        for pattern_def in pii_cfg.get("patterns", []):
            text = re.sub(
                pattern_def["pattern"],
                pattern_def["replacement"],
                text,
                flags=re.IGNORECASE,
            )
        return text

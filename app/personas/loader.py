"""Persona loader and manager."""

from pathlib import Path
from typing import Any

import yaml

from app.prompts.loader import render_string

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class PersonaConfig:
    def __init__(self, data: dict[str, Any]) -> None:
        self.slug: str = data["slug"]
        self.name: str = data["name"]
        self.description: str = data.get("description", "")
        self.tone: str = data.get("tone", "professional")
        self.style: str = data.get("style", "")
        self.behavior: list[str] = data.get("behavior", [])
        self.reasoning_strategy: str = data.get("reasoning_strategy", "step_by_step")
        self.allowed_tools: list[str] = data.get("allowed_tools", [])
        self.temperature: float = data.get("temperature", 0.7)
        self.max_tokens: int = data.get("max_tokens", 4096)
        self.system_prompt_override: str | None = data.get("system_prompt_override")

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "tone": self.tone,
            "style": self.style,
            "behavior": self.behavior,
            "allowed_tools": self.allowed_tools,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


class PersonaLoader:
    def __init__(self) -> None:
        self._cache: dict[str, PersonaConfig] = {}
        self._load_all()

    def _load_all(self) -> None:
        for yaml_file in _TEMPLATES_DIR.glob("*.yaml"):
            with yaml_file.open() as f:
                data = yaml.safe_load(f)
                config = PersonaConfig(data)
                self._cache[config.slug] = config

    def get(self, slug: str) -> PersonaConfig | None:
        return self._cache.get(slug)

    def list_all(self) -> list[PersonaConfig]:
        return list(self._cache.values())

    def get_system_prompt(self, slug: str, **context) -> str:
        persona = self.get(slug)
        if not persona:
            raise ValueError(f"Persona '{slug}' not found")
        if persona.system_prompt_override:
            return render_string(persona.system_prompt_override, **context)
        from datetime import date
        return render_string(
            open(Path(__file__).parent.parent / "prompts/system/default.j2").read(),
            persona=persona,
            allowed_tools=persona.allowed_tools,
            current_date=date.today().isoformat(),
            **context,
        )


_persona_loader = PersonaLoader()


def get_persona_loader() -> PersonaLoader:
    return _persona_loader

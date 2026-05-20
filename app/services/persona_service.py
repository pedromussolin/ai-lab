"""Persona service."""

from app.personas.loader import PersonaConfig, PersonaLoader, get_persona_loader


class PersonaService:
    def __init__(self) -> None:
        self._loader: PersonaLoader = get_persona_loader()

    def get_persona(self, slug: str) -> PersonaConfig | None:
        return self._loader.get(slug)

    def list_personas(self) -> list[PersonaConfig]:
        return self._loader.list_all()

    def get_system_prompt(self, slug: str, **context) -> str:
        return self._loader.get_system_prompt(slug, **context)

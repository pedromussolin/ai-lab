"""Prompt service."""

from app.prompts.loader import render_prompt, render_string


class PromptService:
    def render(
        self,
        template_path: str,
        **variables,
    ) -> str:
        return render_prompt(template_path, **variables)

    def render_string(self, template_str: str, **variables) -> str:
        return render_string(template_str, **variables)

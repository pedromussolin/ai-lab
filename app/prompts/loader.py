"""Jinja2 prompt loader and renderer."""

from pathlib import Path

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateNotFound,
    select_autoescape,
)

_PROMPTS_DIR = Path(__file__).parent

_env = Environment(
    loader=FileSystemLoader(str(_PROMPTS_DIR)),
    autoescape=select_autoescape(["html"]),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)
# Override autoescape for .j2 templates (they are plain text, not HTML)
_env.autoescape = False


def render_prompt(template_path: str, **variables) -> str:
    """
    Render a Jinja2 prompt template.

    Args:
        template_path: Relative path like 'system/default.j2'
        **variables: Template variables

    Returns:
        Rendered string
    """
    try:
        template = _env.get_template(template_path)
        return template.render(**variables).strip()
    except TemplateNotFound as e:
        raise FileNotFoundError(f"Prompt template not found: {template_path}") from e


def render_string(template_str: str, **variables) -> str:
    """Render a Jinja2 template from a raw string."""
    template = _env.from_string(template_str)
    return template.render(**variables).strip()

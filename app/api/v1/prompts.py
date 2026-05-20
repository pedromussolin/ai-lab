"""Prompts endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import verify_api_key
from app.prompts.loader import render_prompt

router = APIRouter()


class RenderPromptRequest(BaseModel):
    template_path: str
    variables: dict = {}


@router.post("/prompts/render")
async def render(
    request: RenderPromptRequest,
    _: str = Depends(verify_api_key),
):
    try:
        rendered = render_prompt(request.template_path, **request.variables)
        return {"rendered": rendered}
    except FileNotFoundError as e:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Prompt template", request.template_path) from e

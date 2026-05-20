"""Guardrails endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import verify_api_key
from app.guardrails.engine import GuardrailEngine

router = APIRouter()


class ValidateRequest(BaseModel):
    text: str
    config: str = "default"


@router.post("/guardrails/validate")
async def validate_input(
    request: ValidateRequest,
    _: str = Depends(verify_api_key),
):
    engine = GuardrailEngine(request.config)
    try:
        validated = engine.validate_input(request.text)
        return {"valid": True, "result": validated}
    except Exception as e:
        return {"valid": False, "error": str(e)}

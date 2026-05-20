"""Personas endpoints."""

from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.personas.loader import get_persona_loader
from app.schemas.persona import PersonaCreate, PersonaSchema

router = APIRouter()


@router.get("/personas", response_model=list[dict])
async def list_personas(_: str = Depends(verify_api_key)):
    loader = get_persona_loader()
    return [p.to_dict() for p in loader.list_all()]


@router.get("/personas/{slug}")
async def get_persona(slug: str, _: str = Depends(verify_api_key)):
    loader = get_persona_loader()
    persona = loader.get(slug)
    if not persona:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Persona", slug)
    return persona.to_dict()

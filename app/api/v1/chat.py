"""Chat endpoints - standard and streaming."""

import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_chat_service
from app.core.security import verify_api_key
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
    _: str = Depends(verify_api_key),
) -> ChatResponse:
    """Non-streaming chat completion."""
    return await service.chat(request)


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
    _: str = Depends(verify_api_key),
) -> StreamingResponse:
    """Server-Sent Events streaming chat."""

    async def event_generator():
        try:
            async for chunk in service.stream_chat(request):
                data = chunk.model_dump_json()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass
        except Exception as e:
            error_data = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {error_data}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

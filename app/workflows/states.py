"""LangGraph workflow state definitions."""

import uuid
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    # Conversation context
    conversation_id: str
    message_id: str
    user_message: str

    # Resolved config
    provider: str
    model: str
    temperature: float
    max_tokens: int
    persona_id: str | None
    tools_enabled: bool
    use_rag: bool

    # Processed data
    validated_input: str
    system_prompt: str
    rag_context: list[dict[str, Any]]
    tool_calls_made: list[dict[str, Any]]

    # LangGraph messages accumulator
    messages: Annotated[list, add_messages]

    # Output
    response_content: str
    citations: list[dict[str, Any]]
    usage: dict[str, int]
    error: str | None
    should_retry: bool

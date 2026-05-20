"""Chat service - orchestrates the LangGraph workflow."""

import uuid
from collections.abc import AsyncGenerator
from typing import Any

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.providers.factory import LLMProviderFactory
from app.rag.pipeline import RAGPipeline
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.schemas.chat import ChatRequest, ChatResponse, Citation, StreamChunk, ToolCallResult
from app.services.embedding_service import EmbeddingService
from app.services.guardrail_service import GuardrailService
from app.services.persona_service import PersonaService
from app.services.prompt_service import PromptService
from app.services.rag_service import RAGService
from app.tools.registry import ToolRegistry
from app.workflows.chat_workflow import build_chat_workflow


class ChatService:
    def __init__(
        self,
        llm_factory: LLMProviderFactory,
        conv_repo: ConversationRepository,
        msg_repo: MessageRepository,
        persona_svc: PersonaService,
        prompt_svc: PromptService,
        guardrail_svc: GuardrailService,
        rag_svc: RAGService,
    ) -> None:
        self._llm_factory = llm_factory
        self._conv_repo = conv_repo
        self._msg_repo = msg_repo
        self._persona_svc = persona_svc
        self._prompt_svc = prompt_svc
        self._guardrail_svc = guardrail_svc
        self._rag_svc = rag_svc

    async def _get_or_create_conversation(
        self, request: ChatRequest
    ) -> Conversation:
        if request.conversation_id:
            conv = await self._conv_repo.get_by_id(request.conversation_id)
            if not conv:
                raise ValueError(f"Conversation {request.conversation_id} not found")
            return conv

        conv = Conversation(
            provider=request.provider or settings.default_llm_provider,
            model=request.model or "gpt-4o",
            persona_id=request.persona_id,
        )
        return await self._conv_repo.create(conv)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Non-streaming chat completion."""
        conv = await self._get_or_create_conversation(request)
        rag_pipeline = await self._rag_svc.get_pipeline()
        tool_registry = ToolRegistry(rag_service=self._rag_svc)
        workflow = build_chat_workflow(
            llm_factory=self._llm_factory,
            rag_pipeline=rag_pipeline,
            tool_registry=tool_registry,
        )

        # Load conversation history
        history = await self._msg_repo.get_conversation_messages(
            conversation_id=conv.id, limit=50
        )

        initial_state = {
            "conversation_id": str(conv.id),
            "message_id": str(uuid.uuid4()),
            "user_message": request.message,
            "provider": request.provider or conv.provider,
            "model": request.model or conv.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "persona_id": request.persona_id or conv.persona_id,
            "tools_enabled": request.tools_enabled,
            "use_rag": request.use_rag,
            "validated_input": "",
            "system_prompt": "",
            "rag_context": [],
            "tool_calls_made": [],
            "messages": [],
            "response_content": "",
            "citations": [],
            "usage": {},
            "error": None,
            "should_retry": False,
        }

        result = await workflow.ainvoke(initial_state)

        # Persist messages
        msg_id = uuid.UUID(result["message_id"])
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=request.message,
            token_count=result.get("usage", {}).get("prompt_tokens", 0),
        )
        await self._msg_repo.create(user_msg)

        assistant_msg = Message(
            id=msg_id,
            conversation_id=conv.id,
            role="assistant",
            content=result.get("response_content", ""),
            citations=result.get("citations", []),
            token_count=result.get("usage", {}).get("completion_tokens", 0),
        )
        await self._msg_repo.create(assistant_msg)

        return ChatResponse(
            conversation_id=conv.id,
            message_id=msg_id,
            content=result.get("response_content", ""),
            citations=[
                Citation(**c)
                for c in result.get("citations", [])
                if isinstance(c, dict)
            ],
            tool_calls=[
                ToolCallResult(
                    tool_name=tc["name"],
                    tool_input=tc["input"],
                    tool_output=tc["output"],
                    duration_ms=0,
                )
                for tc in result.get("tool_calls_made", [])
            ],
            provider=result["provider"],
            model=result["model"],
            usage=result.get("usage", {}),
        )

    async def stream_chat(
        self, request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Streaming chat completion using SSE."""
        conv = await self._get_or_create_conversation(request)
        provider = self._llm_factory.get_llm_provider(request.provider or conv.provider)
        msg_id = uuid.uuid4()

        from app.guardrails.engine import GuardrailEngine
        from app.personas.loader import get_persona_loader
        from app.providers.base import LLMMessage
        from datetime import date

        guardrail = GuardrailEngine()
        persona_loader = get_persona_loader()

        # Validate input
        try:
            validated = guardrail.validate_input(request.message)
        except Exception as e:
            yield StreamChunk(type="error", error=str(e))
            return

        # Build system prompt
        persona_id = request.persona_id or conv.persona_id or "assistant_default"
        try:
            system_prompt = persona_loader.get_system_prompt(
                persona_id, current_date=date.today().isoformat()
            )
        except ValueError:
            system_prompt = "You are a helpful AI assistant."

        messages = [LLMMessage(role="system", content=system_prompt)]

        # Add history
        history = await self._msg_repo.get_conversation_messages(conv.id, limit=50)
        for msg in history:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        # RAG
        if request.use_rag:
            try:
                rag_results = await self._rag_svc.retrieve(validated)
                if rag_results:
                    context = "\n\n".join(f"[{r.source}]: {r.content}" for r in rag_results)
                    validated = f"Context:\n{context}\n\nQuestion: {validated}"
                    for r in rag_results:
                        yield StreamChunk(
                            type="citation",
                            citation=Citation(
                                source=r.source,
                                content_snippet=r.content[:200],
                                confidence=r.score,
                            ),
                        )
            except Exception:
                pass

        messages.append(LLMMessage(role="user", content=validated))

        full_content = ""
        try:
            async for token in provider.stream(
                messages=messages,
                model=request.model or conv.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                full_content += token
                yield StreamChunk(
                    type="chunk",
                    content=token,
                    conversation_id=conv.id,
                    message_id=msg_id,
                )
        except Exception as e:
            yield StreamChunk(type="error", error=str(e))
            return

        # Persist
        user_msg = Message(conversation_id=conv.id, role="user", content=request.message)
        await self._msg_repo.create(user_msg)
        assistant_msg = Message(
            id=msg_id, conversation_id=conv.id, role="assistant", content=full_content
        )
        await self._msg_repo.create(assistant_msg)

        yield StreamChunk(
            type="done",
            conversation_id=conv.id,
            message_id=msg_id,
        )

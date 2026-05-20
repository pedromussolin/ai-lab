"""LangGraph chat orchestration workflow."""

import json
import uuid
from datetime import date
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.core.config import settings
from app.core.exceptions import GuardrailViolationError
from app.guardrails.engine import GuardrailEngine
from app.personas.loader import get_persona_loader
from app.providers.base import LLMMessage
from app.providers.factory import LLMProviderFactory
from app.rag.pipeline import RAGPipeline
from app.services.embedding_service import EmbeddingService
from app.tools.registry import ToolRegistry
from app.workflows.states import ChatState


def build_chat_workflow(
    llm_factory: LLMProviderFactory,
    rag_pipeline: RAGPipeline | None = None,
    tool_registry: ToolRegistry | None = None,
) -> CompiledStateGraph:
    """Build and compile the LangGraph chat workflow."""

    guardrail_engine = GuardrailEngine()
    persona_loader = get_persona_loader()

    # ---- Nodes ----

    async def validate_input(state: ChatState) -> dict:
        """Node: Validate and sanitize user input via guardrails."""
        try:
            validated = guardrail_engine.validate_input(state["user_message"])
            return {"validated_input": validated, "error": None}
        except GuardrailViolationError as e:
            return {"validated_input": "", "error": str(e), "response_content": str(e)}

    async def build_system_prompt(state: ChatState) -> dict:
        """Node: Build the system prompt from persona config."""
        persona_id = state.get("persona_id") or "assistant_default"
        try:
            system_prompt = persona_loader.get_system_prompt(
                persona_id,
                current_date=date.today().isoformat(),
            )
        except ValueError:
            system_prompt = f"You are a helpful AI assistant. Today is {date.today().isoformat()}."
        return {"system_prompt": system_prompt}

    async def rag_retrieval(state: ChatState) -> dict:
        """Node: Retrieve relevant context from RAG pipeline."""
        if not state.get("use_rag") or not rag_pipeline:
            return {"rag_context": []}
        try:
            results = await rag_pipeline.retrieve(query=state["validated_input"], top_k=5)
            rag_context = [
                {"content": r.content, "source": r.source, "score": r.score}
                for r in results
            ]
            return {"rag_context": rag_context}
        except Exception:
            return {"rag_context": []}

    async def generate_response(state: ChatState) -> dict:
        """Node: Call LLM to generate response, with tool calling loop."""
        if state.get("error"):
            return {}

        provider = llm_factory.get_llm_provider(state["provider"])

        # Build messages
        messages_for_llm: list[LLMMessage] = [
            LLMMessage(role="system", content=state["system_prompt"])
        ]

        # Add RAG context to the user message if available
        user_content = state["validated_input"]
        if state.get("rag_context"):
            context_str = "\n\n".join(
                f"[Source: {c['source']}]\n{c['content']}"
                for c in state["rag_context"]
            )
            user_content = (
                f"Use the following context to answer the question:\n\n"
                f"{context_str}\n\n"
                f"Question: {user_content}"
            )

        # Restore conversation history from state messages
        for msg in state.get("messages", []):
            if isinstance(msg, HumanMessage):
                messages_for_llm.append(LLMMessage(role="user", content=str(msg.content)))
            elif isinstance(msg, AIMessage):
                messages_for_llm.append(LLMMessage(role="assistant", content=str(msg.content)))

        messages_for_llm.append(LLMMessage(role="user", content=user_content))

        # Get tool definitions
        tool_defs = None
        if state.get("tools_enabled") and tool_registry:
            persona_id = state.get("persona_id") or "assistant_default"
            persona = persona_loader.get(persona_id)
            allowed_tools = persona.allowed_tools if persona else None
            tool_defs = tool_registry.to_provider_definitions(allowed_tools)

        response = await provider.complete(
            messages=messages_for_llm,
            model=state["model"],
            temperature=state["temperature"],
            max_tokens=state["max_tokens"],
            tools=tool_defs,
        )

        # Tool calling loop
        tool_calls_made = []
        iterations = 0
        while response.tool_calls and iterations < 5:
            iterations += 1
            # Execute each tool call
            tool_results_messages: list[LLMMessage] = []
            for tc in response.tool_calls:
                fn = tc["function"]
                tool_name = fn["name"]
                try:
                    args = json.loads(fn["arguments"])
                except json.JSONDecodeError:
                    args = {}

                if tool_registry:
                    tool_result = await tool_registry.execute_tool(tool_name, args)
                    output = tool_result.output if tool_result.success else f"Error: {tool_result.error}"
                else:
                    output = "Tool registry not available"

                tool_calls_made.append(
                    {"name": tool_name, "input": args, "output": output}
                )
                tool_results_messages.append(
                    LLMMessage(
                        role="tool",
                        content=json.dumps(output) if not isinstance(output, str) else output,
                        tool_call_id=tc["id"],
                    )
                )

            # Add assistant message with tool calls + tool results
            messages_for_llm.append(
                LLMMessage(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                )
            )
            messages_for_llm.extend(tool_results_messages)

            # Call LLM again with tool results
            response = await provider.complete(
                messages=messages_for_llm,
                model=state["model"],
                temperature=state["temperature"],
                max_tokens=state["max_tokens"],
                tools=tool_defs,
            )

        # Build citations from RAG context
        citations = [
            {"source": c["source"], "content_snippet": c["content"][:200], "confidence": c["score"]}
            for c in state.get("rag_context", [])
        ]

        return {
            "response_content": response.content,
            "usage": response.usage,
            "tool_calls_made": tool_calls_made,
            "citations": citations,
            "messages": [HumanMessage(content=user_content), AIMessage(content=response.content)],
        }

    async def validate_output(state: ChatState) -> dict:
        """Node: Validate LLM output via guardrails."""
        if state.get("error"):
            return {}
        try:
            validated = guardrail_engine.validate_output(state.get("response_content", ""))
            return {"response_content": validated}
        except GuardrailViolationError as e:
            return {"response_content": str(e), "error": str(e)}

    # ---- Routing ----

    def should_continue(state: ChatState) -> str:
        if state.get("error"):
            return END
        return "generate_response"

    # ---- Graph ----

    graph = StateGraph(ChatState)
    graph.add_node("validate_input", validate_input)
    graph.add_node("build_system_prompt", build_system_prompt)
    graph.add_node("rag_retrieval", rag_retrieval)
    graph.add_node("generate_response", generate_response)
    graph.add_node("validate_output", validate_output)

    graph.add_edge(START, "validate_input")
    graph.add_edge("validate_input", "build_system_prompt")
    graph.add_edge("build_system_prompt", "rag_retrieval")
    graph.add_conditional_edges("rag_retrieval", should_continue)
    graph.add_edge("generate_response", "validate_output")
    graph.add_edge("validate_output", END)

    return graph.compile()

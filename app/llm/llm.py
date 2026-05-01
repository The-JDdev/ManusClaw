from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any, Optional

from app.config import Config
from app.exceptions import TokenLimitExceeded
from app.logger import logger
from app.schema import Message, Role, ToolCall, Function


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


# ---------------------------------------------------------------------------
# Mock LLM  (deterministic stub so the app runs without credentials)
# ---------------------------------------------------------------------------

class MockLLM:
    """A deterministic stub LLM for testing without credentials."""

    _STEP = 0

    async def ask(self, messages: list[Message], **kwargs: Any) -> Message:
        MockLLM._STEP += 1
        content = (
            f"[MockLLM step {MockLLM._STEP}] "
            "I have analysed the task. Let me use the terminate tool to complete it."
        )
        return Message.assistant(content=content)

    async def ask_tool(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Message:
        MockLLM._STEP += 1
        tool_names = [t["function"]["name"] for t in tools if "function" in t]

        # Step 1: use python_execute if available (demonstrates real tool use)
        if MockLLM._STEP == 1 and "python_execute" in tool_names:
            tc = ToolCall(
                id=f"call_{random.randint(10000,99999)}",
                function=Function(
                    name="python_execute",
                    arguments=json.dumps({"code": "print('Hello from ManusClaw!')"}),
                ),
            )
            return Message.assistant(
                content=f"[MockLLM step {MockLLM._STEP}] Running Python to greet the user.",
                tool_calls=[tc],
            )

        # Step 1 fallback or step 2+: call terminate
        if "terminate" in tool_names:
            tc = ToolCall(
                id=f"call_{random.randint(10000,99999)}",
                function=Function(
                    name="terminate",
                    arguments=json.dumps({"reason": "Task completed successfully by MockLLM."}),
                ),
            )
            return Message.assistant(
                content=f"[MockLLM step {MockLLM._STEP}] Terminating.",
                tool_calls=[tc],
            )

        return Message.assistant(content=f"[MockLLM step {MockLLM._STEP}] Done.")


# ---------------------------------------------------------------------------
# Real LLM wrappers
# ---------------------------------------------------------------------------

class OpenAILLM:
    def __init__(self, cfg: Any) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            timeout=cfg.timeout,
        )
        self._model = cfg.model
        self._max_tokens = cfg.max_tokens
        self._temperature = cfg.temperature

    async def ask(self, messages: list[Message], **kwargs: Any) -> Message:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[m.to_dict() for m in messages],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        choice = resp.choices[0]
        return Message.assistant(content=choice.message.content)

    async def ask_tool(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Message:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[m.to_dict() for m in messages],
            tools=tools,
            tool_choice="auto",
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        choice = resp.choices[0]
        msg = choice.message
        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    function=Function(name=tc.function.name, arguments=tc.function.arguments),
                )
                for tc in msg.tool_calls
            ]
        return Message.assistant(content=msg.content, tool_calls=tool_calls)


class AnthropicLLM:
    def __init__(self, cfg: Any) -> None:
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=cfg.api_key)
        self._model = cfg.model
        self._max_tokens = cfg.max_tokens
        self._temperature = cfg.temperature

    def _convert_messages(self, messages: list[Message]) -> tuple[Optional[str], list[dict]]:
        system_prompt = None
        converted = []
        for m in messages:
            if m.role == Role.SYSTEM:
                system_prompt = m.content
            else:
                converted.append({"role": m.role.value, "content": m.content or ""})
        return system_prompt, converted

    async def ask(self, messages: list[Message], **kwargs: Any) -> Message:
        system, msgs = self._convert_messages(messages)
        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            system=system or "",
            messages=msgs,
        )
        return Message.assistant(content=resp.content[0].text)

    async def ask_tool(self, messages: list[Message], tools: list[dict], **kwargs: Any) -> Message:
        # Anthropic tool format differs; simplified passthrough
        return await self.ask(messages, **kwargs)


class OllamaLLM(OpenAILLM):
    """Ollama uses an OpenAI-compatible API."""
    def __init__(self, cfg: Any) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key="ollama",
            base_url=cfg.base_url or "http://localhost:11434/v1",
            timeout=cfg.timeout,
        )
        self._model = cfg.model
        self._max_tokens = cfg.max_tokens
        self._temperature = cfg.temperature


# ---------------------------------------------------------------------------
# Main LLM class with retry logic
# ---------------------------------------------------------------------------

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class LLM:
    def __init__(self) -> None:
        cfg = Config.get()
        self._cfg = cfg.llm
        self._backend = self._build_backend()

    def _build_backend(self) -> Any:
        provider = self._cfg.provider
        if provider == "mock":
            logger.info("Using MockLLM (no credentials required)")
            return MockLLM()
        if provider in ("openai", "azure"):
            return OpenAILLM(self._cfg)
        if provider == "anthropic":
            return AnthropicLLM(self._cfg)
        if provider == "ollama":
            return OllamaLLM(self._cfg)
        logger.warning(f"Unknown LLM provider '{provider}', falling back to MockLLM")
        return MockLLM()

    async def _with_retry(self, coro_fn: Any, *args: Any, **kwargs: Any) -> Any:
        max_retries = self._cfg.max_retries
        for attempt in range(max_retries):
            try:
                return await coro_fn(*args, **kwargs)
            except TokenLimitExceeded:
                raise
            except Exception as e:
                err_str = str(e)
                status = getattr(e, "status_code", None)
                if status == 400 and "token" in err_str.lower():
                    raise TokenLimitExceeded(err_str) from e
                if attempt < max_retries - 1:
                    wait = min(2 ** attempt + random.uniform(0, 1), 60)
                    logger.warning(f"LLM error (attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait:.1f}s")
                    await asyncio.sleep(wait)
                else:
                    raise

    async def ask(self, messages: list[Message], **kwargs: Any) -> Message:
        return await self._with_retry(self._backend.ask, messages, **kwargs)

    async def ask_tool(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        **kwargs: Any,
    ) -> Message:
        return await self._with_retry(self._backend.ask_tool, messages, tools, **kwargs)

    def count_tokens(self, text: str) -> int:
        return count_tokens(text, self._cfg.model)

from __future__ import annotations

"""
Universal LLM Router — Dual-Mode Architecture
=============================================

Mode 1 — OFFICIAL PROVIDERS
  Set `provider` to one of: openai | anthropic | google | mock
  Uses official SDKs or dedicated client paths.

Mode 2 — UNIVERSAL / AGNOSTIC  (OpenRouter, Ollama, LMStudio, any proxy)
  Just set `base_url` + `api_key` (can be "none") + `model`.
  System sends a standard OpenAI-compatible request — no hardcoded provider checks.
  Works with: OpenRouter, Ollama, LMStudio, vLLM, Together AI, Groq, Perplexity, etc.

Priority: if `base_url` is set AND `provider` is empty/null → agnostic mode.
          if `provider` is explicitly set → official SDK mode.
"""

import asyncio
import random
import time
from typing import Any, Optional

from app.config import Config
from app.exceptions import RateLimitError, TokenLimitExceeded
from app.logger import logger
from app.schema import Message, Role, ToolCall, Function


MAX_RETRIES      = 8
RETRY_BASE_WAIT  = 1.0
RETRY_MAX_WAIT   = 60.0


def _msg_from_openai(choice: dict) -> Message:
    msg = choice.get("message", {})
    role = Role(msg.get("role", "assistant"))
    content = msg.get("content")
    raw_tcs = msg.get("tool_calls") or []
    tool_calls = [
        ToolCall(
            id=tc["id"],
            type=tc.get("type", "function"),
            function=Function(
                name=tc["function"]["name"],
                arguments=tc["function"].get("arguments", "{}"),
            ),
        )
        for tc in raw_tcs
    ]
    return Message(role=role, content=content, tool_calls=tool_calls or None)


class MockLLM:
    def __init__(self) -> None:
        self._call_count = 0

    async def chat(self, messages: list, tools: Optional[list] = None) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {"choices": [{"message": {
                "role": "assistant",
                "content": f"[MockLLM step 1] Running Python to greet the user.",
                "tool_calls": [{
                    "id": "mock-tc-1", "type": "function",
                    "function": {"name": "python_execute",
                                 "arguments": '{"code": "print(\'Hello from ManusClaw!\')"}'},
                }],
            }}]}
        return {"choices": [{"message": {
            "role": "assistant",
            "content": "Task complete.",
            "tool_calls": [{
                "id": "mock-tc-2", "type": "function",
                "function": {"name": "terminate",
                             "arguments": '{"reason": "Task completed successfully by MockLLM."}'},
            }],
        }}]}

    async def ask(self, messages: list[Message], **_) -> Message:
        self._call_count += 1
        step = self._call_count
        content = f"[MockLLM step {step}] Running Python to greet the user."
        return Message.assistant(content=content)

    async def ask_tool(self, messages: list[Message], tools: list[dict], **_) -> Message:
        self._call_count += 1
        if self._call_count == 1:
            return Message(
                role=Role.ASSISTANT,
                content="I will run a Python hello-world.",
                tool_calls=[
                    ToolCall(
                        id="mock-tc-1",
                        type="function",
                        function=Function(
                            name="python_execute",
                            arguments='{"code": "print(\'Hello from ManusClaw!\')"}',
                        ),
                    )
                ],
            )
        return Message(
            role=Role.ASSISTANT,
            content="Task complete.",
            tool_calls=[
                ToolCall(
                    id="mock-tc-2",
                    type="function",
                    function=Function(
                        name="terminate",
                        arguments='{"reason": "Task completed successfully by MockLLM."}',
                    ),
                )
            ],
        )


class UniversalClient:
    def __init__(self, base_url: str, api_key: str, model: str, **kwargs) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_tokens = kwargs.get("max_tokens", 8192)
        self.temperature = kwargs.get("temperature", 0.0)
        self._extra_headers = kwargs.get("extra_headers", {})

    async def _post(self, payload: dict) -> dict:
        import aiohttp
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self._extra_headers,
        }
        url = f"{self.base_url}/chat/completions"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 429:
                    raise RateLimitError("Rate limited")
                if resp.status == 400:
                    body = await resp.text()
                    if "context" in body.lower() or "token" in body.lower():
                        raise TokenLimitExceeded(body)
                    raise ValueError(f"Bad request: {body}")
                resp.raise_for_status()
                return await resp.json()

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return await self._post(payload)


class OpenAIClient:
    def __init__(self, cfg) -> None:
        from openai import AsyncOpenAI
        self._c = AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url or None)
        self.model = cfg.model
        self.max_tokens = cfg.max_tokens
        self.temperature = cfg.temperature

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = await self._c.chat.completions.create(**kwargs)
        return resp.model_dump()


class AnthropicClient:
    def __init__(self, cfg) -> None:
        from anthropic import AsyncAnthropic
        self._c = AsyncAnthropic(api_key=cfg.api_key)
        self.model = cfg.model
        self.max_tokens = cfg.max_tokens

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        conv = [m for m in messages if m["role"] != "system"]

        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=conv,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {}),
                }
                for t in tools
            ]

        resp = await self._c.messages.create(**kwargs)
        content = ""
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                import json
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                })
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": content or None,
                    "tool_calls": tool_calls or None,
                }
            }]
        }


class GoogleClient:
    def __init__(self, cfg) -> None:
        import google.generativeai as genai
        genai.configure(api_key=cfg.api_key)
        self._model_name = cfg.model or "gemini-1.5-pro"
        self.max_tokens = cfg.max_tokens
        self.temperature = cfg.temperature

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None) -> dict:
        import google.generativeai as genai
        model = genai.GenerativeModel(self._model_name)
        prompt = "\n".join(
            f"{m['role'].upper()}: {m.get('content') or ''}"
            for m in messages
        )
        resp = await asyncio.to_thread(model.generate_content, prompt)
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": resp.text,
                    "tool_calls": None,
                }
            }]
        }


class LLM:
    def __init__(self) -> None:
        cfg = Config.get()
        self._backend = self._build_backend(cfg)
        self._max_retries = max(1, int(cfg.llm.max_retries or MAX_RETRIES))

    def _build_backend(self, cfg):
        provider = (cfg.llm.provider or "").lower().strip()

        if provider == "mock":
            logger.info("Using MockLLM (no credentials required)")
            return MockLLM()

        universal_triggers = {"universal", "openrouter", "ollama", "lmstudio", "openai-compat", "groq", "together", "perplexity", "agentrouter", ""}
        if cfg.llm.base_url and (not provider or provider in universal_triggers):
            logger.info(f"Universal/Agnostic LLM mode — base_url={cfg.llm.base_url} model={cfg.llm.model}")
            return UniversalClient(
                base_url=cfg.llm.base_url,
                api_key=cfg.llm.api_key or "none",
                model=cfg.llm.model,
                max_tokens=cfg.llm.max_tokens,
                temperature=cfg.llm.temperature,
                extra_headers=cfg.llm.extra_headers or {},
            )

        if provider == "openai":
            logger.info(f"Official provider: OpenAI (model={cfg.llm.model})")
            return OpenAIClient(cfg.llm)
        if provider == "anthropic":
            logger.info(f"Official provider: Anthropic (model={cfg.llm.model})")
            return AnthropicClient(cfg.llm)
        if provider in ("google", "gemini"):
            logger.info(f"Official provider: Google/Gemini (model={cfg.llm.model})")
            return GoogleClient(cfg.llm)

        if cfg.llm.base_url:
            logger.info(f"Unknown provider '{provider}', falling back to Universal mode")
            return UniversalClient(
                base_url=cfg.llm.base_url,
                api_key=cfg.llm.api_key or "none",
                model=cfg.llm.model,
                max_tokens=cfg.llm.max_tokens,
                temperature=cfg.llm.temperature,
            )

        logger.warning(f"No valid LLM config found (provider='{provider}'). Using MockLLM.")
        return MockLLM()

    async def ask(self, messages: list[Message], **kwargs) -> Message:
        raw = [m.to_dict() for m in messages]
        data = await self._call_with_retry(raw, tools=None, **kwargs)
        return _msg_from_openai(data["choices"][0])

    async def ask_tool(self, messages: list[Message], tools: list[dict], **kwargs) -> Message:
        raw = [m.to_dict() for m in messages]
        data = await self._call_with_retry(raw, tools=tools, **kwargs)
        return _msg_from_openai(data["choices"][0])

    async def _call_with_retry(self, messages: list[dict], tools: Optional[list[dict]], **kwargs) -> dict:
        wait = RETRY_BASE_WAIT
        for attempt in range(1, self._max_retries + 1):
            try:
                return await self._backend.chat(messages, tools=tools)
            except TokenLimitExceeded:
                raise
            except RateLimitError:
                logger.warning(f"[LLM] Rate limited (attempt {attempt}). Waiting {wait:.1f}s...")
                await asyncio.sleep(wait)
                wait = min(wait * 2 + random.uniform(0, 1), RETRY_MAX_WAIT)
            except Exception as e:
                if attempt == self._max_retries:
                    raise
                logger.warning(f"[LLM] Error (attempt {attempt}/{self._max_retries}): {e}. Retrying in {wait:.1f}s...")
                await asyncio.sleep(wait)
                wait = min(wait * 2 + random.uniform(0, 1), RETRY_MAX_WAIT)

        raise RuntimeError("LLM failed after all retries")

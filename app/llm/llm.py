from __future__ import annotations

"""
Universal LLM Router — Multi-Provider with Credential Pool & Token Tracking
============================================================================

Providers: openai | anthropic | google | mistral | bedrock | mock | universal
Credential Pool: multiple API keys per provider with priority ordering + auto-rotation
Token Budget: tracks input/output/cache/reasoning tokens per session + grace call
Secret Redaction: optionally scrub keys from log output
"""

import asyncio
import random
import time
from typing import Any, Optional

from app.config import Config
from app.exceptions import RateLimitError, TokenLimitExceeded
from app.logger import logger
from app.schema import Message, Role, ToolCall, Function
from app.llm.token_tracker import TokenBudget, TokenUsage
from app.llm.credential_pool import CredentialPool, build_pool_from_config

MAX_RETRIES     = 8
RETRY_BASE_WAIT = 1.0
RETRY_MAX_WAIT  = 60.0


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
                "content": "[MockLLM] Running Python hello-world.",
                "tool_calls": [{
                    "id": "mock-tc-1", "type": "function",
                    "function": {"name": "python_execute",
                                 "arguments": '{"code": "print('Hello from ManusClaw!')"}'},
                }],
            }}]}
        return {"choices": [{"message": {
            "role": "assistant",
            "content": "Task complete.",
            "tool_calls": [{
                "id": "mock-tc-2", "type": "function",
                "function": {"name": "terminate",
                             "arguments": '{"reason": "Completed by MockLLM."}'},
            }],
        }}]}

    async def ask(self, messages, **_) -> Message:
        self._call_count += 1
        return Message.assistant(content=f"[MockLLM step {self._call_count}] Thinking...")

    async def ask_tool(self, messages, tools, **_) -> Message:
        self._call_count += 1
        if self._call_count == 1:
            return Message(role=Role.ASSISTANT, content="Running hello-world.", tool_calls=[
                ToolCall(id="mock-tc-1", type="function", function=Function(
                    name="python_execute", arguments='{"code": "print('Hello from ManusClaw!')"}'
                ))
            ])
        return Message(role=Role.ASSISTANT, content="Done.", tool_calls=[
            ToolCall(id="mock-tc-2", type="function", function=Function(
                name="terminate", arguments='{"reason": "MockLLM complete."}'
            ))
        ])


class UniversalClient:
    def __init__(self, base_url: str, api_key: str, model: str, **kwargs) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_tokens = kwargs.get("max_tokens", 8192)
        self.temperature = kwargs.get("temperature", 0.0)
        self._extra_headers = kwargs.get("extra_headers", {})

    async def _post(self, payload: dict, api_key: Optional[str] = None) -> dict:
        import aiohttp
        key = api_key or self.api_key
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            **self._extra_headers,
        }
        url = f"{self.base_url}/chat/completions"
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
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

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None,
                   api_key: Optional[str] = None) -> dict:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return await self._post(payload, api_key=api_key)


class OpenAIClient:
    def __init__(self, cfg) -> None:
        from openai import AsyncOpenAI
        self._c = AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url or None)
        self.model = cfg.model
        self.max_tokens = cfg.max_tokens
        self.temperature = cfg.temperature

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None, **_) -> dict:
        kwargs: dict[str, Any] = dict(
            model=self.model, messages=messages,
            max_tokens=self.max_tokens, temperature=self.temperature,
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
        self.temperature = cfg.temperature

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None, **_) -> dict:
        import json
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        conv = [m for m in messages if m["role"] != "system"]
        kwargs: dict[str, Any] = dict(
            model=self.model, max_tokens=self.max_tokens,
            temperature=self.temperature, messages=conv,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [
                {"name": t["function"]["name"],
                 "description": t["function"].get("description", ""),
                 "input_schema": t["function"].get("parameters", {})}
                for t in tools
            ]
        resp = await self._c.messages.create(**kwargs)
        content_parts, tool_calls = [], []
        for block in resp.content:
            if block.type == "text":
                content_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id, "type": "function",
                    "function": {"name": block.name, "arguments": json.dumps(block.input)},
                })
        usage = {}
        if hasattr(resp, "usage") and resp.usage:
            usage = {
                "prompt_tokens": getattr(resp.usage, "input_tokens", 0),
                "completion_tokens": getattr(resp.usage, "output_tokens", 0),
                "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0),
                "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", 0),
            }
        return {
            "choices": [{"message": {
                "role": "assistant",
                "content": "\n".join(content_parts) or None,
                "tool_calls": tool_calls or None,
            }}],
            "usage": usage,
        }


class GoogleClient:
    def __init__(self, cfg) -> None:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("pip install google-generativeai")
        genai.configure(api_key=cfg.api_key)
        self._model_name = cfg.model or "gemini-1.5-pro"
        self.max_tokens = cfg.max_tokens
        self.temperature = cfg.temperature

    async def chat(self, messages: list[dict], tools: Optional[list[dict]] = None, **_) -> dict:
        import google.generativeai as genai
        model = genai.GenerativeModel(self._model_name)
        prompt = "\n".join(f"{m['role'].upper()}: {m.get('content') or ''}" for m in messages)
        gen_config = genai.types.GenerationConfig(
            max_output_tokens=self.max_tokens, temperature=self.temperature)
        resp = await asyncio.to_thread(model.generate_content, prompt, generation_config=gen_config)
        content = getattr(resp, "text", None) or ""
        return {"choices": [{"message": {"role": "assistant", "content": content, "tool_calls": None}}]}


class LLM:
    """
    Multi-provider LLM router with credential pool, token tracking, and grace call.
    """

    def __init__(self, token_budget: int = 0) -> None:
        cfg = Config.get()
        self._backend = self._build_backend(cfg)
        self._pool: Optional[CredentialPool] = self._build_pool(cfg)
        self._max_retries = max(1, int(cfg.llm.max_retries or MAX_RETRIES))
        self.token_budget = TokenBudget(max_tokens=token_budget)
        self._redact = getattr(cfg, "redact_secrets", False)

    def _build_pool(self, cfg) -> Optional[CredentialPool]:
        provider = (cfg.llm.provider or "").lower()
        if provider in ("mock",):
            return None
        return build_pool_from_config(provider, cfg.llm.api_key)

    def _build_backend(self, cfg):
        provider = (cfg.llm.provider or "").lower().strip()
        if provider == "mock":
            logger.info("Using MockLLM")
            return MockLLM()
        universal_triggers = {"universal", "openrouter", "ollama", "lmstudio", "openai-compat", "groq", "together", "perplexity", ""}
        if cfg.llm.base_url and (not provider or provider in universal_triggers):
            logger.info(f"Universal LLM — {cfg.llm.base_url} model={cfg.llm.model}")
            return UniversalClient(
                base_url=cfg.llm.base_url, api_key=cfg.llm.api_key or "none",
                model=cfg.llm.model, max_tokens=cfg.llm.max_tokens,
                temperature=cfg.llm.temperature, extra_headers=cfg.llm.extra_headers or {},
            )
        if provider == "openai":
            return OpenAIClient(cfg.llm)
        if provider == "anthropic":
            return AnthropicClient(cfg.llm)
        if provider in ("google", "gemini"):
            return GoogleClient(cfg.llm)
        if provider == "mistral":
            from app.llm.mistral_client import MistralClient
            return MistralClient(cfg.llm)
        if provider == "bedrock":
            from app.llm.bedrock_client import BedrockClient
            return BedrockClient(cfg.llm)
        if cfg.llm.base_url:
            return UniversalClient(
                base_url=cfg.llm.base_url, api_key=cfg.llm.api_key or "none",
                model=cfg.llm.model, max_tokens=cfg.llm.max_tokens, temperature=cfg.llm.temperature,
            )
        logger.warning(f"No valid LLM config (provider={provider!r}). Using MockLLM.")
        return MockLLM()

    async def ask(self, messages: list[Message], **kwargs) -> Message:
        raw = [m.to_dict() for m in messages]
        data = await self._call_with_retry(raw, tools=None)
        self.token_budget.record(data)
        return _msg_from_openai(data["choices"][0])

    async def ask_tool(self, messages: list[Message], tools: list[dict], **kwargs) -> Message:
        raw = [m.to_dict() for m in messages]
        data = await self._call_with_retry(raw, tools=tools)
        self.token_budget.record(data)
        return _msg_from_openai(data["choices"][0])

    async def _call_with_retry(self, messages: list[dict], tools: Optional[list[dict]]) -> dict:
        wait = RETRY_BASE_WAIT
        last_err: Optional[Exception] = None

        # Grace call: allow one extra call after budget exhausted for cleanup
        if self.token_budget.is_exhausted:
            if not self.token_budget.use_grace():
                raise TokenLimitExceeded("Token budget exhausted and grace call already used.")

        for attempt in range(1, self._max_retries + 1):
            cred = await self._pool.get() if self._pool else None
            try:
                api_key = cred.api_key if cred else None
                if hasattr(self._backend, "chat"):
                    kwargs_extra: dict[str, Any] = {}
                    if api_key and isinstance(self._backend, UniversalClient):
                        kwargs_extra["api_key"] = api_key
                    result = await self._backend.chat(messages, tools=tools, **kwargs_extra)
                else:
                    result = await self._backend.chat(messages, tools=tools)
                if cred and self._pool:
                    await self._pool.mark_success(cred)
                return result
            except TokenLimitExceeded:
                raise
            except RateLimitError:
                if cred and self._pool:
                    await self._pool.mark_exhausted(cred)
                logger.warning(f"[LLM] Rate limited (attempt {attempt}). Rotating credential. Wait {wait:.1f}s...")
                await asyncio.sleep(wait)
                wait = min(wait * 2 + random.uniform(0, 1), RETRY_MAX_WAIT)
            except Exception as e:
                last_err = e
                if attempt == self._max_retries:
                    raise
                logger.warning(f"[LLM] Error (attempt {attempt}/{self._max_retries}): {e}. Retry in {wait:.1f}s...")
                await asyncio.sleep(wait)
                wait = min(wait * 2 + random.uniform(0, 1), RETRY_MAX_WAIT)

        raise RuntimeError(f"LLM failed after {self._max_retries} retries. Last: {last_err}")


Any = object  # avoid import at module level

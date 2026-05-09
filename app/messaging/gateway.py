from __future__ import annotations
"""MessagingGateway — manages all platform adapters and agent instance cache."""
import asyncio
from collections import OrderedDict
from typing import Callable, Optional
from app.messaging.base import BaseMessagingAdapter, IncomingMessage
from app.messaging.telegram import TelegramAdapter
from app.messaging.discord import DiscordAdapter
from app.messaging.slack import SlackAdapter
from app.logger import logger

_CACHE_SIZE = 128
_IDLE_TTL = 300  # seconds


class MessagingGateway:
    """
    Central gateway that routes messages from any platform to an agent instance.
    Caches up to 128 active agent instances with idle TTL eviction.
    """

    def __init__(self) -> None:
        self._adapters: list[BaseMessagingAdapter] = [
            TelegramAdapter(),
            DiscordAdapter(),
            SlackAdapter(),
        ]
        self._agent_cache: OrderedDict = OrderedDict()
        self._last_active: dict[str, float] = {}
        self._approval_pending: dict[str, dict] = {}

    async def start_all(self, on_message: Optional[Callable] = None) -> None:
        handler = on_message or self._default_handler
        tasks = []
        for adapter in self._adapters:
            await adapter.connect()
            tasks.append(asyncio.create_task(adapter.start(handler)))
        logger.info(f"[Gateway] Started {len(tasks)} platform adapters")

    async def send(self, platform: str, channel_id: str, text: str) -> None:
        for adapter in self._adapters:
            if adapter.platform_name == platform:
                await adapter.send(channel_id, text)
                return
        logger.warning(f"[Gateway] No adapter for platform: {platform}")

    async def _default_handler(self, msg: IncomingMessage) -> None:
        logger.info(f"[Gateway] Message from {msg.platform}/{msg.user_id}: {msg.text[:80]}")
        agent = self._get_or_create_agent(msg.session_key)
        try:
            result = await agent.run(msg.text)
            await self.send(msg.platform, msg.channel_id, result[:4000])
        except Exception as e:
            logger.error(f"[Gateway] Agent error: {e}")
            await self.send(msg.platform, msg.channel_id, f"Error: {e}")

    def _get_or_create_agent(self, session_key: str):
        import time
        from app.agent.manus import Manus
        now = time.monotonic()

        # Evict idle agents
        evict = [k for k, t in self._last_active.items() if now - t > _IDLE_TTL]
        for k in evict:
            self._agent_cache.pop(k, None)
            self._last_active.pop(k, None)

        # LRU eviction if over cache size
        while len(self._agent_cache) >= _CACHE_SIZE:
            self._agent_cache.popitem(last=False)

        if session_key not in self._agent_cache:
            self._agent_cache[session_key] = Manus()
        self._last_active[session_key] = now
        return self._agent_cache[session_key]

    async def stop_all(self) -> None:
        for adapter in self._adapters:
            await adapter.disconnect()

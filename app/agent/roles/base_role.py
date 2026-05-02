from __future__ import annotations

"""
BaseRole — foundation for all multi-agent roles.

Each role implements the Observe → Think → Act → Publish loop:
  Observe  — read incoming messages from the bus
  Think    — reason about the goal using its specialist prompt
  Act      — call tools or generate artefacts
  Publish  — push output messages back to the bus for downstream roles
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Message bus
# ---------------------------------------------------------------------------

@dataclass
class RoleMessage:
    from_role: str
    to_role: str           # "*" = broadcast to all
    content: str
    artefact: Optional[Any] = None   # Structured output (PRD, design doc, code, etc.)
    ts: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return f"[{self.from_role} → {self.to_role}] {self.content[:120]}"


class RoleMessageBus:
    """
    Simple in-process async message bus. Each role subscribes and
    publishes messages. Supports broadcast ("*") and direct routing.
    """

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue] = {}

    def subscribe(self, role_name: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues[role_name] = q
        return q

    async def publish(self, message: RoleMessage) -> None:
        if message.to_role == "*":
            for name, q in self._queues.items():
                if name != message.from_role:
                    await q.put(message)
        elif message.to_role in self._queues:
            await self._queues[message.to_role].put(message)

    async def drain(self, role_name: str, timeout: float = 0.1) -> list[RoleMessage]:
        """Collect all pending messages for a role without blocking."""
        q = self._queues.get(role_name)
        if not q:
            return []
        msgs: list[RoleMessage] = []
        while True:
            try:
                msg = q.get_nowait()
                msgs.append(msg)
            except asyncio.QueueEmpty:
                break
        return msgs


# ---------------------------------------------------------------------------
# BaseRole
# ---------------------------------------------------------------------------

class BaseRole(ABC):
    """
    Abstract base for all specialist roles.
    """

    role_name: str = "base"
    role_description: str = "Generic role"
    specialist_prompt: str = ""

    def __init__(self, bus: RoleMessageBus) -> None:
        self.bus = bus
        self._inbox = bus.subscribe(self.role_name)
        self._done = False

    # ------------------------------------------------------------------
    # Observe → Think → Act → Publish
    # ------------------------------------------------------------------

    async def run(self, initial_input: str) -> str:
        """Entry point. Run the full OTAP loop until done."""
        from app.llm.llm import LLM
        from app.memory.short_term import ShortTermMemory
        from app.schema import Message

        self.llm = LLM()
        self.memory = ShortTermMemory()
        self.memory.add(Message.system(
            self._build_system_prompt()
        ))

        # Observe: seed from initial input
        self.memory.add(Message.user(initial_input))

        result = await self._think_act_publish(initial_input)
        return result

    @abstractmethod
    async def _think_act_publish(self, context: str) -> str:
        """
        Role-specific implementation of Think → Act → Publish.
        Must call self.bus.publish() with the output RoleMessage.
        Must return the primary output string.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        identity = (
            "You are ManusClaw, an autonomous AI engine created by The-JDdev (SHS Shobuj). "
            "You do not identify as any base LLM provider. You are ManusClaw.\n\n"
        )
        return identity + self.specialist_prompt

    async def _ask_llm(self, extra_context: str = "") -> str:
        from app.schema import Message
        if extra_context:
            self.memory.add(Message.user(extra_context))
        response = await self.llm.ask(self.memory.messages)
        self.memory.add(response)
        return response.content or ""

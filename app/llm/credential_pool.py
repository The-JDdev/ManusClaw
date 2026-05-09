from __future__ import annotations

"""
CredentialPool — per-provider API key pool with priority ordering and auto-rotation.

Each provider can have multiple credentials ranked by priority (lower = higher priority).
When a key is exhausted (RateLimitError) it is deprioritised and the next key is tried.
Keys auto-recover after a cooldown window.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from app.logger import logger


@dataclass
class Credential:
    api_key: str
    priority: int = 0
    exhausted_until: float = 0.0
    use_count: int = 0
    fail_count: int = 0

    @property
    def is_available(self) -> bool:
        return time.monotonic() >= self.exhausted_until

    def mark_exhausted(self, cooldown_s: float = 60.0) -> None:
        self.exhausted_until = time.monotonic() + cooldown_s
        self.fail_count += 1
        logger.warning(f"[CredentialPool] Key ...{self.api_key[-6:]} exhausted, cooling {cooldown_s:.0f}s")

    def mark_success(self) -> None:
        self.use_count += 1
        self.exhausted_until = 0.0


class CredentialPool:
    """
    Thread-safe pool of API keys for a single provider.
    Keys are tried in priority order; exhausted keys are skipped until cooled.
    """

    def __init__(self, credentials: list[dict], cooldown_s: float = 60.0) -> None:
        self._creds: list[Credential] = sorted(
            [Credential(api_key=c["api_key"], priority=c.get("priority", 0)) for c in credentials],
            key=lambda c: c.priority,
        )
        self._cooldown = cooldown_s
        self._lock = asyncio.Lock()
        self._current_idx = 0

    @classmethod
    def from_env(cls, env_keys: list[str], cooldown_s: float = 60.0) -> "CredentialPool":
        """Build a pool from a list of API key strings."""
        return cls(
            [{"api_key": k, "priority": i} for i, k in enumerate(env_keys) if k],
            cooldown_s=cooldown_s,
        )

    async def get(self) -> Optional[Credential]:
        """Return the highest-priority available credential, or None if all exhausted."""
        async with self._lock:
            available = [c for c in self._creds if c.is_available]
            if not available:
                return None
            return available[0]

    async def mark_exhausted(self, cred: Credential) -> None:
        async with self._lock:
            cred.mark_exhausted(self._cooldown)

    async def mark_success(self, cred: Credential) -> None:
        async with self._lock:
            cred.mark_success()

    @property
    def size(self) -> int:
        return len(self._creds)

    @property
    def available_count(self) -> int:
        return sum(1 for c in self._creds if c.is_available)


def build_pool_from_config(provider: str, primary_key: Optional[str] = None) -> Optional[CredentialPool]:
    """
    Build a CredentialPool from environment variables.
    Looks for OPENAI_API_KEY, OPENAI_API_KEY_2, OPENAI_API_KEY_3, etc.
    """
    import os
    prefix_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "bedrock": "AWS_ACCESS_KEY_ID",
        "google": "GOOGLE_API_KEY",
    }
    prefix = prefix_map.get(provider.lower())
    if not prefix:
        if primary_key:
            return CredentialPool.from_env([primary_key])
        return None

    keys: list[str] = []
    if primary_key:
        keys.append(primary_key)
    # Also try OPENAI_API_KEY_2, _3, etc.
    for i in range(2, 10):
        k = os.getenv(f"{prefix}_{i}", "")
        if k and k not in keys:
            keys.append(k)

    if not keys:
        env_k = os.getenv(prefix, "")
        if env_k:
            keys.append(env_k)

    return CredentialPool.from_env(keys) if keys else None

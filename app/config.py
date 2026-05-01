from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = "mock"
    model: str = "gpt-4o"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.0
    max_retries: int = 6
    timeout: int = 120


class BrowserConfig(BaseModel):
    headless: bool = True
    disable_security: bool = False
    max_content_length: int = 10000


class SearchConfig(BaseModel):
    engines: list[str] = Field(default_factory=lambda: ["google", "duckduckgo", "baidu", "bing"])
    max_results: int = 10


class SandboxConfig(BaseModel):
    enabled: bool = False
    docker_image: str = "python:3.11-slim"
    memory_limit: str = "256m"
    timeout: int = 30


class MCPServerDef(BaseModel):
    name: str
    transport: str = "stdio"
    command: Optional[str] = None
    args: list[str] = Field(default_factory=list)
    url: Optional[str] = None


class RunFlowConfig(BaseModel):
    enable_data_analysis: bool = False
    timeout: int = 3600


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    mcp_servers: list[MCPServerDef] = Field(default_factory=list)
    runflow: RunFlowConfig = Field(default_factory=RunFlowConfig)
    workspace_dir: str = "workspace"
    max_steps: int = 30


class Config:
    _instance: Optional["Config"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, path: str = "config.toml") -> None:
        self._data: AppConfig = self._load(path)

    @classmethod
    def get(cls, path: str = "config.toml") -> "Config":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(path)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None

    def _load(self, path: str) -> AppConfig:
        raw: dict[str, Any] = {}
        p = Path(path)
        if p.exists() and tomllib is not None:
            with open(p, "rb") as f:
                raw = tomllib.load(f)

        cfg = AppConfig.model_validate(raw) if raw else AppConfig()

        # Environment variable overrides for secrets
        if not cfg.llm.api_key:
            cfg.llm.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not cfg.llm.base_url:
            cfg.llm.base_url = os.getenv("LLM_BASE_URL")

        # Force mock if no real provider configured
        if cfg.llm.provider not in ("mock",) and not cfg.llm.api_key:
            cfg.llm.provider = "mock"

        return cfg

    @property
    def llm(self) -> LLMConfig:
        return self._data.llm

    @property
    def browser(self) -> BrowserConfig:
        return self._data.browser

    @property
    def search(self) -> SearchConfig:
        return self._data.search

    @property
    def sandbox(self) -> SandboxConfig:
        return self._data.sandbox

    @property
    def mcp_servers(self) -> list[MCPServerDef]:
        return self._data.mcp_servers

    @property
    def runflow(self) -> RunFlowConfig:
        return self._data.runflow

    @property
    def workspace_dir(self) -> str:
        return self._data.workspace_dir

    @property
    def max_steps(self) -> int:
        return self._data.max_steps

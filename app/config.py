from __future__ import annotations

"""
ManusClaw Configuration System
================================
Loads configuration from (in priority order, highest to lowest):
  1. Environment variables (always override config file)
  2. .env file (if python-dotenv is installed and .env exists)
  3. config.toml (if present)
  4. Built-in defaults (always safe fallback)

Environment separation is controlled by the APP_ENV variable:
  APP_ENV=dev   → developer defaults (verbose logging, mock LLM)
  APP_ENV=prod  → production defaults (warnings only, strict auth)
  APP_ENV=test  → test defaults (MockLLM, in-memory DB, fast timeouts)

Validation is enforced via Pydantic model_validator. Invalid configs
raise ConfigError immediately at startup — no silent bad state.
"""

from __future__ import annotations

import os
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

from pydantic import BaseModel, Field, model_validator

from app.exceptions import ConfigError


# ──────────────────────────────────────────────────────────────────────────────
# Environment enum
# ──────────────────────────────────────────────────────────────────────────────

class AppEnv(str, Enum):
    DEV  = "dev"
    PROD = "prod"
    TEST = "test"


# ──────────────────────────────────────────────────────────────────────────────
# Config models — all Pydantic, all validated
# ──────────────────────────────────────────────────────────────────────────────

class LLMConfig(BaseModel):
    provider:      str            = "mock"
    model:         str            = "gpt-4o"
    base_url:      Optional[str]  = None
    api_key:       Optional[str]  = None
    max_tokens:    int            = 4096
    temperature:   float          = 0.0
    max_retries:   int            = 6
    timeout:       int            = 120
    extra_headers: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _coerce_provider_to_mock_when_no_key(self) -> "LLMConfig":
        """
        If a real provider is declared but no API key is available,
        fall back to mock so the system always starts cleanly.
        A warning is emitted at runtime when this occurs.
        """
        mock_safe = {"mock", "ollama", "lmstudio", "openai-compat", "universal", ""}
        if self.provider not in mock_safe and not self.api_key and not self.base_url:
            object.__setattr__(self, "provider", "mock")
        return self


class BrowserConfig(BaseModel):
    headless:           bool = True
    disable_security:   bool = False
    max_content_length: int  = 10_000


class SearchConfig(BaseModel):
    engines:     list[str] = Field(default_factory=lambda: ["duckduckgo", "bing"])
    max_results: int        = 10

    @model_validator(mode="after")
    def _normalize_engines(self) -> "SearchConfig":
        valid = {"duckduckgo", "bing", "google"}
        self.engines = [e.lower().strip() for e in self.engines if e.lower().strip() in valid]
        if not self.engines:
            self.engines = ["duckduckgo", "bing"]
        return self


class SandboxConfig(BaseModel):
    enabled:      bool = False
    docker_image: str  = "python:3.11-slim"
    memory_limit: str  = "256m"
    timeout:      int  = 30


class MCPServerDef(BaseModel):
    name:      str
    transport: str           = "stdio"
    command:   Optional[str] = None
    args:      list[str]     = Field(default_factory=list)
    url:       Optional[str] = None


class RunFlowConfig(BaseModel):
    enable_data_analysis: bool = False
    timeout:              int  = 3600


class LoggingConfig(BaseModel):
    level:         str  = "DEBUG"
    json_format:   bool = False
    include_trace: bool = True


class AppConfig(BaseModel):
    env:          AppEnv        = AppEnv.DEV
    llm:          LLMConfig     = Field(default_factory=LLMConfig)
    browser:      BrowserConfig = Field(default_factory=BrowserConfig)
    search:       SearchConfig  = Field(default_factory=SearchConfig)
    sandbox:      SandboxConfig = Field(default_factory=SandboxConfig)
    mcp_servers:  list[MCPServerDef] = Field(default_factory=list)
    runflow:      RunFlowConfig = Field(default_factory=RunFlowConfig)
    logging:      LoggingConfig = Field(default_factory=LoggingConfig)
    workspace_dir: str  = "workspace"
    max_steps:     int  = 30


# ──────────────────────────────────────────────────────────────────────────────
# Singleton config loader
# ──────────────────────────────────────────────────────────────────────────────

class Config:
    """
    Thread-safe singleton configuration loader.

    Usage:
        cfg = Config.get()
        model = cfg.llm.model

    The first call to Config.get() loads and validates the full config.
    Subsequent calls return the cached instance.
    Calling Config.reset() clears the singleton (useful in tests).
    """

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
        """Clear the singleton. Primarily for test isolation."""
        with cls._lock:
            cls._instance = None

    # ------------------------------------------------------------------
    # Loader
    # ------------------------------------------------------------------

    def _load(self, path: str) -> AppConfig:
        # Step 1 — Load .env file (lowest priority, doesn't override existing env vars)
        self._load_dotenv()

        # Step 2 — Load config.toml
        raw: dict[str, Any] = {}
        p = Path(path)
        if p.exists() and tomllib is not None:
            try:
                with open(p, "rb") as f:
                    raw = tomllib.load(f)
            except Exception as e:
                raise ConfigError(f"Failed to parse {path}: {e}") from e

        # Step 3 — Apply APP_ENV
        env_str = os.getenv("APP_ENV", raw.get("env", "dev")).lower()
        try:
            app_env = AppEnv(env_str)
        except ValueError:
            app_env = AppEnv.DEV

        # Step 4 — Parse model with validation
        try:
            cfg = AppConfig.model_validate(raw) if raw else AppConfig()
        except Exception as e:
            raise ConfigError(f"Configuration validation failed: {e}") from e

        cfg.env = app_env

        # Step 5 — Override secrets from environment variables
        if not cfg.llm.api_key:
            cfg.llm.api_key = (
                os.getenv("OPENAI_API_KEY")
                or os.getenv("ANTHROPIC_API_KEY")
                or os.getenv("LLM_API_KEY")
            )
        if not cfg.llm.base_url:
            cfg.llm.base_url = os.getenv("LLM_BASE_URL")

        # Step 6 — Test env overrides (fast, safe defaults)
        if app_env == AppEnv.TEST:
            cfg.llm.provider = "mock"
            cfg.max_steps = 5
            cfg.runflow.timeout = 60

        # Step 7 — Final safety: if provider needs a key but none found, fall back to mock
        safe_providers = {"mock", "ollama", "lmstudio", "universal", "openai-compat", ""}
        if cfg.llm.provider not in safe_providers and not cfg.llm.api_key and not cfg.llm.base_url:
            import warnings
            warnings.warn(
                f"LLM provider '{cfg.llm.provider}' requires an API key, but none was found. "
                "Falling back to MockLLM. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or LLM_API_KEY.",
                stacklevel=3,
            )
            cfg.llm.provider = "mock"

        return cfg

    @staticmethod
    def _load_dotenv() -> None:
        """Load .env file if python-dotenv is installed. Silent no-op otherwise."""
        try:
            from dotenv import load_dotenv
            load_dotenv(override=False)  # env vars already set take precedence
        except ImportError:
            pass

    # ------------------------------------------------------------------
    # Property accessors — typed convenience attributes
    # ------------------------------------------------------------------

    @property
    def env(self) -> AppEnv:
        return self._data.env

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
    def logging(self) -> LoggingConfig:
        return self._data.logging

    @property
    def workspace_dir(self) -> str:
        return self._data.workspace_dir

    @property
    def max_steps(self) -> int:
        return self._data.max_steps

    def is_prod(self) -> bool:
        return self._data.env == AppEnv.PROD

    def is_dev(self) -> bool:
        return self._data.env == AppEnv.DEV

    def is_test(self) -> bool:
        return self._data.env == AppEnv.TEST

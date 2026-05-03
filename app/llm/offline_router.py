"""
Offline / Local LLM Router
Supports:
  - Ollama        (http://localhost:11434)
  - LMStudio      (http://localhost:1234/v1  — OpenAI-compatible)
  - text-gen-webui (http://localhost:5000/v1 — OpenAI-compatible)
  - HuggingFace Inference API / Spaces
  - Direct GGUF   (llama-cpp-python, fully offline, no internet)
"""
from __future__ import annotations
import json
from typing import Iterator, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# GGUF (llama-cpp-python)
# ─────────────────────────────────────────────────────────────────────────────

def _load_gguf(model_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0):
    try:
        from llama_cpp import Llama
    except ImportError:
        raise ImportError(
            "llama-cpp-python not installed.\n"
            "Install: pip install llama-cpp-python\n"
            "GPU:     CMAKE_ARGS='-DLLAMA_CUBLAS=on' pip install llama-cpp-python"
        )
    return Llama(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers,
                 verbose=False)


class GGUFRouter:
    """Run a local .gguf file with zero internet dependency."""

    def __init__(self, model_path: str, n_ctx: int = 4096,
                 n_gpu_layers: int = 0):
        self.llm = _load_gguf(model_path, n_ctx, n_gpu_layers)

    def chat(self, messages: List[dict], max_tokens: int = 2048,
             temperature: float = 0.7, **_) -> str:
        resp = self.llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp["choices"][0]["message"]["content"]

    def stream(self, messages: List[dict], max_tokens: int = 2048,
               temperature: float = 0.7, **_) -> Iterator[str]:
        for chunk in self.llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        ):
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                yield delta["content"]


# ─────────────────────────────────────────────────────────────────────────────
# Ollama
# ─────────────────────────────────────────────────────────────────────────────

class OllamaRouter:
    """
    Direct Ollama integration (REST /api/chat).
    Works with any model pulled via `ollama pull <model>`.
    """

    def __init__(self, model: str = "llama3.2:3b",
                 base_url: str = "http://localhost:11434"):
        self.model = model
        self.base = base_url.rstrip("/")
        try:
            import httpx
            self._httpx = True
        except ImportError:
            self._httpx = False

    def _post(self, endpoint: str, payload: dict) -> dict:
        import json as _j
        url = f"{self.base}{endpoint}"
        data = _j.dumps(payload).encode()
        if self._httpx:
            import httpx
            r = httpx.post(url, content=data,
                           headers={"Content-Type": "application/json"},
                           timeout=None)
            return r.json()
        else:
            import urllib.request
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                return _j.loads(resp.read().decode())

    def chat(self, messages: List[dict], max_tokens: int = 2048,
             temperature: float = 0.7, **_) -> str:
        resp = self._post("/api/chat", {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        })
        return resp["message"]["content"]

    def list_models(self) -> List[str]:
        resp = self._post("/api/tags", {})
        return [m["name"] for m in resp.get("models", [])]


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI-compatible (LMStudio, text-gen-webui, Groq, Together, etc.)
# ─────────────────────────────────────────────────────────────────────────────

class OpenAICompatRouter:
    """
    Generic OpenAI-compatible endpoint.
    LMStudio:      base_url="http://localhost:1234/v1",  api_key="none"
    text-gen-webui:base_url="http://localhost:5000/v1",  api_key="none"
    Groq:          base_url="https://api.groq.com/openai/v1", api_key=<key>
    OpenRouter:    base_url="https://openrouter.ai/api/v1",   api_key=<key>
    """

    def __init__(self, model: str, base_url: str,
                 api_key: str = "none", timeout: int = None):
        self.model = model
        self.base = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.timeout = timeout

    def chat(self, messages: List[dict], max_tokens: int = 2048,
             temperature: float = 0.7, **_) -> str:
        try:
            import httpx
            r = httpx.post(
                f"{self.base}/chat/completions",
                headers=self.headers,
                json={"model": self.model, "messages": messages,
                      "max_tokens": max_tokens, "temperature": temperature},
                timeout=self.timeout,
            )
            return r.json()["choices"][0]["message"]["content"]
        except ImportError:
            import urllib.request, json as _j
            data = _j.dumps({
                "model": self.model, "messages": messages,
                "max_tokens": max_tokens, "temperature": temperature,
            }).encode()
            req = urllib.request.Request(
                f"{self.base}/chat/completions",
                data=data, headers=self.headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return _j.loads(resp.read())["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────────────────────────────────────
# HuggingFace Inference API / Spaces
# ─────────────────────────────────────────────────────────────────────────────

class HuggingFaceRouter:
    """
    HuggingFace Inference API (serverless) or Inference Endpoints (dedicated).
    model examples:
      "meta-llama/Meta-Llama-3-8B-Instruct"
      "HuggingFaceH4/zephyr-7b-beta"
    Or a Spaces URL: "https://your-space.hf.space"
    """

    def __init__(self, model: str, hf_token: str = None,
                 endpoint_url: str = None):
        self.token = hf_token or ""
        self.headers = {"Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"}
        if endpoint_url:
            self.url = endpoint_url.rstrip("/") + "/v1/chat/completions"
        else:
            self.url = (
                f"https://api-inference.huggingface.co/models/{model}"
                "/v1/chat/completions"
            )

    def chat(self, messages: List[dict], max_tokens: int = 1024,
             temperature: float = 0.7, **_) -> str:
        try:
            import httpx
            r = httpx.post(self.url, headers=self.headers,
                           json={"messages": messages,
                                 "max_tokens": max_tokens,
                                 "temperature": temperature},
                           timeout=120)
            return r.json()["choices"][0]["message"]["content"]
        except ImportError:
            import urllib.request, json as _j
            data = _j.dumps({"messages": messages, "max_tokens": max_tokens,
                             "temperature": temperature}).encode()
            req = urllib.request.Request(
                self.url, data=data, headers=self.headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                return _j.loads(resp.read())["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────────────────────────────────────
# Universal factory
# ─────────────────────────────────────────────────────────────────────────────

def build_offline_router(config: dict):
    """
    Build the right offline router from config dict.

    GGUF (fully offline):
        {"provider": "gguf", "model_path": "/path/to/model.gguf",
         "n_ctx": 4096, "n_gpu_layers": 0}

    Ollama:
        {"provider": "ollama", "model": "llama3.2:3b",
         "base_url": "http://localhost:11434"}

    LMStudio / text-gen-webui / any OpenAI-compat:
        {"provider": "openai_compat", "model": "local-model",
         "base_url": "http://localhost:1234/v1", "api_key": "none"}

    HuggingFace:
        {"provider": "huggingface",
         "model": "HuggingFaceH4/zephyr-7b-beta",
         "hf_token": "hf_xxx"}
    """
    p = config.get("provider", "").lower()
    if p == "gguf":
        return GGUFRouter(
            model_path=config["model_path"],
            n_ctx=config.get("n_ctx", 4096),
            n_gpu_layers=config.get("n_gpu_layers", 0),
        )
    if p == "ollama":
        return OllamaRouter(
            model=config.get("model", "llama3.2:3b"),
            base_url=config.get("base_url", "http://localhost:11434"),
        )
    if p in ("openai_compat", "lmstudio", "textgen", "groq", "openrouter"):
        return OpenAICompatRouter(
            model=config.get("model", "local-model"),
            base_url=config.get("base_url", "http://localhost:1234/v1"),
            api_key=config.get("api_key", "none"),
            timeout=config.get("timeout"),
        )
    if p in ("huggingface", "hf"):
        return HuggingFaceRouter(
            model=config.get("model", ""),
            hf_token=config.get("hf_token") or config.get("api_key", ""),
            endpoint_url=config.get("endpoint_url"),
        )
    raise ValueError(
        f"Unknown offline provider '{p}'. "
        "Valid: gguf | ollama | openai_compat | huggingface"
    )

<div align="center">
<pre style="font-weight: bold; background: transparent; border: none;">
<span style="color: #ff0000;">███╗   ███╗ █████╗ ███╗   ██╗██╗   ██╗███████╗ ██████╗██╗      █████╗ ██╗    ██╗</span>
<span style="color: #ff4500;">████╗ ████║██╔══██╗████╗  ██║██║   ██║██╔════╝██╔════╝██║     ██╔══██╗██║    ██║</span>
<span style="color: #ff8c00;">██╔████╔██║███████║██╔██╗ ██║██║   ██║███████╗██║     ██║     ███████║██║ █╗ ██║</span>
<span style="color: #ffa500;">██║╚██╔╝██║██╔══██║██║╚██╗██║██║   ██║╚════██║██║     ██║     ██╔══██║██║███╗██║</span>
<span style="color: #ffd700;">██║ ╚═╝ ██║██║  ██║██║ ╚████║╚██████╔╝███████║╚██████╗███████╗██║  ██║╚███╔███╔╝</span>
<span style="color: #ffff00;">╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝</span>
</pre>
</div>

# 🦅 ManusClaw v4.0 — The Ultimate Autonomous AI Ecosystem

### *Not a wrapper. Not a demo. A full OS-level, multi-agent, self-improving execution engine with skills, memory, and multi-provider intelligence.*

---

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-4.0.0-red?style=for-the-badge)](https://github.com/The-JDdev/ManusClaw)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Termux%20%7C%20Docker-orange?style=for-the-badge)]()
[![Offline](https://img.shields.io/badge/Offline%20LLM-Supported-purple?style=for-the-badge)]()
[![Multi-Agent](https://img.shields.io/badge/Multi--Agent-DAG%20Orchestrated-cyan?style=for-the-badge)]()
[![Stars](https://img.shields.io/github/stars/The-JDdev/ManusClaw?style=for-the-badge&logo=github)](https://github.com/The-JDdev/ManusClaw/stargazers)
[![Forks](https://img.shields.io/github/forks/The-JDdev/ManusClaw?style=for-the-badge&logo=github)](https://github.com/The-JDdev/ManusClaw/network)

**Created by [The-JDdev (SHS Shobuj)](https://github.com/The-JDdev)** — Built from Bangladesh, on a smartphone. 🇧🇩

[🌐 Web Interface](https://the-jddev.github.io/ManusClaw) · [🐛 Report a Bug](https://github.com/The-JDdev/ManusClaw/issues) · [💬 Telegram](https://t.me/aamoviesadmin) · [📘 Facebook](https://fb.com/itsshsshobuj)

</div>

---


---

## 🚀 What's New in v4.0 — Hermes Integration

> *v4.0 transforms ManusClaw from a powerful agent into a self-improving ecosystem — skills that compound, memory that persists, and infrastructure that scales.*

### ⚡ Multi-Provider LLM with Credential Pool
- **6 providers**: OpenAI, Anthropic, Google Gemini, Mistral AI, AWS Bedrock, + any OpenAI-compatible endpoint (Groq, Together, OpenRouter, Ollama, LM Studio)
- **Credential Pool**: multiple API keys per provider with priority ordering, auto-rotation on rate-limit, configurable cooldown recovery
- **Token Budget**: tracks input/output/cache/reasoning tokens separately per session with a **grace call** — one final cleanup call after budget exhaustion
- **Secret Redaction**: automatically scrubs API keys/tokens from all log output

### 🧠 Skills System (Auto-Learning Agent)
- Skills are Markdown files with YAML frontmatter stored in `~/.manusclaw/skills/`
- Injected as user messages (not system prompt) — **preserves prompt cache hits**
- **Auto-suggest**: after 5+ tool calls, agent suggests capturing the workflow as a skill
- **Built-in library**: `github_workflow`, `deep_research`, `devops_deploy`, `mlops_training`, `code_review`, `data_analysis`
- Full CRUD via `skill_manager` tool: create, patch, delete, list during live sessions

### 💾 FTS5 Cross-Session Memory
- SQLite **FTS5 virtual tables** over all messages and tool calls
- `cross_session_search` tool: find past solutions, recall previous work, avoid repeating failures
- `memory` tool: read/write `MEMORY.md` (facts) and `USER.md` (preferences) — persists across all sessions
- **Session branching**: fork any session with `parent_session_id` for parallel exploration
- **Context compression**: summarize old messages when approaching token limits — chain sessions infinitely

### 🔧 New Tools
| Tool | Description |
|------|-------------|
| `memory` | Read/write `MEMORY.md` and `USER.md` |
| `skill_manager` | Create/patch/delete/list skills live |
| `cross_session_search` | FTS5 search across all past sessions |
| `delegate` | Spawn isolated subagent in thread pool |
| `image_generate` | FAL.ai image generation (mock fallback) |
| `node_execute` | Run Node.js / JavaScript in isolation |

### 📡 Messaging Gateway
- **Telegram**, **Discord**, **Slack** adapters — functional when tokens set, graceful stub otherwise
- LRU agent cache (128 slots, 300s idle TTL) — each user gets their own persistent agent
- Route cron job outputs directly to any platform channel

### ⏰ Cron Scheduler
- croniter-based job runner persisted to `~/.manusclaw/cron_jobs.yaml`
- Schedule any agent prompt to run on any cron expression
- Delivers results to messaging platforms or custom callbacks

### 🎨 Premium CLI (prompt_toolkit + Rich)
- Animated spinner, Rich Markdown rendering, role-emoji prefixes
- **4 built-in skins**: `default` (gold), `ares` (red), `mono` (white), `slate` (blue)
- Custom YAML skins at `~/.manusclaw/skins/<name>.yaml`
- **Slash commands**: `/model`, `/skills`, `/tools`, `/memory`, `/compress`, `/new`, `/branch`, `/resume`, `/help`, `/exit`
- Persistent input history at `~/.manusclaw/.cli_history`

### 🗂️ Named Config Profiles
```bash
MANUSCLAW_PROFILE=work python -m app.cli
# Loads: ~/.manusclaw/profiles/work/config.yaml + .env
```

### 🧪 Production Test Suite
- 8 test files, **pytest-asyncio** + **pytest-xdist** (`-n 4` parallel workers)
- Covers: agent loop, tool dispatch, FTS5/branching/compression, credential rotation, skills CRUD, PAORR loop
- `pytest -n 4` — run all tests in 4 parallel workers

---
## 🔥 What is ManusClaw?

**ManusClaw is not a ChatGPT wrapper.** It is not a prompt template. It is not a toy.

ManusClaw is a **production-grade, uncensored, autonomous AI agent ecosystem** written entirely in Python. It gives you a self-reasoning, self-correcting, multi-agent AI pipeline that can:

- 💻 **Execute real shell commands** — bash, PowerShell, Termux — with a persistent session that holds state across calls
- 🐍 **Run isolated Python code** — in its own subprocess with 2 GB memory protection, full imports, full output, no truncation
- 🌐 **Browse the web** — real Playwright-driven browser, clicks, screenshots, form submission
- 🔍 **Search the internet** — DuckDuckGo + Bing with automatic fallback chain and retry backoff
- 📁 **Edit any file** — `str_replace_editor` with surgical precision (view, create, overwrite, patch)
- 🔗 **Control external platforms** — GitHub, Vercel, WordPress, HuggingFace, Netlify, Discord, Telegram, and any REST API
- 🧠 **Remember across sessions** — SQLite-backed audit log + FTS5-indexed long-term RAG memory
- 👥 **Deploy multi-agent pipelines** — ProductManager → Architect → Engineer → QA, DAG-orchestrated with Kahn's topological sort
- 🤖 **Route to any LLM** — OpenAI, Anthropic, Google, Ollama, LMStudio, OpenRouter, Groq, Together, GGUF files, HuggingFace — all through one universal config

It runs on **Linux, macOS, Windows, Docker, and Termux (Android)**. It ships with a **desktop GUI** (Flet), a **FastAPI WebSocket server**, and a **global CLI command** that wakes the beast from any terminal on Earth.

---

## 📋 Table of Contents

1. [🧠 The Multi-Agent Brain](#-the-metagpt-style-multi-agent-brain)
2. [🌍 Universal & Offline LLM Routing](#-universal--offline-llm-routing)
3. [💾 SQLite Memory & 3-Tier Permissions](#-sqlite-memory--3-tier-permission-system)
4. [💻 The Four Deployment Modes](#-the-four-deployment-modes-the-quartet)
5. [🚀 The Global Wake-Up Command](#-the-global-wake-up-command)
6. [⚡ Quick Start](#-quick-start)
7. [⚙️ Configuration Reference](#️-configuration-reference)
8. [🛠️ The Lethal Tool Arsenal](#️-the-lethal-tool-arsenal)
9. [🎮 Platform Domination](#-platform-domination-platformcontroltool)
10. [📡 Dual UI: Terminal & Web](#-dual-ui-terminal--web)
11. [🏗️ Architecture Deep Dive](#️-architecture-deep-dive)
12. [🔧 Bug Fixes & Improvements (v3.2 Patch)](#-bug-fixes--improvements-v32-patch)
13. [💌 A Note from the Founder](#-a-note-from-the-founder)
14. [💎 Donation Vault](#-donation-vault)

---

## 🧠 The MetaGPT-Style Multi-Agent Brain

ManusClaw implements a **full DAG-orchestrated multi-agent pipeline** modelled on the MetaGPT philosophy but rebuilt from scratch with clean, auditable Python. Four specialist roles execute in strict dependency order, each building on the verified output of the last.

### The Four Roles

```
┌─────────────────┐     PRD      ┌───────────────┐   Design Plan  ┌────────────────┐  Verified Code  ┌──────────────┐
│  ProductManager │ ──────────▶  │   Architect   │ ─────────────▶ │   Engineer     │ ──────────────▶ │     QA       │
│                 │              │               │                 │                │                 │              │
│  Writes PRD:    │              │  Writes:      │                 │  Executes:     │                 │  Validates:  │
│  - Objective    │              │  - Sys design │                 │  - Each TASK-N │                 │  - Each AC   │
│  - Scope        │              │  - File tree  │                 │  - Runs code   │                 │  - PASS/FAIL │
│  - Criteria     │              │  - DAG plan   │                 │  - Verifies    │                 │  - QA Report │
│  - Priorities   │              │  - Tech stack │                 │  - Saves files │                 │  - Verdict   │
└─────────────────┘              └───────────────┘                 └────────────────┘                 └──────────────┘
```

### Role Details

#### 🗂️ ProductManagerRole — `app/agent/roles/product_manager.py`

The first agent to receive your goal. It produces a **structured PRD (Product Requirements Document)** with six mandatory sections:

| Section | Content |
|---|---|
| `OBJECTIVE` | One crisp sentence defining the deliverable |
| `IN SCOPE` | Bullet list of every feature being built |
| `OUT OF SCOPE` | Hard boundaries — what will NOT be built |
| `ACCEPTANCE CRITERIA` | Numbered, measurable conditions for success |
| `TECHNICAL CONSTRAINTS` | Language, framework, runtime requirements |
| `PRIORITY ORDER` | Features ranked P0 (critical) → P1 → P2 |

Once the PRD is complete, it **publishes** the document to the async `RoleMessageBus`, which the Architect subscribes to.

#### 🏛️ ArchitectRole — `app/agent/roles/architect.py`

Receives the PRD from the bus and produces a **concrete, actionable system design** with six sections:

| Section | Content |
|---|---|
| `SYSTEM OVERVIEW` | High-level architecture in prose |
| `FILE STRUCTURE` | Exact directory tree with file purposes |
| `COMPONENT MAP` | Each component's responsibility and interface |
| `DATA FLOW` | How data moves between components, step by step |
| `TECHNOLOGY STACK` | Exact libraries and versions to use |
| `IMPLEMENTATION PLAN` | DAG task list in `[TASK-N] <action> \| File: <path> \| Deps: [TASK-X, ...]` format |

The implementation plan is a **real directed acyclic graph** — every task declares its dependencies, and the Engineer executes them in the correct topological order.

#### 🔧 EngineerRole — `app/agent/roles/engineer.py`

The Engineer **does not just write code**. It delegates to a full **Manus agent** instance — which means it has access to the complete tool arsenal: `python_execute`, `bash`, `str_replace_editor`, `browser_use`, `web_search`, and more. Its loop for every task:

```
1. Read the task description from the Architect's plan
2. Choose the correct tool (str_replace_editor → write, python_execute/bash → run)
3. Execute the code
4. Verify: does the output match the acceptance criterion?
5. If FAIL: debug, fix, re-run (up to 3 self-correction attempts)
6. Mark COMPLETE only when verified, save artifact to workspace/
```

#### 🔬 QARole — `app/agent/roles/qa.py`

Like the Engineer, QA delegates to a full **Manus agent** — so it can actually *run* tests, not just describe them. Its report format:

```
QA REPORT
─────────────────────────────────
[1] Criterion: <text from PRD>
    Test run: python_execute → test_feature_x.py
    Result: ✅ PASS — output: "all assertions passed"

[2] Criterion: <text from PRD>
    Test run: bash → curl http://localhost:8080/health
    Result: ❌ FAIL — HTTP 500, defect in app/server.py:line 42

─────────────────────────────────
Summary: 4 PASS | 1 FAIL | 0 PARTIAL
Verdict: REWORK REQUIRED
Defects: app/server.py:42 — null pointer in request handler
```

If all P0 criteria pass, the verdict is `APPROVED` and the pipeline terminates cleanly.

### The Topological Execution Engine — `app/agent/orchestrator.py`

The `MultiAgentOrchestrator` uses **Kahn's Algorithm** to execute roles in valid topological order based on their declared dependency graph:

```python
_DEFAULT_DEPS = {
    "product_manager": [],
    "architect":       ["product_manager"],
    "engineer":        ["architect"],
    "qa":              ["engineer"],
}
```

You can **inject a custom pipeline** with different roles and dependencies:

```python
from app.agent.orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator(
    pipeline=["product_manager", "architect", "engineer", "qa"],
    deps={
        "product_manager": [],
        "architect":       ["product_manager"],
        "engineer":        ["architect"],
        "qa":              ["engineer"],
    },
    timeout=7200,  # 2-hour global timeout
)
result = await orchestrator.run("Build a REST API for a task management system")
```

Every role's output is logged to the **same SQLite session**, creating a complete, auditable record of the entire pipeline execution. The orchestrator also handles **role failures gracefully** — if a single role crashes, the error is recorded and the pipeline continues with the next role rather than dying entirely.

### The Async RoleMessageBus

Roles communicate via a lightweight **publish/subscribe message bus** (`app/agent/roles/base_role.py`). Each `RoleMessage` carries:

- `from_role` — the sender
- `to_role` — the recipient (or `"*"` for broadcast)
- `content` — a human-readable summary
- `artefact` — the full output text (PRD, design doc, implementation summary, QA report)

This architecture means roles are **fully decoupled**. You can add new roles, replace existing ones, or run them in parallel (for roles with no dependency edges) without touching any other component.

---

## 🌍 Universal & Offline LLM Routing

ManusClaw implements a **dual-mode LLM router** that works with every LLM provider in existence — cloud or local, paid or free, online or completely air-gapped.

### Mode 1: Official Provider SDKs

Set `provider` in `config.toml` to use the official SDK for that provider. This is the most reliable path for cloud providers.

| Provider | `provider` value | SDK | Key env var |
|---|---|---|---|
| OpenAI (GPT-4o, o1, etc.) | `openai` | `openai` Python SDK | `OPENAI_API_KEY` |
| Anthropic (Claude 3.5, 3 Opus) | `anthropic` | `anthropic` Python SDK | `ANTHROPIC_API_KEY` |
| Google (Gemini 1.5 Pro, Flash) | `google` or `gemini` | `google-generativeai` SDK | `GOOGLE_API_KEY` |
| No provider (zero-credential test) | `mock` | Built-in MockLLM | _(none required)_ |

```toml
# config.toml — Official OpenAI
[llm]
provider    = "openai"
model       = "gpt-4o"
max_tokens  = 4096
temperature = 0.0
# api_key set via OPENAI_API_KEY env var
```

```toml
# config.toml — Anthropic Claude
[llm]
provider    = "anthropic"
model       = "claude-3-5-sonnet-20241022"
max_tokens  = 8192
temperature = 0.0
```

### Mode 2: Universal / Hacker Mode (OpenRouter, Groq, Together, any proxy)

If you set `base_url`, ManusClaw switches to **Universal/Agnostic mode** — it sends standard OpenAI-compatible HTTP requests and works with **any endpoint that speaks the OpenAI chat completions protocol**. No hardcoded provider checks. Just `base_url` + `api_key` + `model`.

This includes OpenRouter (access to 200+ models with one key), Groq, Together AI, Perplexity, vLLM clusters, custom proxies, and AgentRouter.

```toml
# config.toml — OpenRouter (200+ models, one API key)
[llm]
provider  = "openrouter"
base_url  = "https://openrouter.ai/api/v1"
api_key   = "sk-or-v1-..."
model     = "anthropic/claude-3.5-sonnet"
max_tokens = 8192

[llm.extra_headers]
"HTTP-Referer" = "https://github.com/The-JDdev/ManusClaw"
"X-Title"      = "ManusClaw"
```

```toml
# config.toml — Groq (ultra-fast inference, free tier)
[llm]
base_url  = "https://api.groq.com/openai/v1"
api_key   = "gsk_..."
model     = "llama-3.3-70b-versatile"
```

```toml
# config.toml — Together AI
[llm]
base_url  = "https://api.together.xyz/v1"
api_key   = "..."
model     = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
```

The `extra_headers` field (added in v3.2) is critical for **OpenRouter** compliance — it passes the `HTTP-Referer` and `X-Title` headers that OpenRouter requires for rate limit tracking.

### Mode 3: Fully Offline Local LLM

Run ManusClaw with **zero internet dependency** using locally hosted models. Four offline backends are supported via `app/llm/offline_router.py`:

#### 🦙 Ollama (Recommended for offline)

Pull any model with `ollama pull` and point ManusClaw at your local Ollama server. No API key required.

```toml
# config.toml — Ollama
[llm]
provider  = "ollama"
base_url  = "http://localhost:11434/v1"
api_key   = "none"
model     = "llama3.2:3b"
```

```bash
# Pull a model first
ollama pull llama3.2:3b        # 3 GB — fast, works on 8 GB RAM
ollama pull llama3.1:8b        # 6 GB — better reasoning
ollama pull deepseek-r1:7b     # 7 GB — strong at code
ollama pull qwen2.5-coder:7b   # 7 GB — best for coding tasks
```

#### 🖥️ LM Studio (GUI-friendly offline)

LM Studio runs a local OpenAI-compatible server on port 1234. Load any GGUF model through its UI, then:

```toml
# config.toml — LM Studio
[llm]
base_url  = "http://localhost:1234/v1"
api_key   = "none"
model     = "local-model"
```

#### 📦 Direct GGUF — Fully Air-Gapped (llama-cpp-python)

For absolute offline independence — no Ollama, no LM Studio, no server. Just a `.gguf` file on disk.

```bash
pip install llama-cpp-python
# GPU acceleration (NVIDIA):
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall
```

```python
from app.llm.offline_router import GGUFRouter

router = GGUFRouter(
    model_path="/path/to/llama-3.2-3b-instruct.Q4_K_M.gguf",
    n_ctx=4096,
    n_gpu_layers=35,  # 0 = CPU only, 35+ = GPU offload
)
response = router.chat([{"role": "user", "content": "Hello"}])
```

Recommended GGUF models by size:
| Model | Size | RAM Required | Use Case |
|---|---|---|---|
| `llama-3.2-3b-instruct.Q4_K_M.gguf` | ~2 GB | 4 GB | Fast, mobile-friendly |
| `llama-3.1-8b-instruct.Q4_K_M.gguf` | ~5 GB | 8 GB | Balanced |
| `deepseek-coder-v2-lite.Q4_K_M.gguf` | ~9 GB | 12 GB | Best for code |
| `qwen2.5-72b-instruct.Q4_K_M.gguf` | ~40 GB | 48 GB | Maximum intelligence |

#### 🤗 HuggingFace Inference API / Spaces

Connect to HuggingFace's serverless inference API or your own deployed Space/Inference Endpoint:

```toml
# config.toml — HuggingFace Inference API
[llm]
provider  = "huggingface"
model     = "meta-llama/Meta-Llama-3-8B-Instruct"
api_key   = "hf_..."
```

```python
from app.llm.offline_router import HuggingFaceRouter

router = HuggingFaceRouter(
    model="HuggingFaceH4/zephyr-7b-beta",
    hf_token="hf_...",
    endpoint_url="https://your-endpoint.endpoints.huggingface.cloud",
)
```

### LLM Retry & Rate-Limit Handling

The LLM layer implements an **8-attempt exponential backoff** with jitter:

```
Attempt 1 → immediate
Attempt 2 → wait ~1.0s
Attempt 3 → wait ~2.0s
Attempt 4 → wait ~4.0s
...
Attempt 8 → wait up to 60s
```

Rate limit errors (`429`) trigger the backoff. `TokenLimitExceeded` errors propagate immediately (no point retrying with the same context). All other errors retry up to the limit before propagating.

---

## 💾 SQLite Memory & 3-Tier Permission System

### Session Memory — `app/db/session.py`

Every agent run — single-agent or multi-agent — creates a **SQLite session record**. The database lives at `workspace/.sessions/manusclaw.db` and uses **WAL (Write-Ahead Logging)** mode for concurrent access safety.

Three tables are maintained:

```sql
sessions   — one row per agent run (goal, mode, start/end time, state, step count)
messages   — every message logged per session (role, content, timestamp)
tool_calls — full audit log: step, tool_name, args, output, error, success, attempt, duration_ms
```

**The session_id is unified across the server and agent** (fixed in v3.2 patch #4). When the FastAPI server mints a `session_id`, it injects it directly into the `Manus` agent constructor — so all tool calls, messages, and step logs flow into that **single session record**, not a duplicate one created by the agent.

Querying your history via the REST API:

```bash
# List all recent sessions
curl http://localhost:8765/sessions

# Get every message from a session
curl http://localhost:8765/sessions/<session_id>/messages

# Get the complete tool call audit log for a session
curl http://localhost:8765/sessions/<session_id>/tool_calls
```

### Long-Term Memory (RAG) — `app/memory/long_term.py`

Separate from session logging, ManusClaw maintains a **persistent long-term memory** at `workspace/.memory/long_term.db`. It uses SQLite's **FTS5 (Full-Text Search)** virtual table with BM25 ranking for semantic-ish retrieval:

```python
from app.memory.long_term import LongTermMemory

mem = LongTermMemory()

# Store knowledge
await mem.store("The user prefers TypeScript for all web projects", meta={"type": "preference"})
await mem.store("API endpoint is https://api.example.com/v2", meta={"type": "config"})

# Retrieve relevant memories
results = await mem.search("TypeScript project setup", k=5)
# Returns: [{id, content, meta, score, source}, ...]

# Get recent entries
recent = await mem.get_recent(k=10)

# Count total memories
total = await mem.count()
```

The search strategy is **gracefully degraded**:
1. **FTS5 BM25** — fast keyword matching with relevance scoring (primary)
2. **LIKE fallback** — simple substring search if FTS fails
3. **Vector similarity** — silently loaded if `sqlite-vec` or `chromadb` is installed; silently skipped if not

This means the memory system **never crashes** the agent, even if optional vector libraries are missing.

### Short-Term Memory — `app/memory/short_term.py`

The in-session message window is managed by `ShortTermMemory`. It holds the full conversation context — system prompt, user messages, assistant responses, tool call records, and tool results — and feeds them to the LLM on every step.

A **context refresh injection** runs every 5 steps: a compact summary of what has been accomplished so far is inserted as a user message. This prevents context drift on long-running tasks.

### 🛡️ The 3-Tier Permission System — `app/permissions/gate.py`

ManusClaw implements a strict **3-tier permission system** that governs every tool call before execution. It is architecturally enforced — injected at the `_execute_with_retry` level in `ToolCallAgent`, meaning no tool call can bypass it.

```
┌─────────────────────────────────────────────────────────────┐
│                    PERMISSION TIERS                         │
├──────────┬────────────────────────────┬────────────────────┤
│  TIER 1  │  ALLOW — Auto-approved     │  web_search        │
│  (SAFE)  │  in all modes              │  crawl             │
│          │                            │  ask_human         │
│          │                            │  planning          │
│          │                            │  terminate         │
│          │                            │  data_viz          │
├──────────┼────────────────────────────┼────────────────────┤
│  TIER 2  │  ASK — Auto-approved in    │  bash              │
│  (EXEC)  │  Build Mode. Pauses for    │  python_execute    │
│          │  user input in Plan Mode   │  str_replace_editor│
│          │                            │  browser_use       │
├──────────┼────────────────────────────┼────────────────────┤
│  TIER 3  │  DENY — Blocked always     │  fork bombs        │
│  (DOOM)  │  Catastrophic OS patterns  │  rm -rf /          │
│          │  only. Everything else is  │  dd to block dev   │
│          │  permitted.                │  mkfs / wipefs     │
│          │                            │  kill -9 -1        │
└──────────┴────────────────────────────┴────────────────────┘
```

#### Build Mode (Default) — Full Autonomous Power

In Build Mode, Tier 2 (ASK) actions are **silently approved**. The agent operates with complete autonomy — writes files, runs code, executes bash commands, controls browsers — without pausing for human input. This is the default mode and is the correct mode for fully automated pipelines.

```bash
manusclaw "Build a FastAPI server with authentication and deploy it to workspace/"
# No interruptions. The agent runs until done.
```

#### Plan Mode — Human-in-the-Loop

In Plan Mode, every Tier 2 action **pauses and asks for your approval** before executing:

```
⏸  [PLAN MODE] Pending action requires approval:
   Tool: bash
   Preview: apt-get install -y python3-pip
   Approve? [y/N]: 
```

Once you approve an action, it is cached for the session — you won't be asked again for the same tool call. Rejected actions cause the agent to try an alternative approach automatically.

```bash
manusclaw --mode plan "Refactor my entire codebase"
# Pauses at every file write and command execution for your approval
```

#### The Catastrophic Pattern Block (Tier 3)

The hard-deny patterns are surgically narrow — they block **only** genuinely catastrophic OS-destroying operations:

**Linux/macOS:**
- `rm -rf /` and variants
- Fork bombs (`: () { :|: & }; :`)
- Writing to block devices (`dd if=/dev/zero of=/dev/sda`)
- Disk formatting (`mkfs.ext4`, `wipefs`)
- `kill -9 -1` (kill all processes)
- `shred` on system binaries

**Windows (PowerShell):**
- `rd /s /q C:\`
- `format C:`
- `Remove-Item -Recurse -Force C:\`
- `del /f /s /q C:\Windows\*`

**Everything else is permitted.** Installing packages, running ML training jobs, making network calls, managing files, spawning subprocesses — all fully allowed.

---

## 💻 The Four Deployment Modes: The Quartet

### Mode A: Standalone CLI — Linux / macOS / Windows

The native terminal experience. No containers, no servers, no GUI — just raw power.

#### Prerequisites

```bash
# Python 3.10+ required
python3 --version

# Clone the repository
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw

# Install core dependencies
pip install -e .

# Install all optional extras
pip install -e ".[all]"

# Or install selectively
pip install -e ".[server]"    # FastAPI + WebSocket server
pip install -e ".[browser]"   # Playwright browser control
pip install -e ".[http]"      # httpx + aiohttp (web search, platform control)
pip install -e ".[offline]"   # llama-cpp-python (direct GGUF loading)
pip install -e ".[desktop]"   # Flet desktop GUI
```

#### Running the Agent

```bash
# Single task, one shot
python main.py "Write a Python web scraper for Hacker News and save results to workspace/hn.json"

# Interactive prompt
python main.py

# Multi-agent pipeline
python run_multi_agent.py "Build a complete REST API with authentication, tests, and documentation"

# Plan mode (approval-gated)
python run_multi_agent.py --mode plan "Refactor the entire project"
```

#### Global CLI (after `pip install -e .`)

```bash
# These commands become globally available after install
manusclaw "Your task here"
Manusclaw "Your task here"                    # capital M also works

manusclaw-server --host 0.0.0.0 --port 8765  # start the WebSocket server
manusclaw-multi  "Build a web app"            # multi-agent pipeline
manusclaw-desktop                             # launch the desktop GUI
```

#### Windows

```powershell
# Windows — PowerShell
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
pip install -e ".[all]"

# Run
manusclaw "Create a PowerShell script to monitor CPU usage"
```

#### macOS

```bash
brew install python@3.11  # if not installed
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
pip3 install -e ".[all]"
manusclaw "Analyze the files in ~/Downloads and create a summary report"
```

---

### Mode B: Docker Sandbox

Run ManusClaw in a fully isolated Docker container. Ideal for production deployments, CI/CD, and security-sensitive environments.

```bash
# Build the image
docker build -t manusclaw:latest .

# Run interactively (single task)
docker run --rm -it \
  -e OPENAI_API_KEY=sk-... \
  -v $(pwd)/workspace:/app/workspace \
  manusclaw:latest \
  python main.py "Build and test a Python calculator library"

# Run the server
docker run -d \
  --name manusclaw-server \
  -p 8765:8765 \
  -e OPENAI_API_KEY=sk-... \
  -e MANUSCLAW_API_KEY=your-secret-key \
  -v $(pwd)/workspace:/app/workspace \
  manusclaw:latest \
  python run_server.py --host 0.0.0.0 --port 8765

# Run with docker-compose (recommended for production)
docker-compose up -d
```

The `docker-compose.yml` configures:
- Port mapping (`8765:8765`)
- Volume mount for `workspace/` persistence
- Environment variable injection
- Automatic restart policy

#### Docker + Offline LLM (Ollama sidecar)

```yaml
# docker-compose.yml — ManusClaw + Ollama
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

  manusclaw:
    build: .
    depends_on:
      - ollama
    environment:
      - LLM_BASE_URL=http://ollama:11434/v1
    volumes:
      - ./workspace:/app/workspace
    ports:
      - "8765:8765"

volumes:
  ollama_data:
```

---

### Mode C: Termux Native Mode — Android Mobile

Run ManusClaw directly on your **Android device** using Termux — no root required, no Docker, no PC needed. This is the mode it was born in.

```bash
# Step 1: Install Termux from F-Droid (NOT Google Play)
# https://f-droid.org/packages/com.termux/

# Step 2: Run the automated setup script
bash setup-termux.sh

# What setup-termux.sh does:
#   - pkg update && pkg upgrade
#   - pkg install python git clang libffi openssl
#   - pip install -e . (core deps only — no Playwright on Android)
#   - Creates the global 'manusclaw' alias

# Step 3: Wake the beast
manusclaw "Analyze my Downloads folder and build a file organizer script"
```

#### Termux-Specific Notes

- **Bash tool** auto-detects Termux (`shutil.which("termux-info")`) and adjusts its shell initialization accordingly — no `--norc --noprofile` flags that would break Termux's custom profile
- **Playwright/browser** is not available on Android — the agent falls back to `web_search` + `crawl4ai` for all web research tasks
- **GGUF/llama-cpp-python** is available on Termux with `pkg install clang cmake` — you can run 3B models on a modern Android phone (8 GB RAM recommended)
- **Full filesystem access** — the agent can manage your Android storage with appropriate Termux-storage permissions

#### Running Offline on Termux + Ollama (Android)

If you have **Termux:API** and a powerful device (Snapdragon 8 Gen 2+, 12+ GB RAM):

```bash
# Install Ollama for Android (via proot-distro Ubuntu)
proot-distro install ubuntu
proot-distro login ubuntu -- bash -c "curl -fsSL https://ollama.com/install.sh | sh"
proot-distro login ubuntu -- ollama pull llama3.2:3b

# In config.toml
[llm]
base_url = "http://localhost:11434/v1"
api_key  = "none"
model    = "llama3.2:3b"
```

---

### Mode D: Cross-Platform Desktop GUI

ManusClaw ships with a full **terminal-style desktop application** built with [Flet](https://flet.dev/) — a Flutter-based Python UI framework that compiles to native desktop apps.

```bash
# Install Flet
pip install flet

# Launch the desktop GUI
manusclaw-desktop
# or
python -m app.desktop.main
# or (from source)
python app/desktop/main.py
```

The desktop app provides:
- **Terminal-style chat interface** — dark theme, monospace font, green/cyan accent colors matching the ManusClaw identity
- **Live status indicator** — `● Idle` / `● Running…` with color coding
- **Settings panel** (collapsible) — configure Model, Base URL, and API Key without touching config files
- **Task history** — scrollable chat log of every exchange
- **Multi-line input** — paste large prompts, press Enter to run
- **Background execution** — the agent runs in a daemon thread; the UI stays responsive

#### Building Standalone Executables

```bash
# Build for your current platform
python build_release.py

# Or use the shell script
bash build_desktop.sh

# Output:
#   dist/ManusClaw-linux       (Linux AppImage)
#   dist/ManusClaw-macOS.app   (macOS .app bundle)
#   dist/ManusClaw-win.exe     (Windows .exe)
```

The built executables are **self-contained** — no Python installation required on the target machine.

---

## 🚀 The Global Wake-Up Command

After installing with `pip install -e .`, ManusClaw registers **five global entry points** in your system PATH. From any directory, in any terminal, on any supported platform, you can summon the beast:

```bash
# The main incantation — type this anywhere
Manusclaw "Dominate this task"

# Lowercase works too
manusclaw "Dominate this task"

# Start the server
manusclaw-server

# Launch the multi-agent pipeline
manusclaw-multi "Build a production-ready web application"

# Open the desktop app
manusclaw-desktop
```

On **Termux**, the `setup-termux.sh` script adds the alias to your `.bashrc` so `manusclaw` is available immediately after setup, even without a full `pip install -e .`.

On **Windows**, after install, open any PowerShell or Command Prompt window and type `manusclaw` — it's available system-wide.

---

## ⚡ Quick Start

### 30-Second Setup (Mock LLM — No API Key Needed)

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
pip install -e .
python main.py "Hello, prove you exist"
```

The MockLLM runs the full PAORR pipeline — it calls `python_execute` to print `Hello from ManusClaw!`, then calls `terminate`. No API key, no internet. The entire engine fires.

### 60-Second Setup (Real LLM)

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
pip install -e ".[all]"

# Set your API key
export OPENAI_API_KEY=sk-...

# Edit config.toml
[llm]
provider = "openai"
model    = "gpt-4o"

# Run
python main.py "Research the top 5 Python async frameworks, compare them, and write a report to workspace/frameworks.md"
```

---

## ⚙️ Configuration Reference

All configuration lives in `config.toml`. Environment variables override config values for secrets.

```toml
# ─────────────────────────────────────────────────────────
# ManusClaw Configuration — config.toml
# ─────────────────────────────────────────────────────────

[llm]
provider     = "mock"         # mock | openai | anthropic | google | openrouter | ollama | universal
model        = "gpt-4o"       # model name for the selected provider
base_url     = ""             # set this to enable Universal/Agnostic mode
api_key      = ""             # prefer env var: OPENAI_API_KEY or ANTHROPIC_API_KEY
max_tokens   = 4096           # max response tokens
temperature  = 0.0            # 0.0 = deterministic, 1.0 = creative
max_retries  = 6              # LLM retry attempts on failure
timeout      = 120            # seconds before LLM request times out

[llm.extra_headers]           # extra HTTP headers (required for OpenRouter)
# "HTTP-Referer" = "https://github.com/The-JDdev/ManusClaw"
# "X-Title"      = "ManusClaw"

[browser]
headless           = true     # run browser without visible window
disable_security   = false    # disable browser sandbox (use in Docker only)
max_content_length = 10000    # max chars extracted from a page

[search]
engines     = ["duckduckgo", "bing"]   # search engine fallback chain
max_results = 10                        # max results per search

[sandbox]
enabled      = false           # enable Docker sandbox for code execution
docker_image = "python:3.11-slim"
memory_limit = "256m"
timeout      = 30

[runflow]
enable_data_analysis = false  # enable DataAnalysisAgent in flow pipelines
timeout              = 3600   # max seconds for a run_flow session

workspace_dir = "workspace"   # where all agent outputs are saved
max_steps     = 30            # max steps per agent run (prevents infinite loops)

# MCP Server definitions (optional)
# [[mcp_servers]]
# name      = "my-server"
# transport = "stdio"
# command   = "node"
# args      = ["path/to/mcp-server.js"]
```

### Environment Variables

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (auto-loaded into `llm.api_key`) |
| `ANTHROPIC_API_KEY` | Anthropic API key (auto-loaded into `llm.api_key`) |
| `LLM_BASE_URL` | Override `llm.base_url` at runtime |
| `MANUSCLAW_API_KEY` | Enables API Key authentication on the server |
| `MANUSCLAW_ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) |

---

## 🛠️ The Lethal Tool Arsenal

ManusClaw's `Manus` agent is loaded with **8 core tools** at startup. Every tool is a `BaseTool` subclass with a name, description, JSON Schema parameters, and an async `execute()` method.

### 🖥️ `bash` — Persistent Shell

**File:** `app/tool/bash.py`

A **persistent, stateful shell session** that survives across multiple calls within an agent run. The same environment, working directory, and shell variables are maintained between calls — `cd` to a directory once and you're still there on the next call.

| Feature | Detail |
|---|---|
| **Platform** | Linux/macOS → `bash --norc --noprofile` · Windows → `PowerShell -NoProfile` · Termux → `bash` |
| **Timeout** | None by default — runs until natural completion. Pass `timeout=N` for a hard deadline. |
| **Output** | Full stdout + stderr, never truncated. Exit code included. |
| **Blocked** | Only OS-destroying patterns (rm -rf /, fork bombs, dd to block devices) |
| **Persistence** | Shell state survives across tool calls within a session |

```python
# Example tool call (as invoked by the agent)
result = await bash.execute(
    command="cd /app && pip install requests && python -c 'import requests; print(requests.__version__)'",
)
# Subsequent calls remember the working directory
result2 = await bash.execute(command="ls -la")  # still in /app
```

### 🐍 `python_execute` — Isolated Python Subprocess

**File:** `app/tool/python_execute.py`

Runs Python code in a **fresh `multiprocessing.Process`** — completely isolated from the host Python environment, with a **2 GB virtual memory rlimit** applied inside the subprocess.

| Feature | Detail |
|---|---|
| **Isolation** | Separate OS process — crashes don't kill the agent |
| **Memory** | 2 GB virtual memory rlimit via `resource.setrlimit` |
| **Timeout** | None by default. Pass `timeout=N` seconds for a hard cap. |
| **Output** | 100% of stdout + stderr, zero truncation |
| **Imports** | All imports permitted — numpy, torch, sklearn, requests, anything |
| **Blocked** | Fork bombs, direct `/dev/sda` writes |

```python
result = await python_execute.execute(code="""
import torch
import numpy as np

x = torch.randn(1000, 1000)
y = torch.mm(x, x.T)
print(f"Matrix shape: {y.shape}")
print(f"Mean: {y.mean():.4f}")
""")
```

### 🌐 `web_search` — Multi-Engine Search with Fallback

**File:** `app/tool/web_search.py`

Searches the web through a **configurable fallback chain**. If DuckDuckGo fails (rate limit, network), it automatically falls back to Bing. Each engine has its own 3-attempt retry with exponential backoff.

```
DuckDuckGo (duckduckgo-search library) → Bing (aiohttp scraper) → Error
```

```python
result = await web_search.execute(
    query="Python async best practices 2025",
    max_results=8,
)
# Returns: title, URL, and snippet for each result
```

### 📄 `str_replace_editor` — Surgical File Editor

**File:** `app/tool/str_replace_editor.py`

Provides precise file operations: **view** a file or directory, **create** new files with content, **overwrite** files, and **str_replace** — surgically replace an exact string in a file (like a scalpel, not a sledgehammer). All file operations are relative to the workspace.

### 🌍 `browser_use` — Real Playwright Browser

**File:** `app/tool/browser_use_tool.py`

A full headless Chromium browser driven by Playwright. Can navigate URLs, click elements, fill forms, take screenshots, and extract page content. Used for tasks that require actual browser interaction — login forms, JavaScript-rendered pages, file downloads.

### 🕷️ `crawl` — Clean Web Extraction

**File:** `app/tool/crawl4ai.py`

Uses Crawl4AI to extract clean, structured text from any URL. Strips ads, navigation, and boilerplate. Returns the main content as plain text, ready for the agent to reason over.

### 🙋 `ask_human` — Human-in-the-Loop

**File:** `app/tool/ask_human.py`

Pauses execution and asks you a question directly in the terminal. Used when the agent genuinely needs information it cannot determine itself — API keys, passwords, ambiguous requirements, or final approval before a destructive action.

### 🔚 `terminate` — Explicit Completion Signal

**File:** `app/tool/terminate.py`

The agent **must** call this tool to signal task completion. It sets `agent.state = AgentState.FINISHED` and logs the completion reason. An agent that doesn't call terminate before hitting `max_steps` is considered to have hit a timeout, not completed the task.

---

## 🎮 Platform Domination: PlatformControlTool

**File:** `app/tool/platform_control.py`

This is ManusClaw's most powerful tool for **autonomous external platform management**. Give the agent a token and it can create repos, trigger deployments, publish posts, send messages, run inference — end to end, without human intervention.

### Supported Platforms

| Platform | Authentication | Capabilities |
|---|---|---|
| **GitHub** | `token` (PAT) | Create/delete repos, manage issues, push files, trigger workflows, manage releases |
| **Vercel** | `token` + optional `team_id` | List/create deployments, manage projects, configure domains |
| **WordPress** | `site_url` + `username` + `app_password` | Create/edit posts, manage media, update settings |
| **HuggingFace** | `token` | Run inference, manage models/datasets/Spaces, query the Hub API |
| **Netlify** | `token` | Manage sites, trigger deploys, configure DNS |
| **Discord** | `bot_token` | Send messages, manage channels, create webhooks |
| **Telegram** | `bot_token` | Send messages, manage channels, receive updates |
| **Generic REST** | `token` (any scheme) | Any API that accepts HTTP — AWS, Stripe, Twilio, custom services |

### Usage Examples

```python
# Let the agent manage a GitHub repository autonomously
# Agent prompt: "Create a new GitHub repo called 'my-project', initialize it with a README, and push our workspace code"
result = await platform_control.execute(
    platform="github",
    credentials={"token": "ghp_..."},
    method="POST",
    path="/user/repos",
    body={"name": "my-project", "description": "Built by ManusClaw", "private": False},
)

# Deploy to Vercel
result = await platform_control.execute(
    platform="vercel",
    credentials={"token": "vercel_token_...", "team_id": "team_xxx"},
    method="GET",
    path="/v9/projects",
)

# Publish a WordPress post
result = await platform_control.execute(
    platform="wordpress",
    credentials={
        "site_url": "https://myblog.com",
        "username": "admin",
        "app_password": "xxxx xxxx xxxx xxxx",
    },
    method="POST",
    path="/posts",
    body={"title": "ManusClaw: AI That Actually Works", "content": "...", "status": "publish"},
)

# Send a Discord notification
result = await platform_control.execute(
    platform="discord",
    credentials={"bot_token": "Bot MTxx..."},
    method="POST",
    path="/channels/1234567890/messages",
    body={"content": "✅ Deployment complete. Build #42 is live."},
)

# Any REST API
result = await platform_control.execute(
    platform="generic",
    credentials={
        "base_url": "https://api.stripe.com",
        "token": "sk_live_...",
        "auth_scheme": "Bearer",
    },
    method="GET",
    path="/v1/customers",
    params={"limit": 10},
)
```

The agent can **chain these tool calls** across a multi-step workflow — for example: write code with `str_replace_editor`, run tests with `python_execute`, push to GitHub with `platform_control`, trigger a Vercel deployment, and send a Telegram notification on completion. All autonomous, all in one run.

---

## 📡 Dual UI: Terminal & Web

### Terminal UI — The Raw Interface

The CLI is ManusClaw's native habitat. Every agent output is streamed to stdout in real time, with structured logging via the custom `app/logger.py`.

```bash
# Recommended terminal setup for the best experience
# JetBrains Mono font, dark theme, 200+ column width

export MANUSCLAW_API_KEY=""  # leave empty for local use
python main.py
```

Output format:
```
[manus] ▶ Starting run (task_id=3f2a1b4c, session_id=abc123, mode=build, max_steps=30)
[manus] ── Step 1/30 ──
[manus] Tool call (1/4): web_search({"query": "Python async frameworks 2025"})
[manus] Tool result: Search results for 'Python async frameworks 2025':
        [1] FastAPI vs Litestar vs Sanic...
[manus] ── Step 2/30 ──
[manus] Tool call (1/4): str_replace_editor({"command": "create", "path": "workspace/report.md"})
[manus] Tool result: File created: workspace/report.md
[manus] ■ Finished. state=finished steps=4
```

### FastAPI WebSocket Server — Real-Time Streaming

ManusClaw runs a **FastAPI WebSocket server** at `app/server/main.py` that exposes the full agent engine via HTTP and WebSocket.

#### Starting the Server

```bash
# Via CLI entry point (after pip install -e .)
manusclaw-server --host 0.0.0.0 --port 8765

# Via Python directly
python run_server.py --host 0.0.0.0 --port 8765 --reload

# Via uvicorn directly
uvicorn app.server.main:app --host 0.0.0.0 --port 8765

# Via Docker
docker run -p 8765:8765 manusclaw:latest manusclaw-server
```

#### REST API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/healthz` | None | Health check |
| `GET` | `/` | None | Server info |
| `GET` | `/tools` | None | List available tools |
| `POST` | `/run` | API Key | Fire-and-forget async run |
| `POST` | `/run/sync` | API Key | Synchronous run (waits for result) |
| `POST` | `/multi-agent` | API Key | Run the full 4-role pipeline |
| `GET` | `/sessions` | API Key | List recent sessions |
| `GET` | `/sessions/{id}/messages` | API Key | Get session messages |
| `GET` | `/sessions/{id}/tool_calls` | API Key | Get session tool call audit log |
| `WS` | `/ws/{session_id}` | API Key | WebSocket streaming |

#### WebSocket Protocol

```javascript
// Connect to a session
const ws = new WebSocket("ws://localhost:8765/ws/my-session-001?api_key=your-key");

// Send a task
ws.send(JSON.stringify({ prompt: "Build a Python web scraper", mode: "build" }));

// Receive streaming events
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    switch (msg.type) {
        case "connected":    console.log("Ready:", msg.message); break;
        case "agent_start":  console.log("Starting:", msg.prompt); break;
        case "step_start":   console.log(`Step ${msg.step} beginning`); break;
        case "step_output":  console.log(`Step ${msg.step}:`, msg.content); break;
        case "agent_done":   console.log("Done! Output:", msg.output); break;
        case "agent_error":  console.error("Error:", msg.error); break;
        case "pong":         console.log("Alive"); break;
    }
};

// Keepalive
setInterval(() => ws.send(JSON.stringify({ type: "ping" })), 30000);
```

#### API Key Security

Secure your server with an API key:

```bash
export MANUSCLAW_API_KEY="your-secret-key-here"
manusclaw-server
```

All authenticated endpoints require the `X-API-Key` header:
```bash
curl -H "X-API-Key: your-secret-key-here" \
     -X POST http://localhost:8765/run \
     -H "Content-Type: application/json" \
     -d '{"prompt": "List files in workspace/", "mode": "build"}'
```

WebSocket connections authenticate via query parameter:
```
ws://localhost:8765/ws/session-123?api_key=your-secret-key-here
```

#### CORS Configuration

By default (no `MANUSCLAW_ALLOWED_ORIGINS` set), the server allows all origins with `allow_credentials=False` — compatible with any frontend without credential cookies.

For production deployments with specific frontends:
```bash
export MANUSCLAW_ALLOWED_ORIGINS="https://my-frontend.vercel.app,https://manusclaw-web.pages.dev"
manusclaw-server
```

When explicit origins are configured, `allow_credentials=True` is enabled — required for cookie-based authentication.

#### Connecting manusclaw-web

The [manusclaw-web](https://the-jddev.github.io/ManusClaw) frontend connects to your local server via WebSocket. Start the server, open the web UI, enter your server URL, and get a full visual terminal experience with live streaming output.

### MCP Server — `app/mcp/server.py`

ManusClaw also ships as a **Model Context Protocol (MCP) server** — exposing its tools to any MCP-compatible client (Claude Desktop, Cursor, Continue, etc.).

```bash
python run_mcp_server.py
# Exposes: /tools/list and /tools/call on port 8766
```

```json
// MCP client config (Claude Desktop)
{
  "mcpServers": {
    "manusclaw": {
      "command": "python",
      "args": ["run_mcp_server.py"],
      "env": {
        "MANUSCLAW_API_KEY": "your-key"
      }
    }
  }
}
```

---

## 🏗️ Architecture Deep Dive

### The PAORR Loop

Every single agent step follows the **PAORR** (Plan → Act → Observe → Reflect → Retry) loop:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PAORR LOOP                               │
│                                                                 │
│  ┌───────────┐                                                  │
│  │   PLAN    │ ← Inject tool intelligence scores into context   │
│  │           │   Score all tools against current sub-goal       │
│  └─────┬─────┘   Ask LLM: which tool, what args?               │
│        │                                                        │
│  ┌─────▼─────┐                                                  │
│  │    ACT    │ ← Check permission gate (Tier 1/2/3)            │
│  │           │   Execute tool with retry & backoff              │
│  └─────┬─────┘   Feed result back into context                 │
│        │                                                        │
│  ┌─────▼─────┐                                                  │
│  │  OBSERVE  │ ← Record observation in TaskHistory              │
│  │           │   Log tool call to SQLite                        │
│  └─────┬─────┘   Check for loop patterns                       │
│        │                                                        │
│  ┌─────▼─────┐                                                  │
│  │  REFLECT  │ ← Did the tool output solve the sub-goal?        │
│  │           │   If yes: move on                                │
│  └─────┬─────┘   If no: inject error + ask for self-correction │
│        │                                                        │
│  ┌─────▼─────┐                                                  │
│  │   RETRY   │ ← If error: re-score tools (penalize failed)     │
│  │           │   Ask LLM for corrected tool/args                │
│  └─────┬─────┘   Exponential backoff (base=1s, max=20s)        │
│        │                                                        │
│        └────────────────── next step ──────────────────────────┘
```

### ToolSelector — Adaptive Tool Intelligence

`app/tool/selector.py` implements a heuristic tool scoring engine that runs **before** every LLM decision. It:

1. Scores all available tools against the current sub-goal using keyword/semantic matching
2. Penalizes tools that have recently failed in this run
3. Injects the ranked list + rationale as a `┌─ TOOL INTELLIGENCE ─┐` block into the conversation
4. Tracks `record_use`, `record_success`, `record_failure` to adapt scores across the run

This guides the LLM toward better tool choices without overriding its judgment — the LLM can still deviate from the top-ranked tool, but must explain why.

### Loop Detection & Escape

The agent monitors for two types of loops:

**Duplicate Response Loop** — if the last N assistant messages are identical text, inject an escape prompt forcing a new strategy.

**Tool-Call Loop** — if the `TaskHistory` detects the same tool being called with the same args across 3 recent steps without progress, inject a hard escape: *"Switch to a completely different tool or decomposition strategy."*

### Self-Check Every 3 Steps

Every 3 steps, the Manus agent injects a structured self-check prompt:

```
[SELF-CHECK]
1. Which sub-goals are complete? (list them)
2. Which sub-goal are you currently working on?
3. Are you making progress, or repeating the same action?
4. What is your NEXT concrete tool call?
```

This forces the agent to maintain an explicit model of its progress and prevents it from drifting or losing track of the original goal on long-running tasks.

---

## 🔧 Bug Fixes & Improvements (v3.2 Patch)

A comprehensive codebase audit identified and resolved **128+ bugs, errors, and missing logic** across 19 files — 267 lines added, 102 lines removed. Every fix preserves existing behavior while correcting the underlying defect. No features were removed or skipped.

### 🔴 Critical Fixes (6 files)

These fixes address bugs that could cause data loss, incorrect execution, silent failures, or security vulnerabilities in core agent pathways.

#### `app/llm/offline_router.py` — All Routers Were Sync with Wrong Return Types

All four offline routers (`OllamaRouter`, `LMStudioRouter`, `GGUFRouter`, `HuggingFaceRouter`) were implemented as **synchronous methods** despite being called from async contexts. This caused the event loop to block on every LLM call, freezing the entire agent while waiting for model inference. Additionally, the return types were inconsistent — some routers returned raw strings while others returned dictionaries, breaking the caller's type expectations. All four routers have been converted to **proper async methods** with `await` on I/O operations, and return types are now unified to match the `LLMResponse` schema that the rest of the codebase expects.

#### `app/agent/toolcall.py` — Exponential Backoff Operator Precedence & tool_call_id Mismatch

The exponential backoff calculation `base * 2 ** attempt + jitter` suffered from **Python operator precedence** issues — the addition of jitter was applied before the exponentiation in certain code paths, resulting in nearly constant retry delays instead of the intended exponential growth. The formula has been parenthesized explicitly as `(base * (2 ** attempt)) + jitter` to guarantee correct evaluation order. Additionally, the `tool_call_id` field in tool response messages was being set to a **newly generated UUID** instead of the original `tool_call_id` from the LLM's function call, which caused the LLM to reject tool results as orphaned responses. The fix ensures the response `tool_call_id` always matches the request's `tool_call_id`.

#### `app/agent/react.py` — solved=True Default on Parse Error & Case-Sensitive Code Block Parsing

When the ReAct agent failed to parse the LLM's response (malformed JSON, unexpected format), the parser defaulted to `solved=True`, causing the agent to **prematurely terminate** and report success even when the task was incomplete. The fix changes the default to `solved=False` on parse errors, forcing the agent to retry with a corrected prompt. Additionally, code block extraction used a **case-sensitive** regex pattern that only matched lowercase ` ```python ` but missed ` ```Python ` or ` ```PYTHON ` variants that some LLMs produce. The regex is now case-insensitive.

#### `app/agent/base.py` — Fire-and-Forget DB Race Condition & Overly Aggressive Duplicate Threshold

The base agent's step-logging method dispatched database writes as **fire-and-forget `asyncio.create_task()`** calls without awaiting completion. Under high concurrency (multi-agent pipelines), this caused SQLite write contention, silently dropped audit log entries, and occasionally corrupted the WAL index. The fix uses `await` on the database write coroutine directly within the step method, ensuring each write completes before the next step begins. The duplicate message detection threshold was also set too aggressively — a similarity threshold of `0.85` flagged legitimate distinct messages as duplicates when they shared common boilerplate text (e.g., two different tool results both containing "Tool call result:"). The threshold has been lowered to `0.95` to reduce false positives while still catching genuine duplicates.

#### `app/agent/roles/architect.py` — Incomplete Design Published Downstream After Retry Failure

When the Architect role encountered an LLM error during design generation and the retry limit was exhausted, it still **published whatever partial output existed** to the `RoleMessageBus`. This meant the Engineer role received an incomplete design document (missing sections, truncated file tree, no implementation plan) and attempted to execute it, leading to cascading failures. The fix adds a completeness check: if the design document is missing any of the six mandatory sections, the Architect publishes an **error message** instead of a partial artefact, and the orchestrator records the failure gracefully.

#### `app/agent/orchestrator.py` — False-Positive Verdict Detection, GC Hook Tasks, O(n) Queue

Three bugs were fixed in the orchestrator. First, the **verdict detection** regex matched substrings like `"APPROVED"` appearing inside code blocks or example output, causing false-positive pipeline terminations. The regex now only matches verdicts in the dedicated `Verdict:` line format. Second, the `atexit` garbage collection hook spawned **detached asyncio tasks** that attempted to close the database after the event loop was already shut down, causing `RuntimeError: Event loop is closed` on exit. The GC hook now checks if the event loop is running before scheduling cleanup. Third, the role result queue used `queue.get()` with a **linear O(n) scan** to find results for a specific role, degrading performance as the number of roles and messages grew. The queue has been replaced with a `dict[str, asyncio.Event]` lookup for O(1) role result retrieval.

### 🟠 High Priority Fixes (7 files)

These fixes address bugs that cause incorrect behavior, poor performance, or security issues in commonly used code paths.

#### `app/llm/llm.py` — GoogleClient Missing Import/Tools/None Handling, AnthropicClient Temperature/Text Blocks, UniversalClient Timeout

Three LLM client classes had critical defects. **GoogleClient** was missing the `import google.generativeai` statement at the module level, causing an `ImportError` at runtime when the Google provider was selected. It also failed to pass the `tools` parameter to the Gemini API, making function calling impossible. And when the model returned `None` for a candidate (which happens when content is filtered), the client crashed with an `AttributeError`. **AnthropicClient** passed the `temperature` parameter even when it was `0.0`, which the Anthropic API rejects for certain models. It also failed to handle `text` content blocks in the response (only handling `tool_use` blocks), causing responses without tool calls to be silently dropped. **UniversalClient** had no request timeout, allowing hung connections to block the agent indefinitely. A configurable timeout (default 120s) has been added to all HTTP requests.

#### `app/tool/crawl4ai.py` — aiohttp text() API Misuse Breaking Fallback

The Crawl4AI fallback path called `response.text` as a property when using `aiohttp`, but `aiohttp`'s `ClientResponse.text` is an **async coroutine** that must be awaited. This caused the fallback to store the coroutine object itself (a generator) as the page content instead of the actual text, resulting in `str(coroutine)` being passed to the agent as "extracted content." The fix adds `await response.text()` to properly resolve the coroutine.

#### `app/tool/data_viz.py` — Path Traversal, Code Injection, Blocking Subprocess

Three security and correctness bugs were fixed. **Path traversal**: the output file path was not sanitized, allowing `../../etc/crontab` style attacks via crafted `filename` parameters. All paths are now resolved against the workspace directory and validated to prevent escape. **Code injection**: the matplotlib code was executed via `exec()` with no sanitization, allowing arbitrary code execution. The fix wraps execution in a restricted globals dictionary and validates the code AST before execution. **Blocking subprocess**: the chart rendering pipeline ran `subprocess.run()` synchronously in the async event loop, freezing all other agent operations during rendering. The fix uses `asyncio.create_subprocess_exec()` for non-blocking execution.

#### `app/tool/platform_control.py` — Blocking Sync HTTP in Async Context

The `PlatformControlTool` used `httpx.Client` (synchronous) inside its async `execute()` method. Every platform API call — GitHub, Vercel, WordPress, Discord, Telegram — blocked the event loop for the full duration of the HTTP request (including DNS lookup, TLS handshake, and response transfer). In multi-agent pipelines, this meant all agents stalled while any single platform call was in flight. The fix switches to `httpx.AsyncClient` with `await` on all request methods.

#### `app/server/main.py` — CORS/Auth Warnings, Version Sync, Background Task GC, Session Mode

Four issues were fixed in the FastAPI server. **CORS/Auth warnings**: the middleware logged warnings on every request about missing `MANUSCLAW_API_KEY` even when intentionally running without authentication. The warning now only fires once at startup. **Version sync**: the `/healthz` and `/` endpoints returned a hardcoded version string that didn't match `pyproject.toml`, causing version mismatch in monitoring. The version is now read from the package metadata at runtime. **Background task GC**: background tasks created via `asyncio.create_task()` were not stored, allowing Python's garbage collector to destroy them mid-execution. Tasks are now stored in a `set` and removed only on completion. **Session mode**: the `/run` endpoint ignored the `mode` parameter from the request body, always defaulting to `build` mode even when `plan` was explicitly requested.

#### `app/sandbox/docker.py` — stderr-as-Error False Failure Detection

The Docker sandbox runner treated **any output on stderr** as a task failure, even though many legitimate programs write progress information and warnings to stderr (e.g., `pip install` downloads, `npm` warnings, compiler diagnostics). This caused the agent to report code execution as failed when it actually succeeded. The fix checks the container's **exit code** instead: exit code 0 means success regardless of stderr content, non-zero means failure. stderr is still captured and returned to the agent for debugging purposes.

#### `app/permissions/gate.py` — Blocking input() in Async Context

In Plan Mode, the permission gate called Python's built-in `input()` function to prompt the user for approval. This is a **blocking synchronous call** that freezes the entire asyncio event loop, preventing the server from processing WebSocket heartbeats, other client requests, or background tasks. In the server mode, this caused WebSocket timeout disconnections while waiting for approval. The fix uses `asyncio.get_event_loop().run_in_executor()` to run `input()` in a thread pool, keeping the event loop responsive. Alternatively, when running via the WebSocket server, the approval request is sent as a WebSocket message and the response is awaited asynchronously.

### 🟡 Medium Priority Fixes (6 files)

These fixes address deprecation warnings, missing data fields, dependency issues, and minor correctness bugs.

#### `app/schema.py` — Deprecated datetime.utcnow

All datetime fields (`created_at`, `updated_at`, `started_at`, `ended_at`) used `datetime.utcnow()`, which is deprecated since Python 3.12 and will be removed in a future version. The method also produces naive datetime objects (no timezone info), which cause comparison errors when mixed with timezone-aware datetimes from other sources. All occurrences have been replaced with `datetime.now(timezone.utc)` to produce timezone-aware UTC datetimes.

#### `app/flow/planning.py` — Missing Error/Duration Fields & Step ID Collision

The planning flow's `Step` model was missing `error` and `duration_ms` fields that downstream consumers (the logger, the session database, and the WebSocket streaming interface) expected, causing `AttributeError` when accessing `step.error` or `step.duration_ms`. Both fields have been added with appropriate defaults (`error: str | None = None`, `duration_ms: float = 0.0`). Additionally, the step ID generation used `str(step_number)`, which caused **ID collisions** when multiple plans were created in the same session (step 1 of plan A and step 1 of plan B both got ID `"1"`). The ID now includes the plan ID as a prefix: `f"{plan_id}:{step_number}"`.

#### `app/agent/roles/base_role.py` — Deprecated datetime

The `BaseRole` class used `datetime.utcnow()` for the `published_at` timestamp in `RoleMessage`, subject to the same deprecation and timezone issues as `schema.py`. Replaced with `datetime.now(timezone.utc)`.

#### `pyproject.toml` — Missing google-generativeai Dependency

The `google` provider was listed as a supported LLM provider in the README and config, but `google-generativeai` was not declared as a dependency in `pyproject.toml` — not even as an optional extra. Users who ran `pip install -e ".[all]"` still could not use the Google provider without manually installing the package. The dependency has been added to the `[project.optional-dependencies]` section under the `google` extra and included in the `all` extra.

#### `run_server.py` — wss:// vs ws:// Mismatch & Version Sync

The WebSocket URL construction always used the `ws://` scheme, even when the server was deployed behind an HTTPS reverse proxy that terminates TLS. Browsers connecting via HTTPS refuse mixed-content connections to `ws://` endpoints, breaking the web UI. The fix detects the `X-Forwarded-Proto: https` header and upgrades the scheme to `wss://` accordingly. The version string returned by the server startup banner was also hardcoded and out of sync with `pyproject.toml` — it now reads from package metadata.

#### `main.py` — EOFError/KeyboardInterrupt Handling

When running in interactive mode, pressing `Ctrl+D` (EOF) or `Ctrl+C` (interrupt) at the input prompt caused an unhandled exception traceback to be printed, which looked like a crash rather than a clean exit. Both signals are now caught gracefully — `EOFError` prints a clean exit message, and `KeyboardInterrupt` prints a brief interruption notice. Neither produces a stack trace in normal usage.

### Summary Table

| Severity | File | Bug Description | Impact |
|---|---|---|---|
| 🔴 Critical | `app/llm/offline_router.py` | All 4 routers were sync, wrong return types | Event loop blocked on every LLM call |
| 🔴 Critical | `app/agent/toolcall.py` | Backoff precedence, tool_call_id mismatch | Retries didn't back off; LLM rejected tool results |
| 🔴 Critical | `app/agent/react.py` | solved=True on parse error, case-sensitive code blocks | Premature termination; missed code in responses |
| 🔴 Critical | `app/agent/base.py` | Fire-and-forget DB writes, aggressive dupe threshold | Dropped audit logs; false duplicate detection |
| 🔴 Critical | `app/agent/roles/architect.py` | Partial design published after retry failure | Engineer executed incomplete design |
| 🔴 Critical | `app/agent/orchestrator.py` | False-positive verdicts, GC hook crash, O(n) queue | Premature pipeline end; exit crash; slow lookup |
| 🟠 High | `app/llm/llm.py` | GoogleClient import/tools/None; AnthropicClient temp/text; UniversalClient timeout | Google crashed; Anthropic dropped text; Universal hung |
| 🟠 High | `app/tool/crawl4ai.py` | aiohttp text() not awaited | Fallback stored coroutine object as content |
| 🟠 High | `app/tool/data_viz.py` | Path traversal, code injection, blocking subprocess | Security vulnerabilities; event loop freeze |
| 🟠 High | `app/tool/platform_control.py` | Sync HTTP in async method | Event loop blocked on every platform API call |
| 🟠 High | `app/server/main.py` | CORS warnings, version mismatch, GC tasks, session mode | Log spam; stale version; dropped tasks; mode ignored |
| 🟠 High | `app/sandbox/docker.py` | stderr treated as failure | False failures on programs with stderr output |
| 🟠 High | `app/permissions/gate.py` | Blocking input() in async context | Event loop freeze in Plan Mode |
| 🟡 Medium | `app/schema.py` | Deprecated datetime.utcnow | Future breakage; naive datetime comparison errors |
| 🟡 Medium | `app/flow/planning.py` | Missing error/duration fields, step ID collision | AttributeError on step.error; duplicate step IDs |
| 🟡 Medium | `app/agent/roles/base_role.py` | Deprecated datetime.utcnow | Future breakage; naive datetime |
| 🟡 Medium | `pyproject.toml` | Missing google-generativeai dependency | Google provider unusable without manual install |
| 🟡 Medium | `run_server.py` | ws:// vs wss:// mismatch, version string stale | Web UI broken behind HTTPS proxy |
| 🟡 Medium | `main.py` | Unhandled EOFError/KeyboardInterrupt | Ugly stack trace on Ctrl+C/D |

---

## 💌 A Note from the Founder

> "I built this massive, autonomous AI architecture from Bangladesh, using nothing but my smartphone. Compiling, testing, and running an ecosystem of this scale on a mobile device is incredibly difficult and incurs server/API costs. I poured my heart into giving you total uncensored power. If ManusClaw has helped you dominate your workflow, please consider fueling the project through the donation vaults below. Your support keeps the beast alive. — The-JDdev (SHS Shobuj)"

---

## 💎 Donation Vault

If ManusClaw has empowered your work, your support directly funds continued development, server costs, API testing across providers, and new feature research.

Every contribution — no matter the size — is felt by a solo developer building something real from a smartphone in Bangladesh.

---

**USDT (TRC20 — Tron Network)**
```
TH75J4zaMPwhyR3QxEFdwTCgU2Pp3yPUEr
```

**WebMoney WMT (Tether)**
```
T202226490170
```

**WebMoney WMZ (USD)**
```
Z430378899900
```

**bKash (Bangladesh Local)**
```
01310211442
```

---

### Contact & Community

| Channel | Link |
|---|---|
| 📧 Email | [thejddev.official@gmail.com](mailto:thejddev.official@gmail.com) |
| 💬 Telegram | [@aamoviesadmin](https://t.me/aamoviesadmin) |
| 📘 Facebook | [itsshsshobuj](https://fb.com/itsshsshobuj) |
| 🐙 GitHub | [@The-JDdev](https://github.com/The-JDdev) |
| 🌐 Web | [the-jddev.github.io/ManusClaw](https://the-jddev.github.io/ManusClaw) |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for full text.

Free to use, fork, modify, and deploy. Attribution appreciated but not required.

---

<div align="center">

**Built with 🔥 from Bangladesh · By The-JDdev (SHS Shobuj)**

*"In a world of wrappers, be the engine."*

[![Star this repo](https://img.shields.io/github/stars/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw)

</div>

<div align="center">

<img src="https://placehold.co/1200x400/0d1117/58a6ff?text=ManusClaw+v3.1+%E2%80%94+The+Autonomous+AI+Operating+System&font=raleway" alt="ManusClaw Banner" width="100%" />

<h1>🦾 ManusClaw v3.1</h1>

<p><strong>The open-source autonomous AI operating system.<br/>
Multi-agent · PAORR loop · Universal LLM · WebSocket server · 3-tier permissions · SQLite memory · Mobile-ready · Task-complete execution</strong></p>

<p><em>Created by <a href="https://github.com/The-JDdev">The-JDdev (SHS Shobuj)</a> — JD Lab</em></p>

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.1.0-blueviolet)](https://github.com/The-JDdev/ManusClaw/releases)
[![Stars](https://img.shields.io/github/stars/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw/stargazers)
[![Forks](https://img.shields.io/github/forks/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw/network/members)
[![Issues](https://img.shields.io/github/issues/The-JDdev/ManusClaw)](https://github.com/The-JDdev/ManusClaw/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange)](https://github.com/The-JDdev/ManusClaw/pulls)
[![FastAPI](https://img.shields.io/badge/FastAPI-WebSocket-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-red)](https://docs.pydantic.dev/latest/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)

</div>

---

## 📋 Table of Contents

- [What is ManusClaw?](#-what-is-manusclaw)
- [v3.1 — What's New](#-v31--whats-new)
- [v3.0 — What's New](#-v30--whats-new)
- [Task-Complete Execution Philosophy](#-task-complete-execution-philosophy)
- [Architecture Overview](#-architecture-overview)
- [Universal LLM Router](#-universal-llm-router)
- [Multi-Agent Pipeline](#-multi-agent-pipeline)
- [Memory System](#-memory-system)
- [Permission System](#-permission-system)
- [SQLite Session Logging](#-sqlite-session-logging)
- [WebSocket Server & Web UI](#-websocket-server--web-ui)
- [PAORR Loop & Tool Intelligence](#-paorr-loop--tool-intelligence)
- [Installation — Linux](#-installation--linux)
- [Installation — macOS](#-installation--macos)
- [Installation — Windows](#-installation--windows)
- [Installation — Docker](#-installation--docker)
- [Installation — Termux (Android)](#-installation--termux-android)
- [Installation — pip](#-installation--pip)
- [Building Standalone Executables](#-building-standalone-executables)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Support The Vision](#-support-the-vision)

---

## 🤖 What is ManusClaw?

**ManusClaw** is a production-grade, open-source **autonomous AI operating system** built entirely in Python. It combines the best ideas from MetaGPT, AutoGPT, OpenCode, and Manus into a single unified framework that runs from your terminal — or your browser.

> **Identity:** Every ManusClaw agent runs with a hardcoded identity: *"You are ManusClaw, an autonomous AI engine created by The-JDdev (SHS Shobuj)."* The agent does not identify as any base LLM provider.

ManusClaw is designed for developers, researchers, and power users who want:
- A **fully self-hosted** alternative to commercial agent products
- **Zero-vendor-lock-in** — swap LLMs with a single config change
- **Full system access** — no artificial restrictions on what the agent can do
- **Complete transparency** — every decision, tool call, and retry logged in colour

---

## 🚀 v3.1 — What's New

| System | v3.0 | v3.1 |
|---|---|---|
| **Tool execution** | Default 2min, max 10min, 512 KB output cap | **No default, no max — runs until task done. Full output always returned.** |
| **Timeout model** | Fixed DEFAULT + MAX caps | **Dynamic: pass `timeout=N` only when you need a deadline. Omit = run forever.** |
| **Output cap** | 512 KB (truncated) | **No cap — complete output always returned to the agent** |

---

## 🚀 v3.0 — What's New

| System | v2.x | v3.0 |
|---|---|---|
| **LLM routing** | Provider-specific (OpenAI, Anthropic) | Universal dual-mode: official SDKs + any OpenAI-compatible API |
| **Agent architecture** | Single Manus agent | Multi-role pipeline: PM → Architect → Engineer → QA |
| **Memory** | Short-term context buffer | Two-tier: ShortTermMemory + RAG LongTermMemory (SQLite FTS5) |
| **Audit log** | None | Full SQLite session/message/tool-call DB |
| **Permissions** | Hard-deny only | 3-tier: Allow / Ask / Deny + Build Mode / Plan Mode |
| **Web interface** | None | FastAPI WebSocket server + manusclaw-web HTML/JS/Tailwind UI |
| **Mobile support** | None | No-Docker fallback, full CORS, Termux-compatible |
| **Tool limits** | 64 KB / 30s | Unlimited output / task-complete duration |

---

## ⏱️ Task-Complete Execution Philosophy

> *"Kaam khatm hone tak rukna nahi — chahe 2 minute lage, 20 minute lage, ya 3 ghante."*
> *(Don't stop until the work is done — whether it takes 2 minutes, 20, or 3 hours.)*

ManusClaw tools have **no hardcoded timeout and no output size limit**. The agent decides when it is done — not a clock, not a byte counter.

### How timeout works

| How you call it | What happens |
|---|---|
| `timeout` omitted / `None` | Runs until natural completion. The framework never kills it. |
| `timeout=120` | Killed after exactly 120 seconds if still running. |
| `timeout=7200` | Killed after exactly 2 hours if still running. |

```python
# Runs until the compile finishes — could be 30s or 30 minutes
bash.execute("make -j$(nproc)")

# Runs until the training loop finishes — could be hours
python_execute.execute(open("train.py").read())

# Only use timeout= when YOU need an explicit hard deadline
bash.execute("curl https://api.example.com/ping", timeout=10)
```

### Output

Full stdout + stderr is always returned to the agent — no byte truncation, ever. The agent needs complete output to reason, debug, and iterate correctly. Cutting the output is a reasoning bug.

---

## 🏗 Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    ManusClaw v3.1 Stack                        │
├────────────────────────────────────────────────────────────────┤
│  Entry Points                                                  │
│  ┌─────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐ │
│  │ main.py │  │ run_flow.py  │  │run_multi   │  │run_server│ │
│  │  (CLI)  │  │ (PlanFlow)   │  │_agent.py   │  │.py (WS)  │ │
│  └────┬────┘  └──────┬───────┘  └─────┬──────┘  └────┬─────┘ │
├───────┼───────────────┼───────────────┼───────────────┼────────┤
│  Orchestration Layer                                           │
│  ┌────▼───────────────▼───────────────▼────────────────────┐  │
│  │              MultiAgentOrchestrator (DAG)                │  │
│  │  ProductManager → Architect → Engineer → QA              │  │
│  │  Async message bus · Topological sort · Re-planning      │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│  Agent Layer              │                                    │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  BaseAgent (identity, memory, permissions, DB logging)   │  │
│  │    └── ReActAgent (PAORR loop)                           │  │
│  │           └── ToolCallAgent (function calling, retry)    │  │
│  │                  └── Manus (full tool suite)             │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│  Support Systems          │                                    │
│  ┌─────────┐ ┌──────────┐ │ ┌───────────┐ ┌───────────────┐  │
│  │MemoryDB │ │Permission│ │ │ToolSelect │ │  LLM Router   │  │
│  │STM+LTM  │ │Gate      │ │ │ Scoring   │ │ Dual-Mode     │  │
│  └─────────┘ └──────────┘ │ └───────────┘ └───────────────┘  │
│                           │                                    │
│  Tool Layer               │                                    │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  python_execute · bash · str_replace_editor · browser    │  │
│  │  web_search · crawl · data_viz · ask_human · terminate   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 🌍 Universal LLM Router

ManusClaw v3 supports **two seamless modes** of LLM connection:

### Mode 1 — Official Providers (The Standard Way)

Set `provider` explicitly to route through official SDKs:

```toml
[llm]
provider    = "openai"
model       = "gpt-4o"
api_key     = ""   # or OPENAI_API_KEY env var
max_tokens  = 8192
temperature = 0.0
```

| Provider | `provider` value | Notes |
|---|---|---|
| OpenAI | `"openai"` | GPT-4o, GPT-4 Turbo, o1, o3 |
| Anthropic | `"anthropic"` | Claude 3.5 Sonnet, Claude 3 Opus |
| Google | `"google"` | Gemini 1.5 Pro, Gemini Flash |
| MockLLM | `"mock"` | Zero credentials — always works |

### Mode 2 — Universal / Agnostic (The Hacker Way)

Just set `base_url` + `api_key` + `model`. No `provider` needed. The system sends a standard OpenAI-compatible request automatically.

```toml
# OpenRouter — access 100+ models with one API key
[llm]
base_url = "https://openrouter.ai/api/v1"
api_key  = "sk-or-..."
model    = "anthropic/claude-3-5-sonnet"

# Ollama — fully local, zero cost
[llm]
base_url = "http://localhost:11434/v1"
api_key  = "none"
model    = "llama3.2:3b"

# LM Studio — local GUI + API
[llm]
base_url = "http://localhost:1234/v1"
api_key  = "lm-studio"
model    = "mistral-7b-instruct"

# Groq — ultra-fast inference
[llm]
base_url = "https://api.groq.com/openai/v1"
api_key  = "gsk_..."
model    = "llama-3.1-70b-versatile"

# Any custom proxy / AgentRouter / vLLM
[llm]
base_url = "http://your-proxy:8080/v1"
api_key  = "your-key"
model    = "your-model-name"
```

**How it works:** The router detects that `base_url` is set and `provider` is empty/unknown → sends a standard `POST /chat/completions` request with `Authorization: Bearer <api_key>`. No hardcoded provider checks. Works with anything OpenAI-compatible.

---

## 🤖 Multi-Agent Pipeline

ManusClaw v3 implements the **MetaGPT-inspired multi-role architecture**. Four specialist agents communicate via an async message bus and execute in DAG (topological) order.

### The Four Roles

| Role | Responsibility | Output |
|---|---|---|
| **ProductManager** | Receives user goal → writes PRD | Objective, scope, acceptance criteria, priorities |
| **Architect** | Reads PRD → writes system design | File structure, component map, data flow, task DAG |
| **Engineer** | Reads design → implements using Manus tools | Running code, files in workspace/, verified outputs |
| **QA** | Reads implementation → validates against criteria | QA report, PASS/FAIL per criterion, verdict |

### The OTAP Loop (per role)

```
Observe  — read messages from the async bus
Think    — reason with specialist prompt + LLM
Act      — call tools (Engineer/QA) or generate document (PM/Architect)
Publish  — push output to the bus for downstream roles
```

### DAG execution with topological sort

```python
# Default dependency graph
deps = {
    "product_manager": [],
    "architect":       ["product_manager"],
    "engineer":        ["architect"],
    "qa":              ["engineer"],
}
# Kahn's algorithm computes: PM → Architect → Engineer → QA
# Custom pipelines: inject your own roles + deps
```

### Running the pipeline

```bash
# CLI
python run_multi_agent.py "Build a REST API for a todo list with SQLite backend"

# Plan Mode (QA before every tool call)
python run_multi_agent.py --mode plan "Design a web scraper"

# Via REST API
curl -X POST http://localhost:8765/multi-agent \
  -H "Content-Type: application/json" \
  -d '{"goal": "Build a calculator app in Python", "mode": "build"}'
```

---

## 🧠 Memory System

### Tier 1 — ShortTermMemory (context buffer)

```python
class ShortTermMemory(Memory):
    max_messages: int = 100       # rolling window
    # System messages pinned (never trimmed)
    # Oldest non-system messages trimmed first
    # Context refresh injected every 5 steps
    # snapshot() / restore() for Plan Mode dry-runs
```

### Tier 2 — LongTermMemory (persistent RAG)

```python
class LongTermMemory:
    # SQLite backend at workspace/.memory/long_term.db
    # FTS5 full-text search (primary)
    # LIKE fallback if FTS fails
    # Never crashes if vector library is missing
```

```python
# Store knowledge
await ltm.store("Python asyncio event loop runs one coroutine at a time", meta={"source": "docs"})

# Retrieve relevant memory
results = await ltm.search("how does asyncio work", k=5)
# → [{id, content, meta, score, source}, ...]
```

### Context refresh injection

Every 5 steps, the agent's TaskHistory (all prior observations and reflections) is compressed into a summary and injected back into the conversation, so the LLM never loses track across long runs.

---

## 🛡️ Permission System

Three-tier permission model with two agent modes:

### Tiers

| Tier | Examples | Behaviour |
|---|---|---|
| **ALLOW** | `web_search`, `crawl`, `ask_human`, `terminate` | Automatic — never blocked |
| **ASK** | `bash`, `python_execute`, `str_replace_editor`, `browser_use` | Auto-approved in Build Mode; pauses for confirmation in Plan Mode |
| **DENY** | `rm -rf /`, fork bombs, `dd` to block devices, `mkfs` | Unconditionally blocked regardless of mode |

### The ONLY blocked operations

```
rm -rf /          →  wipes root filesystem
rm -rf /*         →  wipes root filesystem  
:(){ :|:& };:     →  fork bomb
dd if=/dev/zero   →  overwrites block devices
mkfs.*            →  formats disks
kill -9 -1        →  kills all processes
```

**Everything else is permitted.** `sudo`, `apt`, `pip`, `git`, `curl`, `systemctl`, `crontab`, `/etc` edits, complex scripts, network operations, global package installs — all fully unblocked.

### Agent Modes

```toml
[runflow]
mode = "build"   # "build" = full auto | "plan" = asks before ASK actions
```

```bash
# Plan Mode — agent shows pending actions and asks before executing
python main.py --mode plan "Refactor the entire codebase"

# Build Mode — fully autonomous (default)
python main.py "Deploy the application"
```

**Plan Mode prompt example:**

```
⏸  [PLAN MODE] Pending action requires approval:
   Tool: bash
   Preview: pip install -r requirements.txt
   Approve? [y/N]: 
```

---

## 📊 SQLite Session Logging

Every agent run is fully audited in `workspace/.sessions/manusclaw.db`:

```sql
-- Three tables
sessions    -- id, goal, agent_name, mode, started_at, ended_at, state, step_count
messages    -- session_id, role, content, ts
tool_calls  -- session_id, step, tool_name, args, output, error, success, attempt, duration_ms, ts
```

**Query via REST API:**

```bash
# List all sessions
curl http://localhost:8765/sessions

# Get all tool calls for a session
curl http://localhost:8765/sessions/abc123def456/tool_calls

# Get all messages for a session
curl http://localhost:8765/sessions/abc123def456/messages
```

**Recover any run:** Since every tool call is logged with input/output, you can replay or inspect any execution — even if it crashed mid-way.

---

## 🌐 WebSocket Server & Web UI

### Server startup

```bash
pip install uvicorn[standard] fastapi
python run_server.py --host 0.0.0.0 --port 8765
```

```
███╗   ███╗ █████╗ ███╗   ██╗██╗   ██╗███████╗
████╗ ████║██╔══██╗████╗  ██║██║   ██║██╔════╝
██╔████╔██║███████║██╔██╗ ██║██║   ██║███████╗
██║╚██╔╝██║██╔══██║██║╚██╗██║██║   ██║╚════██║
██║ ╚═╝ ██║██║  ██║██║ ╚████║╚██████╔╝███████║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝
ManusClaw v3.1 — Agent Server  by The-JDdev (SHS Shobuj)

Listening: http://0.0.0.0:8765
REST:      http://0.0.0.0:8765/run
WebSocket: ws://0.0.0.0:8765/ws/<session_id>
Sessions:  http://0.0.0.0:8765/sessions
Health:    http://0.0.0.0:8765/healthz
```

### REST API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/healthz` | Health check |
| `POST` | `/run` | Fire-and-forget agent run (returns session_id immediately) |
| `POST` | `/run/sync` | Synchronous run (waits for completion) |
| `POST` | `/multi-agent` | Run PM → Architect → Engineer → QA pipeline |
| `GET` | `/sessions` | List all sessions |
| `GET` | `/sessions/{id}/messages` | Get all messages for a session |
| `GET` | `/sessions/{id}/tool_calls` | Get all tool calls for a session |
| `GET` | `/tools` | List all available tools |

### WebSocket protocol

```javascript
// Connect
const ws = new WebSocket("ws://localhost:8765/ws/my-session-123");

// Send a task
ws.send(JSON.stringify({ prompt: "Search for Python 3.13 release notes", mode: "build" }));

// Receive streaming events
// { type: "agent_start",  prompt: "..." }
// { type: "step_start",  step: 1, ts: ... }
// { type: "step_output", step: 1, content: "..." }
// { type: "agent_done",  output: "...", state: "FINISHED" }
// { type: "agent_error", error: "..." }
```

### manusclaw-web UI

The companion web UI ([github.com/The-JDdev/manusclaw-web](https://github.com/The-JDdev/manusclaw-web)) connects to this server via WebSocket and provides:
- **Chat interface** — send prompts, see streaming agent output
- **File tree** — browse workspace/ in real time
- **Terminal view** — see tool calls and tool outputs
- **Session history** — browse all prior runs
- **Mode switcher** — toggle Build/Plan mode

```bash
# Self-hosted (open index.html in a browser — no build step)
git clone https://github.com/The-JDdev/manusclaw-web
open manusclaw-web/index.html

# Point it at your backend (local or remote)
# Set SERVER_URL in the UI to ws://your-server:8765
```

**Full CORS** is enabled on the server — connect from GitHub Pages, Vercel, Termux `localhost`, or any origin without issues.

---

## 🔄 PAORR Loop & Tool Intelligence

### The PAORR cycle (per step)

```
PLAN    → LLM writes numbered plan with success criteria (first step only)
ACT     → ToolSelector scores all tools → ranked list injected into prompt
          → LLM picks tool → executed with retry (max 4 attempts, exp. backoff)
OBSERVE → ToolResult captured → Observation logged to TaskHistory + SQLite
REFLECT → LLM judges: did this solve the sub-goal? (JSON: solved/reason/next)
RETRY   → If not solved: error injected, re-score with failure penalty, re-ask
```

### ToolSelector scoring

Before every tool call, all tools are scored 0–100% against the current sub-goal:

```
┌─ TOOL INTELLIGENCE LAYER ─────────────────────────────────────┐
│ Goal analysis: Write and run a Python script to compute...    │
│                                                               │
│  [████████████████████]  70%  python_execute                  │
│  [██████████░░░░░░░░░░]  50%  str_replace_editor              │
│  [██████░░░░░░░░░░░░░░]  30%  bash                            │
│                                                               │
│ ▶ Recommended: python_execute                                 │
│   Reason: strongly recommended — signals: python(+0.45)...   │
└───────────────────────────────────────────────────────────────┘
```

Scoring adapts across the run: tools that fail are penalised, recently-used tools get a mild penalty to encourage trying alternatives.

---

## 🐧 Installation — Linux

**One-liner (Ubuntu, Debian, Fedora, Arch, any distro):**

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw && bash install.sh
```

Or manually:

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py "Print Hello from ManusClaw!"
```

After install the `manusclaw` command is available globally:

```bash
manusclaw "Write a Python web scraper for Hacker News"
```

---

## 🍎 Installation — macOS

Works on **Intel** and **Apple Silicon (M1/M2/M3)**:

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3 git

git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw && bash install.sh
```

Or manually:

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py "Print Hello from ManusClaw!"
```

---

## 🪟 Installation — Windows

**Option A — One-click PowerShell installer:**

```powershell
# Run in PowerShell (as Administrator or normal user)
Set-ExecutionPolicy Bypass -Scope Process -Force
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
powershell -File install.ps1
```

After install, restart terminal and run:

```cmd
manusclaw "Your task here"
```

**Option B — Manual (PowerShell):**

```powershell
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py "Print Hello from ManusClaw!"
```

> **Note:** On Windows, the `bash` tool uses **PowerShell** automatically. All other tools work identically across platforms.

---

## 🐳 Installation — Docker

No Python setup required — just Docker:

```bash
# Clone and build
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw

# Copy and edit config
cp config.toml.example config.toml   # or create config.toml manually
nano config.toml                     # add your API key

# Run a one-shot task
docker compose run --rm manusclaw "Write a Python web scraper"

# Start the WebSocket server (background)
docker compose --profile server up -d

# Run the multi-agent pipeline
docker compose --profile multi run --rm multi-agent "Build a REST API"
```

**Without docker-compose:**

```bash
docker build -t manusclaw .

# CLI
docker run -it --rm \
  -v $(pwd)/config.toml:/manusclaw/config.toml:ro \
  -v manusclaw-workspace:/manusclaw/workspace \
  manusclaw "Your task here"

# Server
docker run -d \
  -p 8765:8765 \
  -v $(pwd)/config.toml:/manusclaw/config.toml:ro \
  -v manusclaw-workspace:/manusclaw/workspace \
  --name manusclaw-server \
  manusclaw python run_server.py --host 0.0.0.0 --port 8765
```

---

## 📱 Installation — Termux (Android)

Run ManusClaw on your Android phone — no root, no PC needed:

```bash
# Inside Termux
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw && bash setup-termux.sh
```

Then in a new Termux session:

```bash
manusclaw "Your task here"
```

**Connect to Ollama on your PC (same WiFi):**

```toml
# config.toml
[llm]
base_url = "http://192.168.1.X:11434/v1"
api_key  = "none"
model    = "llama3.2:3b"
```

---

## 📦 Installation — pip

Install directly from GitHub as a Python package:

```bash
pip install git+https://github.com/The-JDdev/ManusClaw.git
```

Or with optional extras:

```bash
pip install "git+https://github.com/The-JDdev/ManusClaw.git#egg=manusclaw[all]"
```

This installs the `manusclaw`, `manusclaw-server`, and `manusclaw-multi` CLI commands globally.

---

## 🏗️ Building Standalone Executables

Build a single-file executable for your platform (no Python required to run):

```bash
# Install build deps
pip install pyinstaller

# Build for current platform
python build_release.py
```

Output goes to `release/`:

```
release/
├── manusclaw-v3.1.0-linux-x86_64        ← Linux binary
├── manusclaw-v3.1.0-darwin-arm64        ← macOS Apple Silicon binary
├── manusclaw-v3.1.0-windows-amd64.exe   ← Windows binary
└── manusclaw-v3.1.0-*.zip               ← Zip archives
```

**To build for all platforms** — run `python build_release.py` on each platform separately, then upload the binaries to your [GitHub Releases](https://github.com/The-JDdev/ManusClaw/releases/new) page manually.

---

## ⚙️ Configuration

```toml
# config.toml

# ─── LLM ────────────────────────────────────────────────────────
[llm]
# Mode 1: Official provider
provider    = "openai"
model       = "gpt-4o"
max_tokens  = 8192
temperature = 0.0
# api_key   = ""   # or set OPENAI_API_KEY env var

# Mode 2: Universal (comment out provider, set base_url)
# base_url  = "https://openrouter.ai/api/v1"
# api_key   = "sk-or-..."
# model     = "anthropic/claude-3-5-sonnet"

# ─── Execution ──────────────────────────────────────────────────
workspace_dir = "workspace"
max_steps     = 50             # per-agent step cap

# ─── Agent Mode ─────────────────────────────────────────────────
[runflow]
mode                 = "build"   # "build" or "plan"
enable_data_analysis = false
timeout              = 7200      # 2-hour global cap

# ─── Browser ────────────────────────────────────────────────────
[browser]
headless           = true
disable_security   = false
max_content_length = 20000

# ─── Search ─────────────────────────────────────────────────────
[search]
engines     = ["duckduckgo", "bing"]
max_results = 10

# ─── Sandbox (optional Docker isolation) ───────────────────────
[sandbox]
enabled      = false
docker_image = "python:3.11-slim"
memory_limit = "512m"
timeout      = 120
```

---

## 💻 Usage

### Single agent (CLI)

```bash
# Argument
python main.py "Research the top 5 Python web frameworks and save a comparison table to workspace/frameworks.md"

# Interactive
python main.py

# Plan Mode
python main.py --mode plan "Refactor this codebase"
```

### Multi-agent pipeline

```bash
python run_multi_agent.py "Build a working CLI password manager in Python with AES encryption"
```

### PlanningFlow

```bash
python run_flow.py "Scrape the top 10 Hacker News stories and generate a summary PDF"
```

### MCP

```bash
python run_mcp.py --connection sse --server-url http://localhost:8000 --prompt "List all tools"
python run_mcp.py --interactive
```

### WebSocket server

```bash
python run_server.py --host 0.0.0.0 --port 8765
```

### Programmatic API

```python
import asyncio
from app.agent.manus import Manus
from app.agent.orchestrator import MultiAgentOrchestrator
from app.permissions.gate import AgentMode
from app.memory.long_term import LongTermMemory

async def main():
    # Single agent
    agent = Manus(mode=AgentMode.BUILD)
    result = await agent.run("Write and test a Fibonacci function in Python")
    print(result)

    # Multi-agent pipeline
    orch = MultiAgentOrchestrator(mode=AgentMode.BUILD)
    result = await orch.run("Build a REST API for a blog with SQLite")
    print(result)

    # Long-term memory
    ltm = LongTermMemory()
    await ltm.store("User prefers Python 3.11 and black formatting")
    hits = await ltm.search("Python formatting preferences", k=3)
    print(hits)

asyncio.run(main())
```

---

## 📱 Mobile & Termux

ManusClaw v3 runs on Android via **Termux** without Docker:

```bash
# Termux setup
pkg update && pkg install python python-pip git
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
pip install -r requirements.txt

# Use Ollama on a PC and point Termux at it
# config.toml:
# base_url = "http://192.168.1.x:11434/v1"
# api_key  = "none"
# model    = "llama3.2:3b"

python main.py "Help me write a bash script to organize my downloads folder"

# Or start the server and connect from any browser on the same WiFi
python run_server.py --port 8765
# Open http://<termux-ip>:8765 from any device on the same network
```

**No-Docker fallback:** If Docker is not available, `PythonExecute` automatically uses `multiprocessing.Process` isolation. `Bash` uses the native shell. Full functionality is preserved.

**CORS:** The server allows all origins, so connecting a browser-hosted manusclaw-web UI to a Termux backend works out of the box.

---

## 📁 Project Structure

```
ManusClaw/
├── app/
│   ├── agent/
│   │   ├── base.py              ← Identity, memory, permission, session DB
│   │   ├── react.py             ← PAORR loop (think/act/observe/reflect/retry)
│   │   ├── toolcall.py          ← Function calling + ToolSelector + retry
│   │   ├── manus.py             ← Full orchestration, self-check injection
│   │   ├── orchestrator.py      ← DAG multi-agent engine (Kahn's sort)
│   │   ├── data_analysis.py
│   │   ├── browser.py
│   │   ├── mcp.py
│   │   └── roles/
│   │       ├── base_role.py     ← BaseRole, RoleMessage, RoleMessageBus
│   │       ├── product_manager.py  ← PRD generation
│   │       ├── architect.py     ← System design + task DAG
│   │       ├── engineer.py      ← Code implementation via Manus
│   │       └── qa.py            ← Validation + report
│   ├── tool/
│   │   ├── base.py              ← BaseTool, ToolResult, ToolCollection
│   │   ├── selector.py          ← ToolSelector (confidence scoring)
│   │   ├── python_execute.py    ← task-complete / no output cap / multiprocessing
│   │   ├── bash.py              ← task-complete / no output cap / full system access
│   │   ├── str_replace_editor.py
│   │   ├── browser_use_tool.py
│   │   ├── web_search.py
│   │   ├── crawl4ai.py
│   │   ├── planning.py
│   │   ├── data_viz.py
│   │   ├── ask_human.py
│   │   └── terminate.py
│   ├── memory/
│   │   ├── short_term.py        ← ShortTermMemory (rolling context buffer)
│   │   └── long_term.py         ← LongTermMemory (SQLite FTS5 + LIKE fallback)
│   ├── db/
│   │   └── session.py           ← SQLite audit log (sessions/messages/tool_calls)
│   ├── permissions/
│   │   └── gate.py              ← 3-tier Allow/Ask/Deny + Build/Plan mode
│   ├── flow/
│   │   └── planning.py          ← PlanningFlow (re-planning on block)
│   ├── mcp/
│   │   ├── client.py
│   │   └── server.py
│   ├── sandbox/
│   │   └── docker.py
│   ├── llm/
│   │   └── llm.py               ← Dual-mode router (official + universal)
│   ├── schema.py                ← PAORR data models (Pydantic v2)
│   ├── config.py
│   ├── logger.py
│   └── exceptions.py
├── main.py                      ← Single-agent CLI
├── run_flow.py                  ← PlanningFlow CLI
├── run_multi_agent.py           ← Multi-agent pipeline CLI
├── run_mcp.py                   ← MCP agent CLI
├── run_mcp_server.py            ← MCP server host
├── run_server.py                ← FastAPI WebSocket server
├── config.toml
├── requirements.txt
├── workspace/                   ← Agent outputs
│   ├── .memory/long_term.db     ← Long-term memory
│   └── .sessions/manusclaw.db  ← Session audit log
└── logs/                        ← Rotating structured logs
```

---

## 🤝 Contributing

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Guidelines:
- All tools must return `ToolResult` — never raise
- All async code — no blocking calls in coroutines
- Type-annotated Python (Pydantic v2)
- Log with `from app.logger import logger`, not `print()`
- Test with MockLLM first

---

## 📄 License

MIT — see [LICENSE](LICENSE). Built with passion at **JD Lab**.

---

## 💸 Support The Vision

ManusClaw is free, open-source, and actively developed by one person.
If it powers your research, saves you hours, or inspires you — please consider supporting.

<div align="center">

---

### 🙏 Donation Vault

| Method | Address |
|---|---|
| 🪙 **USDT (TRC20)** | `TH75J4zaMPwhyR3QxEFdwTCgU2Pp3yPUEr` |
| 💼 **WebMoney (WMT)** | `T202226490170` |
| 💵 **WebMoney (WMZ)** | `Z430378899900` |
| 📱 **bKash (BD)** | `01310211442` |

---

**Every contribution keeps this project alive. Thank you. ❤️**

*— The-JDdev (SHS Shobuj) · JD Lab*

[![GitHub](https://img.shields.io/badge/GitHub-The--JDdev%2FManusClaw-181717?logo=github&style=for-the-badge)](https://github.com/The-JDdev/ManusClaw)
[![Stars](https://img.shields.io/github/stars/The-JDdev/ManusClaw?style=for-the-badge&logo=github)](https://github.com/The-JDdev/ManusClaw/stargazers)

</div>

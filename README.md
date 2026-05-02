<div align="center">

<img src="https://placehold.co/1200x400/0d1117/58a6ff?text=ManusClaw+v3.1+%E2%80%94+The+Autonomous+AI+Operating+System&font=raleway" alt="ManusClaw Banner" width="100%" />

<h1>🦾 ManusClaw v3.1</h1>

<p><strong>The open-source autonomous AI operating system.<br/>
Multi-agent · PAORR loop · Universal LLM · WebSocket server · 3-tier permissions · SQLite memory · Task-complete execution</strong></p>

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

</div>

---

## 📋 Table of Contents

- [What is ManusClaw?](#-what-is-manusclaw)
- [v3.1 — What's New](#-v31--whats-new)
- [Core Philosophy: Task-Complete Execution](#-core-philosophy-task-complete-execution)
- [Architecture Overview](#-architecture-overview)
- [Universal LLM Router](#-universal-llm-router)
- [PAORR Loop & Tool Intelligence](#-paorr-loop--tool-intelligence)
- [Multi-Agent Pipeline](#-multi-agent-pipeline)
- [Memory System](#-memory-system)
- [Permission System](#-permission-system)
- [SQLite Session Logging](#-sqlite-session-logging)
- [WebSocket Server & Web UI](#-websocket-server--web-ui)
- [Safety Guardrails](#-safety-guardrails)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Mobile & Termux](#-mobile--termux)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Support The Vision](#-support-the-vision)

---

## 🤖 What is ManusClaw?

ManusClaw is a **terminal-first, open-source autonomous AI agent framework** built in Python. It connects any LLM (OpenAI, Anthropic, Google, Ollama, OpenRouter, or any OpenAI-compatible endpoint) to a rich tool ecosystem and a production-grade multi-agent orchestration layer.

You give it a goal. It plans, acts, observes, reflects, and retries until the task is done — not until a timer runs out.

---

## 🚀 v3.1 — What's New

| Feature | Detail |
|---|---|
| **Task-Complete Execution** | No DEFAULT timeout, no MAX cap. Tools run until the job is done. |
| **Unlimited Output** | `bash` and `python_execute` return full output always — no byte truncation. |
| **Dynamic Deadlines** | Pass `timeout=N` only when you need a hard kill. Omit for run-to-completion. |
| **Full v3.0 stack** | LLM router, multi-agent roles, STM+LTM memory, permissions, audit log, WebSocket server |

---

## ⚙️ Core Philosophy: Task-Complete Execution

> **"Kaam khatm hone tak rukna nahi — chahe 2 minute lage, 20 minute lage, ya 3 ghante."**
> *(Don't stop until the work is done — whether it takes 2 minutes, 20, or 3 hours.)*

ManusClaw tools have **no hardcoded timeout and no output size limit**. The agent decides when it is done, not a clock.

```python
# bash — runs until the compile finishes, however long that takes
bash.execute("make -j$(nproc)")

# python_execute — runs until the training loop completes
python_execute.execute(open("train.py").read())

# explicit deadline — only when YOU need one
bash.execute("curl ...", timeout=30)   # kill if still going after 30s
```

### How timeout works

| Call | Behaviour |
|---|---|
| `timeout` omitted / `None` | Runs until natural completion. Never killed by the framework. |
| `timeout=60` | Killed after exactly 60 seconds if still running. |
| `timeout=7200` | Killed after exactly 2 hours if still running. |

The framework never decides what is "too long". You do — or you don't, and it just runs.

---

## 🏗️ Architecture Overview

```
User / API / Web UI
        │
        ▼
  ┌─────────────────────────────────────────┐
  │           ManusClaw Core Engine         │
  │                                         │
  │  ┌─────────────┐   ┌─────────────────┐  │
  │  │  LLM Router │   │  Permission Gate │  │
  │  │  dual-mode  │   │  Allow/Ask/Deny  │  │
  │  └──────┬──────┘   └────────┬────────┘  │
  │         │                   │            │
  │  ┌──────▼───────────────────▼────────┐  │
  │  │         PAORR Agent Loop          │  │
  │  │  Plan → Act → Observe →           │  │
  │  │  Reflect → Retry (max 4x)         │  │
  │  └──────────────┬────────────────────┘  │
  │                 │                        │
  │  ┌──────────────▼────────────────────┐  │
  │  │         Multi-Agent DAG           │  │
  │  │  PM → Architect → Engineer → QA   │  │
  │  └──────────────┬────────────────────┘  │
  │                 │                        │
  │  ┌──────────────▼────────────────────┐  │
  │  │          Tool Layer               │  │
  │  │  bash · python_execute · browser  │  │
  │  │  web_search · file · ask_human    │  │
  │  └──────────────┬────────────────────┘  │
  │                 │                        │
  │  ┌──────────────▼────────────────────┐  │
  │  │       Memory & Audit              │  │
  │  │  STM (task history) + LTM (RAG)   │  │
  │  │  SQLite session log               │  │
  │  └───────────────────────────────────┘  │
  └─────────────────────────────────────────┘
```

---

## 🔀 Universal LLM Router

Connect any LLM — official SDKs or any OpenAI-compatible endpoint.

**Mode 1 — Official providers** (`provider` key in config):

| Provider | Models |
|---|---|
| `openai` | gpt-4o, gpt-4-turbo, gpt-3.5-turbo |
| `anthropic` | claude-3-5-sonnet, claude-3-haiku |
| `google` | gemini-1.5-pro, gemini-flash |
| `mock` | Built-in — zero credentials needed |

**Mode 2 — Agnostic / Universal** (set `base_url`):

Works with OpenRouter, Ollama, LMStudio, vLLM, Groq, Together, Perplexity, any proxy — just point `base_url` at any OpenAI-compatible endpoint.

```toml
# config.toml — OpenRouter
[llm]
base_url = "https://openrouter.ai/api/v1"
api_key  = "sk-or-..."
model    = "anthropic/claude-3.5-sonnet"

# config.toml — Local Ollama
[llm]
base_url = "http://localhost:11434/v1"
api_key  = "none"
model    = "llama3.2:3b"
```

---

## 🔥 PAORR Loop & Tool Intelligence

Every agent step runs the full **Plan → Act → Observe → Reflect → Retry** cycle:

```
PLAN    — LLM reasons about the current sub-goal
ACT     — calls the highest-confidence tool
OBSERVE — captures full output (no truncation)
REFLECT — LLM judges: "Was the goal solved?"
RETRY   — if not solved, feeds error back and tries again (max 4x)
```

### Tool Confidence Scoring

Before every tool call, `ToolSelector` scores all available tools against the current goal:

```
[ToolSelector] Goal: "Download and parse arxiv:2401.00001"
  [████████████████░░░░]  82%  web_search    ← download(+0.55), parse(+0.35), recency(+0.10)
  [████████████░░░░░░░░]  62%  bash          ← curl(+0.45), recency(-0.10)
  [████░░░░░░░░░░░░░░░░]  22%  python_execute← parse(+0.35), recency-penalty(-0.10)
  [██░░░░░░░░░░░░░░░░░░]  10%  browser_use   ← general capability
```

The ranked list + rationale is injected into the LLM prompt so it makes a deliberate, informed pick — not a random one.

### Exponential Backoff on Failure

```
Attempt 1 → fail → wait 1.0s
Attempt 2 → fail → wait 2.4s
Attempt 3 → fail → wait 5.3s
Attempt 4 → fail → wait 11.6s → give up, log error, move to next step
```

### Doom-Loop Detection

`ShortTermMemory` tracks every failed tool call. If the agent tries the same tool with the same arguments twice consecutively, it is automatically blocked and forced to choose a different approach.

---

## 🤝 Multi-Agent Pipeline

For complex tasks, ManusClaw spins up a full agent team routed through a DAG orchestrator:

```
PM          → writes structured requirements
Architect   → designs system, picks tech stack
Engineer    → writes and runs the code
QA          → tests, validates, reports bugs
```

```bash
python run_multi_agent.py "Build a REST API that scrapes Hacker News front page"
```

---

## 🧠 Memory System

### Short-Term Memory (STM)
- Rolling task history — last N steps, tool calls, and results
- Failed-call cache — prevents doom-loops
- Injected into every LLM prompt as context

### Long-Term Memory (LTM)
- TF-IDF + cosine similarity RAG over past task outcomes
- Automatically retrieves relevant past experience for new tasks
- Persists across sessions (SQLite-backed)

---

## 🛡️ Permission System

Three-tier gate on every tool call:

| Tier | Action |
|---|---|
| `ALLOW` | Tool runs immediately — no prompt |
| `ASK` | Agent pauses and asks the human for approval |
| `DENY` | Tool call is blocked entirely |

Two modes: **BUILD** (autonomous, executes freely) and **PLAN** (restricted, read-only tools only).

```bash
python main.py "Deploy to prod" --mode plan   # PLAN mode — review before anything runs
python main.py "Deploy to prod"               # BUILD mode — fully autonomous
```

---

## 🗃️ SQLite Session Logging

Every run is fully audited to `~/.manusclaw/sessions.db`:

| Column | Content |
|---|---|
| `task_id` | UUID per run |
| `timestamp` | ISO 8601 |
| `role` | user / assistant / tool |
| `content` | message or tool result |
| `tool_name` | which tool was called |
| `duration_ms` | how long it took |

```bash
sqlite3 ~/.manusclaw/sessions.db "SELECT * FROM events ORDER BY timestamp DESC LIMIT 20;"
```

---

## 🌐 WebSocket Server & Web UI

### Start the API server

```bash
python run_server.py
# → ws://localhost:8000/ws
# → http://localhost:8000/docs  (Swagger UI)
```

### Companion Web UI

→ **[github.com/The-JDdev/manusclaw-web](https://github.com/The-JDdev/manusclaw-web)**

Full HTML/JS/Tailwind interface — no build step, no Node.js, open in any browser:
- Real-time chat via WebSocket
- Live tool log with confidence score bars
- File tree viewer
- Session history

```bash
git clone https://github.com/The-JDdev/manusclaw-web
cd manusclaw-web
python3 -m http.server 3000
# → http://localhost:3000
```

---

## 🛡️ Safety Guardrails

ManusClaw takes a **minimal, precise** approach to safety. Only operations that literally destroy the OS are blocked. Everything else is permitted.

### Blocked (hard deny — always, unconditionally):

```bash
rm -rf /          # destroys root filesystem
rm -rf /*         # same
fork bomb         # :(){:|:&};:
dd if=/dev/zero of=/dev/sda   # wipes disk
mkfs.*            # formats a partition
wipefs            # nukes partition table
kill -9 -1        # kills every process on the system
shred /bin/*      # shreds system binaries
```

### Permitted (everything else — no exceptions):

```bash
sudo anything     rm -rf ~/project    apt install xyz
pip install xyz   docker run ...      systemctl restart nginx
curl / wget       /etc edits          crontab changes
git operations    ssh commands        npm / cargo / go build
ml training       data crawlers       overnight batch jobs
```

---

## 📦 Installation

```bash
# Clone
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw

# Install dependencies
pip install -r requirements.txt

# Configure your LLM (see Configuration below)
cp config.example.toml config.toml
nano config.toml

# Run
python main.py "Your task here"
```

### Requirements

```
python >= 3.10
fastapi
uvicorn[standard]
websockets
anthropic
openai
google-generativeai
pydantic >= 2.0
loguru
toml
aiohttp
sqlite3 (stdlib)
```

---

## ⚙️ Configuration

```toml
# config.toml

[llm]
# Option A — Official provider
provider = "openai"
api_key  = "sk-..."
model    = "gpt-4o"

# Option B — Agnostic (OpenRouter, Ollama, any proxy)
# base_url = "https://openrouter.ai/api/v1"
# api_key  = "sk-or-..."
# model    = "anthropic/claude-3.5-sonnet"

# Option C — Local Ollama (no API key)
# base_url = "http://localhost:11434/v1"
# api_key  = "none"
# model    = "llama3.2:3b"

[agent]
max_steps = 30        # max PAORR steps per run
mode      = "build"   # "build" (autonomous) or "plan" (ask before acting)

[memory]
stm_window   = 20     # how many steps to keep in short-term memory
ltm_top_k    = 5      # how many past experiences to retrieve

[server]
host = "0.0.0.0"
port = 8000
```

---

## 🚀 Usage

### Single-agent CLI

```bash
python main.py "Write a Python web scraper for news.ycombinator.com"
python main.py "Analyse this CSV and plot sales trends" --file data.csv
python main.py "Set up a FastAPI project with auth" --mode plan
```

### Multi-agent pipeline

```bash
python run_multi_agent.py "Build a full-stack todo app with React + FastAPI"
```

### WebSocket server

```bash
python run_server.py
# Then open manusclaw-web/index.html in your browser
```

### Python API

```python
import asyncio
from app.agent.manus import Manus

async def main():
    agent = Manus()
    result = await agent.run("Summarise the top 10 Hacker News posts")
    print(result)

asyncio.run(main())
```

---

## 📱 Mobile & Termux

ManusClaw runs fully on Android via Termux — no root required.

```bash
# Termux setup
pkg update && pkg upgrade
pkg install python git
pip install -r requirements.txt

# Point to a local Ollama or any API
# Set base_url in config.toml → done
python main.py "Your task"
```

---

## 📁 Project Structure

```
ManusClaw/
├── main.py                     # CLI entry point
├── run_server.py               # FastAPI + WebSocket server
├── run_multi_agent.py          # Multi-agent pipeline runner
├── config.toml                 # Your config (git-ignored)
├── requirements.txt
│
├── app/
│   ├── agent/
│   │   ├── base.py             # BaseAgent — MANUSCLAW_IDENTITY, run loop, audit
│   │   ├── react.py            # ReActAgent — PAORR loop
│   │   ├── toolcall.py         # ToolCallAgent — tool dispatch + retry + backoff
│   │   ├── manus.py            # Manus — the main autonomous agent
│   │   ├── orchestrator.py     # DAG multi-agent orchestrator
│   │   └── roles/
│   │       ├── product_manager.py
│   │       ├── architect.py
│   │       ├── engineer.py
│   │       └── qa.py
│   │
│   ├── llm/
│   │   └── llm.py              # Universal dual-mode LLM router
│   │
│   ├── memory/
│   │   ├── short_term.py       # STM — task history + doom-loop detection
│   │   └── long_term.py        # LTM — TF-IDF RAG over past tasks
│   │
│   ├── db/
│   │   └── session.py          # SQLite session audit log
│   │
│   ├── permissions/
│   │   └── gate.py             # 3-tier Allow/Ask/Deny gate
│   │
│   ├── server/
│   │   └── main.py             # FastAPI + WebSocket + CORS
│   │
│   └── tool/
│       ├── bash.py             # Persistent shell — task-complete, no caps
│       ├── python_execute.py   # Isolated Python — task-complete, no caps
│       ├── selector.py         # Tool confidence scoring
│       ├── web_search.py
│       ├── browser_use_tool.py
│       ├── str_replace_editor.py
│       ├── ask_human.py
│       └── terminate.py
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss.

```bash
git fork https://github.com/The-JDdev/ManusClaw
git checkout -b feature/your-feature
# make changes
git commit -m "feat: your feature"
git push origin feature/your-feature
# open a PR
```

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 💙 Support The Vision

ManusClaw is built solo, published free, open to all.
If it saves you time or powers your project, consider supporting:

| Method | Address |
|---|---|
| **USDT TRC20** | `TH75J4zaMPwhyR3QxEFdwTCgU2Pp3yPUEr` |
| **WebMoney WMT** | `T202226490170` |
| **WebMoney WMZ** | `Z430378899900` |
| **bKash** | `01310211442` |

Every contribution — however small — keeps this project alive and improving.

---

<div align="center">

**Built by [The-JDdev (SHS Shobuj)](https://github.com/The-JDdev) — JD Lab**

*"Autonomous. Persistent. Unstoppable."*

</div>

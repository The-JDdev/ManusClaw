<div align="center">

```
  __  __                      ______ _               
 |  \/  |                    |  ____| |              
 | \  / | __ _ _ __  _   _ _| |__  | | _____      __
 | |\/| |/ _` | '_ \| | | / /  __| | |/ _ \ \ /\ / /
 | |  | | (_| | | | | |_| / /| |____| | (_) \ V  V / 
 |_|  |_|\__,_|_| |_|\__,/_/ |______|_|\___/ \_/\_/  
```

**The Open-Source Autonomous AI Ecosystem**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/version-3.2.0-brightgreen.svg)](https://github.com/The-JDdev/ManusClaw/releases)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Docker%20%7C%20Termux-lightgrey.svg)]()

*Built from Bangladesh, running everywhere.*

[**Download**](https://github.com/The-JDdev/ManusClaw/releases) · [**Web UI**](https://the-jddev.github.io/manusclaw-web/) · [**Report Bug**](https://github.com/The-JDdev/ManusClaw/issues)

</div>

---


## 📱 Android App

**ManusClaw is now on Android!** Download the native app from the [manusclaw-app](https://github.com/The-JDdev/manusclaw-app) repository.

| | |
|---|---|
| **Download APK** | [manusclaw-v3.2.0.apk](https://github.com/The-JDdev/manusclaw-app/releases/download/v3.2.0/manusclaw-v3.2.0.apk) |
| **Source** | [github.com/The-JDdev/manusclaw-app](https://github.com/The-JDdev/manusclaw-app) |
| **Android** | 8.0+ (API 26) |
| **Features** | Terminal-style dark UI · Real-time WebSocket streaming · Settings screen · Ollama offline support |

**Quick start:**
1. Start ManusClaw server on your PC: `python run_server.py --host 0.0.0.0 --port 8765`
2. Install the APK on your Android phone
3. Tap ⚙ in the app → enter your PC's local IP → Save
4. Send tasks from your phone — agent responds in real-time

---
## 📋 Table of Contents

- [Android App](#-android-app)
- [What is ManusClaw?](#-what-is-manusclaw)
- [v3.2 — What's New](#-v32--whats-new)
- [v3.1 — What's New](#-v31--whats-new)
- [v3.0 — What's New](#-v30--whats-new)
- [Task-Complete Execution Philosophy](#-task-complete-execution-philosophy)
- [Architecture Overview](#-architecture-overview)
- [Universal LLM Router](#-universal-llm-router)
- [True Offline & Local LLM Mastery](#-true-offline--local-llm-mastery)
- [Multi-Agent Pipeline](#-multi-agent-pipeline)
- [Memory System](#-memory-system)
- [Permission System](#-permission-system)
- [SQLite Session Logging](#-sqlite-session-logging)
- [WebSocket Server & Web UI](#-websocket-server--web-ui)
- [PlatformControlTool — External Platform Access](#-platformcontroltool--external-platform-access)
- [PAORR Loop & Tool Intelligence](#-paorr-loop--tool-intelligence)
- [Deployment Quartet — 4 Modes](#-deployment-quartet--4-modes)
- [Installation — Linux](#-installation--linux)
- [Installation — macOS](#-installation--macos)
- [Installation — Windows](#-installation--windows)
- [Installation — Docker](#-installation--docker)
- [Installation — Termux (Android)](#-installation--termux-android)
- [Installation — pip](#-installation--pip)
- [Desktop Software (GUI)](#-desktop-software-gui)
- [Global Command — Wake ManusClaw Anywhere](#-global-command--wake-manusclaw-anywhere)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Support The Vision](#-support-the-vision)

---

## 🤖 What is ManusClaw?

ManusClaw is a **fully autonomous, uncensored AI operating system** — not a chatbot wrapper. It thinks in loops, plans multi-step strategies, executes code, browses the web, controls external platforms, remembers across sessions, and manages complex tasks end-to-end without hand-holding.

It runs **completely locally** with no external API key required (via Ollama or GGUF), or it can power up with any commercial LLM (OpenAI, Anthropic, Google, Groq, etc.). It is **100% open source**, self-hosted, and has zero censorship enforced at the framework level.

**Core capabilities:**

| Capability | Description |
|---|---|
| 🔁 PAORR Loop | Plan → Act → Observe → Reflect → Repeat — persistent autonomous execution |
| 🧠 Two-tier memory | Short-term context + Long-term SQLite/vector RAG |
| 🌐 Universal LLM | Any provider, any local model, zero lock-in |
| 📴 Full offline | Run GGUF models with zero internet, zero API key |
| 👥 Multi-agent | PM → Architect → Engineer → QA pipeline |
| 🔒 3-tier permissions | Allow / Ask / Deny — you control what it can touch |
| 🛡️ Audit log | Every action, every tool call, fully logged to SQLite |
| 🌍 PlatformControl | Autonomously manage GitHub, Vercel, WordPress, AWS, and more |
| 🖥️ Desktop GUI | Native Flet app for Windows, Linux, macOS |
| 📱 Mobile-first | Native Termux support, no Docker needed on Android |

---

## 🚀 v3.2 — What's New

- **Deployment Quartet** — 4 distinct execution modes: CLI, Docker, Termux mobile, Desktop GUI
- **Desktop software** — `build_desktop.sh` compiles a native GUI app for Windows (`.exe`), Linux, macOS via PyInstaller + Flet
- **PlatformControlTool** — autonomous external platform manager (GitHub, Vercel, WordPress, HuggingFace, Netlify, Discord, Telegram, any REST API)
- **Offline LLM Router** — direct GGUF support (llama-cpp-python), Ollama native, LMStudio, text-gen-webui, HuggingFace Inference API
- **Global command injection** — `manusclaw_inject.sh` makes `Manusclaw` (any case) work from any terminal, forever
- **pip packaging** — proper `pyproject.toml` with `[project.scripts]` entry points, optional extras

---

## 🚀 v3.1 — What's New

- **Task-complete execution** — removed all timeout caps. Tools run until the job is done, period.
- **Unlimited output** — no truncation on bash or Python tool output
- **Cross-platform shell** — `bash.py` auto-detects OS: `bash` on Linux/Mac, `PowerShell` on Windows, Termux-aware on Android

---

## 🚀 v3.0 — What's New

- **Dual-mode LLM router** — universal (any provider) + intelligent selection
- **Multi-agent roles** — PM, Architect, Engineer, QA operating in pipeline
- **Short-term + Long-term memory** — full session context + persistent RAG
- **3-tier permission system** — Allow / Ask / Deny per tool category
- **SQLite audit trail** — every session, every call, fully logged
- **FastAPI WebSocket server** — real-time streaming to web clients

---

## ⚙️ Task-Complete Execution Philosophy

ManusClaw operates on one rule: **finish the task**.

- `bash` tool: no timeout — scripts run for seconds or hours, as needed
- `python_execute` tool: no timeout, no output cap — full stdout/stderr preserved
- The agent loops (PAORR) until it reaches a natural task boundary or the user explicitly stops it
- No artificial caps on context, output size, or recursion depth

---

## 🏛️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     ManusClaw Ecosystem                     │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Mode A: CLI │ Mode B:Docker│ Mode C:Termux│ Mode D: Desktop│
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬────────┘
       │              │              │               │
       └──────────────┴──────────────┴───────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   PAORR Agent Loop  │
                    │ Plan→Act→Obs→Reflect│
                    └─────────┬──────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼───────┐  ┌─────────▼──────┐  ┌─────────▼──────┐
│  Universal LLM │  │  Tool Registry  │  │  Memory System  │
│  Router        │  │                 │  │                 │
│  ─────────     │  │  bash           │  │  ShortTermMemory│
│  OpenAI        │  │  python_execute │  │  LongTermMemory │
│  Anthropic     │  │  browser        │  │  SQLite log     │
│  Google        │  │  file_*         │  └─────────────────┘
│  Ollama        │  │  web_search     │
│  LMStudio      │  │  platform_ctrl  │
│  GGUF (local)  │  │  str_replace    │
│  HuggingFace   │  │  terminate      │
└────────────────┘  └─────────────────┘
         │
┌────────▼───────────────────────────────┐
│          Multi-Agent Pipeline          │
│  PM → Architect → Engineer → QA        │
└────────────────────────────────────────┘
```

---

## 🌐 Universal LLM Router

One config key — infinite providers. No code changes needed.

```toml
[llm]
# ── Commercial APIs ──────────────────────────────────────────
provider = "openai"
model    = "gpt-4o"
api_key  = "sk-..."

# ── Anthropic ────────────────────────────────────────────────
# provider = "anthropic"
# model    = "claude-opus-4-5"
# api_key  = "sk-ant-..."

# ── Google ───────────────────────────────────────────────────
# provider = "google"
# model    = "gemini-2.0-flash"
# api_key  = "AIza..."

# ── Groq (fast inference) ────────────────────────────────────
# base_url = "https://api.groq.com/openai/v1"
# model    = "llama-3.3-70b-versatile"
# api_key  = "gsk_..."

# ── OpenRouter (100+ models) ─────────────────────────────────
# base_url = "https://openrouter.ai/api/v1"
# model    = "meta-llama/llama-3.1-70b-instruct"
# api_key  = "sk-or-..."

# ── Fully local — see next section ───────────────────────────
```

---

## 📴 True Offline & Local LLM Mastery

ManusClaw supports **completely offline** operation — zero cloud, zero API key, zero internet.

### Option 1 — Ollama (recommended for beginners)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh    # Linux/Mac
# Windows: https://ollama.ai/download

# Pull a model (runs locally, once downloaded = fully offline)
ollama pull llama3.2:3b       # 2GB — fast, good for most tasks
ollama pull llama3.1:8b       # 5GB — better reasoning
ollama pull codellama:13b     # 8GB — best for code tasks
ollama pull mistral:7b        # 4GB — great all-rounder
ollama pull phi3:mini         # 2GB — ultra fast, low RAM

# Configure ManusClaw
```

```toml
[llm]
provider = "openai_compat"
base_url = "http://localhost:11434/v1"
api_key  = "none"
model    = "llama3.2:3b"
```

### Option 2 — Direct GGUF (fully offline, no Ollama needed)

Download any `.gguf` file from HuggingFace and plug it in directly:

```bash
# Example: download Mistral 7B Q4
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Install the GGUF runtime
pip install llama-cpp-python

# GPU acceleration (NVIDIA CUDA)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python

# Metal (Apple Silicon)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
```

```toml
[llm]
provider   = "gguf"
model_path = "/path/to/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
n_ctx      = 4096
n_gpu_layers = 35   # set 0 for CPU-only
```

### Option 3 — LMStudio (GUI model manager)

1. Download [LMStudio](https://lmstudio.ai/) — free, no account needed
2. Search and download any model inside the app
3. Start the local server (it's OpenAI-compatible)

```toml
[llm]
provider = "openai_compat"
base_url = "http://localhost:1234/v1"
api_key  = "none"
model    = "local-model"
```

### Option 4 — text-generation-webui

```toml
[llm]
provider = "openai_compat"
base_url = "http://localhost:5000/v1"
api_key  = "none"
model    = "your-loaded-model"
```

### Option 5 — HuggingFace Inference API

```toml
[llm]
provider = "huggingface"
model    = "HuggingFaceH4/zephyr-7b-beta"
api_key  = "hf_your_token_here"
```

Or connect to a private HuggingFace Space / dedicated endpoint:

```toml
[llm]
provider     = "huggingface"
endpoint_url = "https://your-space.hf.space"
api_key      = "hf_your_token_here"
```

---

## 👥 Multi-Agent Pipeline

```bash
python run_multi_agent.py "Build a full REST API with auth, rate limiting, and tests"
```

Pipeline execution:

```
PM Agent          → breaks task into milestones, assigns subtasks
Architect Agent   → designs system, picks stack, writes ADR
Engineer Agent    → implements code, runs tests, fixes bugs
QA Agent          → validates output, writes test report
```

Each agent has its own system prompt, memory scope, and tool access level. Results feed forward through the pipeline.

---

## 🧠 Memory System

**Short-Term Memory (STM)**
- Full conversation history within a session
- Tool call results, observations, intermediate thoughts
- Stays in RAM, cleared on exit

**Long-Term Memory (LTM)**
- Persisted to SQLite
- Key facts, completed task summaries, user preferences
- Retrieved via semantic search at the start of each relevant task

**Session Audit Log**
- Every session → its own table in `data/sessions.db`
- Tool calls, inputs, outputs, timestamps, token counts all logged
- Query with any SQLite client

---

## 🔒 Permission System

Three permission tiers — configured per tool category:

| Tier | Behaviour |
|---|---|
| `allow` | Tool executes silently, no prompt |
| `ask` | Agent pauses, requests user confirmation |
| `deny` | Tool is blocked entirely |

```toml
[permissions]
bash           = "allow"   # run shell commands
python_execute = "allow"   # run Python code
file_write     = "ask"     # pause before writing files
browser        = "allow"   # web browsing
network        = "allow"   # HTTP requests
platform_ctrl  = "ask"     # external platform actions
```

Two agent modes:

- **Build mode** — maximum autonomy, minimal interruptions
- **Plan mode** — generates plans and strategy, no execution

---

## 🗄️ SQLite Session Logging

Every run is fully logged to `data/sessions.db`. Query at any time:

```bash
sqlite3 data/sessions.db "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 5;"
sqlite3 data/sessions.db "SELECT tool, input, output FROM tool_calls WHERE session_id='abc123';"
```

Export a session:

```bash
sqlite3 -csv data/sessions.db "SELECT * FROM tool_calls WHERE session_id='abc123';" > session.csv
```

---

## 🌐 WebSocket Server & Web UI

```bash
# Start server
python run_server.py --host 0.0.0.0 --port 8765

# Connect via web UI
open https://the-jddev.github.io/manusclaw-web/

# Or connect programmatically
wscat -c ws://localhost:8765
```

Send a task:

```json
{"type": "task", "content": "Write a Python script that monitors CPU usage"}
```

Receive streaming token output in real-time.

---

## 🌍 PlatformControlTool — External Platform Access

The agent can now **autonomously control any external platform** using your credentials — just like a human admin.

### GitHub

```python
# The agent will call this internally when you give it a task like:
# "Create a new repo, push these files, and open a PR"
platform_control(
    platform="github",
    credentials={"token": "ghp_your_token"},
    method="POST",
    path="/user/repos",
    body={"name": "my-new-project", "private": False}
)
```

### Vercel

```python
platform_control(
    platform="vercel",
    credentials={"token": "your_vercel_token"},
    method="GET",
    path="/v9/projects"
)
```

### WordPress

```python
platform_control(
    platform="wordpress",
    credentials={
        "site_url": "https://yoursite.com",
        "username": "admin",
        "app_password": "xxxx xxxx xxxx"
    },
    method="POST",
    path="/posts",
    body={"title": "Auto-published post", "status": "publish", "content": "..."}
)
```

### Any REST API (generic)

```python
platform_control(
    platform="generic",
    credentials={
        "base_url": "https://api.yourplatform.com",
        "token": "your_api_token",
        "auth_scheme": "Bearer"
    },
    method="DELETE",
    path="/v1/resources/123"
)
```

**Supported platforms:** GitHub · Vercel · WordPress · HuggingFace · Netlify · Discord · Telegram · Any REST API

---

## 🔄 PAORR Loop & Tool Intelligence

ManusClaw uses an adaptive tool-scoring PAORR loop:

```
Plan      → decompose task, identify tools needed
Act       → execute best-scored tool for current step
Observe   → parse output, update memory
Reflect   → update tool scores, check if done
Repeat    → continue until task boundary reached
```

Tool scoring adapts dynamically — failed tools get penalised, recently-used tools get a mild penalty to encourage strategy variation.

---

## 🚀 Deployment Quartet — 4 Modes

### Mode A — Standalone CLI
Pure terminal execution, no GUI, no server. Maximum speed.

```bash
manusclaw "Write a web scraper for Hacker News"
```

### Mode B — Dockerized Sandbox
Fully isolated container. Ideal for sensitive tasks, CI, or shared servers.

```bash
docker compose run --rm manusclaw "Your task"
docker compose --profile server up -d        # WebSocket server
docker compose --profile multi run --rm multi-agent "Build an API"
```

### Mode C — Termux Mobile
Runs natively on Android. No Docker, no PC. Just your phone.

```bash
bash setup-termux.sh
manusclaw "Your task from your phone"
```

### Mode D — Desktop GUI
A native graphical app compiled for your OS. Double-click to launch.

```bash
bash build_desktop.sh
./release/manusclaw-v3.2.0-linux-x86_64
```

---

## 🐧 Installation — Linux

**One-liner:**

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw && bash install.sh
```

**Manual:**

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py "Print Hello from ManusClaw!"
```

After install, `manusclaw` is available globally:

```bash
manusclaw "Write a Python script that monitors disk usage"
```

---

## 🍎 Installation — macOS

Works on Intel and Apple Silicon (M1/M2/M3/M4):

```bash
# Install Homebrew (if not present)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3 git

git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw && bash install.sh
```

GPU acceleration for GGUF models (Apple Silicon):

```bash
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
```

---

## 🪟 Installation — Windows

**Option A — PowerShell installer (recommended):**

```powershell
# Run PowerShell as normal user (no Administrator needed)
Set-ExecutionPolicy Bypass -Scope Process -Force
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
powershell -File install.ps1
```

Restart terminal, then:

```cmd
manusclaw "Your task here"
```

**Option B — Manual:**

```powershell
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py "Your task here"
```

> On Windows, the `bash` tool inside ManusClaw automatically uses **PowerShell** — no WSL required.

---

## 🐳 Installation — Docker

Zero Python setup required:

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw

# Edit your config
cp config.toml.example config.toml
nano config.toml

# One-shot CLI task
docker compose run --rm manusclaw "Write a Python web scraper"

# Background WebSocket server
docker compose --profile server up -d

# Multi-agent pipeline
docker compose --profile multi run --rm multi-agent "Build a REST API with auth"
```

**Without compose:**

```bash
docker build -t manusclaw .

docker run -it --rm \
  -v $(pwd)/config.toml:/manusclaw/config.toml:ro \
  -v manusclaw-workspace:/manusclaw/workspace \
  manusclaw "Your task here"
```

---

## 📱 Installation — Termux (Android)

No PC required. No Docker. Just your phone.

```bash
# Inside Termux
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw && bash setup-termux.sh
```

New session:

```bash
manusclaw "Build a Python REST API"
```

**Connect to Ollama on your PC (same WiFi):**

```toml
[llm]
provider = "openai_compat"
base_url = "http://192.168.1.X:11434/v1"   # your PC's IP
api_key  = "none"
model    = "llama3.2:3b"
```

---

## 📦 Installation — pip

```bash
# Core only
pip install git+https://github.com/The-JDdev/ManusClaw.git

# With all extras
pip install "git+https://github.com/The-JDdev/ManusClaw.git#egg=manusclaw[all]"

# Desktop GUI only
pip install "git+https://github.com/The-JDdev/ManusClaw.git#egg=manusclaw[desktop]"

# Offline GGUF support
pip install "git+https://github.com/The-JDdev/ManusClaw.git#egg=manusclaw[offline]"
```

After pip install, these commands are available globally:

```bash
manusclaw           # CLI agent
Manusclaw           # same (case alias)
manusclaw-server    # WebSocket server
manusclaw-multi     # multi-agent pipeline
manusclaw-desktop   # desktop GUI
```

---

## 🖥️ Desktop Software (GUI)

ManusClaw compiles into a **standalone native desktop application** — no Python installation required on the target machine.

### Build on your platform

```bash
# Install build dependencies
pip install pyinstaller flet

# Build for current OS (auto-detected)
bash build_desktop.sh

# Options:
bash build_desktop.sh --flet     # GUI app (default)
bash build_desktop.sh --cli      # CLI-only executable
bash build_desktop.sh --onedir   # folder output (faster launch)
```

Output:

```
release/
├── manusclaw-v3.2.0-linux-x86_64          ← Linux binary
├── manusclaw-v3.2.0-linux-x86_64.tar.gz
├── manusclaw-v3.2.0-macos-arm64           ← macOS binary
├── manusclaw-v3.2.0-macos-arm64.tar.gz
└── manusclaw-v3.2.0-windows-amd64.exe     ← Windows binary
```

### Platform notes

**Linux:**
```bash
chmod +x release/manusclaw-*-linux-*
./release/manusclaw-*-linux-*
```

**macOS:**
```bash
chmod +x release/manusclaw-*-macos-*
./release/manusclaw-*-macos-*
# If Gatekeeper blocks: xattr -cr ./release/manusclaw-*-macos-*
```

**Windows:**
Double-click the `.exe` or run from PowerShell.
If SmartScreen warns: click **More info → Run anyway**.

> Note: PyInstaller builds for the *current* platform only. To build for all 3 platforms, run the script on each OS separately.

---

## 🌐 Global Command — Wake ManusClaw Anywhere

After running `install.sh` or `manusclaw_inject.sh`, the word `Manusclaw` (any case) wakes the system from **any terminal window** — no need to navigate to the project folder.

```bash
# Install the global command
bash manusclaw_inject.sh

# Reload your shell
source ~/.bashrc    # or ~/.zshrc

# Now from anywhere:
manusclaw "Summarise all my Python files in ~/projects"
Manusclaw "Deploy my app to Vercel"
MANUSCLAW "Check my GitHub notifications"
```

**If you exit the terminal and come back:**

```bash
# Same — just type it:
Manusclaw "Continue the task from yesterday"
```

**Remove the global command:**

```bash
bash manusclaw_inject.sh --remove
```

**Windows (PowerShell):**

The installer creates `manusclaw.bat` in the project folder and offers to add it to system PATH. After that:

```cmd
manusclaw "Your task here"
```

**Termux:**

```bash
bash manusclaw_inject.sh
# Installs to $PREFIX/bin — available immediately in any Termux session
```

---

## ⚙️ Configuration

Create `config.toml` in the project root:

```toml
# ─── LLM ────────────────────────────────────────────────────────────────────
[llm]
provider = "mock"        # mock | openai | anthropic | google | gguf | ollama
                         # openai_compat | huggingface
model    = "gpt-4o"
# api_key = ""

# Offline GGUF example:
# provider   = "gguf"
# model_path = "/models/llama-3.1-8b.Q4_K_M.gguf"
# n_ctx      = 8192
# n_gpu_layers = 35

# Ollama example:
# provider = "openai_compat"
# base_url = "http://localhost:11434/v1"
# api_key  = "none"
# model    = "llama3.2:3b"

# ─── Agent ───────────────────────────────────────────────────────────────────
[agent]
max_steps  = 50
mode       = "build"     # build | plan

# ─── Permissions ────────────────────────────────────────────────────────────
[permissions]
bash           = "allow"
python_execute = "allow"
file_write     = "allow"
browser        = "allow"
network        = "allow"
platform_ctrl  = "ask"

# ─── Memory ──────────────────────────────────────────────────────────────────
[memory]
db_path        = "data/sessions.db"
max_stm_tokens = 8000

# ─── Server ──────────────────────────────────────────────────────────────────
[server]
host = "0.0.0.0"
port = 8765
```

---

## 🎮 Usage

**Basic task:**

```bash
manusclaw "Write a Python script that monitors CPU usage every 5 seconds"
```

**Multi-step project:**

```bash
manusclaw "Build a FastAPI REST API with JWT auth, SQLite database, and unit tests"
```

**Multi-agent pipeline:**

```bash
python run_multi_agent.py "Design and implement a microservices architecture for an e-commerce platform"
```

**WebSocket server:**

```bash
python run_server.py
# → ws://localhost:8765
```

**Desktop GUI:**

```bash
python -m app.desktop.main
# or run the compiled executable
```

**Platform control (via agent task):**

```bash
manusclaw "Using my GitHub token in config, create a repo called 'my-project', push the files in ./src, then open a pull request"
```

**Offline (no internet):**

```bash
# With Ollama running:
manusclaw "Explain the Rust ownership model and write an example"
```

---

## 📁 Project Structure

```
ManusClaw/
├── main.py                    ← CLI entry point
├── run_server.py              ← WebSocket server
├── run_multi_agent.py         ← Multi-agent pipeline runner
├── run_flow.py                ← Flow execution runner
├── config.toml                ← Your configuration
├── pyproject.toml             ← pip packaging + entry points
├── install.sh                 ← Linux/macOS installer
├── install.ps1                ← Windows PowerShell installer
├── setup-termux.sh            ← Android/Termux installer
├── manusclaw_inject.sh        ← Global command injector
├── build_desktop.sh           ← Desktop GUI builder (PyInstaller + Flet)
├── Dockerfile                 ← Multi-stage Docker build
├── docker-compose.yml         ← CLI + server + multi-agent profiles
│
├── app/
│   ├── agent/                 ← Agent core, PAORR loop, base agent
│   ├── tool/
│   │   ├── bash.py            ← Cross-platform shell (bash/PowerShell/Termux)
│   │   ├── python_execute.py  ← Python execution sandbox
│   │   ├── browser.py         ← Playwright web automation
│   │   ├── file_*.py          ← File read/write/search tools
│   │   ├── web_search.py      ← Web search tool
│   │   ├── platform_control.py← External platform manager ← NEW v3.2
│   │   └── ...
│   ├── llm/
│   │   ├── llm.py             ← Universal LLM router
│   │   └── offline_router.py  ← GGUF / Ollama / LMStudio / HuggingFace ← NEW v3.2
│   ├── desktop/
│   │   └── main.py            ← Flet GUI desktop app ← NEW v3.2
│   ├── memory/                ← STM + LTM + SQLite
│   ├── flow/                  ← Planning flow, flow factory
│   ├── server/                ← FastAPI WebSocket server
│   ├── prompt/                ← System prompts per agent role
│   └── mcp/                   ← MCP server/client
│
├── data/                      ← SQLite databases (auto-created)
└── workspace/                 ← Agent working directory
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit: `git commit -m "feat: add your feature"`
4. Push: `git push origin feat/your-feature`
5. Open a Pull Request

All contributions welcome — tools, LLM adapters, UI improvements, documentation, bug fixes.

---

## 📜 License

MIT License — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

## ❤️ Support The Vision

<div align="center">

---

### 💬 A Note from the Founder (The-JDdev / SHS Shobuj):

*"I built this massive, autonomous AI architecture from Bangladesh, using nothing but my smartphone.*
*Compiling, testing, and running an ecosystem of this scale on a mobile device is incredibly difficult*
*and incurs server/API costs. I poured my heart into giving you total uncensored power.*
*If ManusClaw has helped you dominate your workflow, please consider fueling the project*
*through the donation vaults below. Your support keeps the beast alive."*

---

</div>

| Method | Address |
|---|---|
| USDT TRC20 | `TH75J4zaMPwhyR3QxEFdwTCgU2Pp3yPUEr` |
| WebMoney WMT | `T202226490170` |
| WebMoney WMZ | `Z430378899900` |
| bKash | `01310211442` |

Every contribution — no matter the size — directly funds development, API testing costs, and keeps ManusClaw free and open forever.

---

<div align="center">
  Built with ❤️ from Bangladesh · <a href="https://github.com/The-JDdev">The-JDdev</a> · MIT License
</div>

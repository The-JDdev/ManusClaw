<div align="center">

<!-- HERO IMAGE -->
<img src="https://placehold.co/1200x400/0d1117/58a6ff?text=ManusClaw+%E2%80%94+Autonomous+AI+Agent+Framework&font=raleway" alt="ManusClaw Banner" width="100%" />

<h1>🦾 ManusClaw</h1>

<p><strong>A modular, open-source autonomous AI agent framework for the terminal.<br/>Multi-LLM · Browser Automation · Code Execution · Web Search · MCP Protocol</strong></p>

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Build](https://img.shields.io/badge/build-passing-brightgreen?logo=github-actions)](https://github.com/The-JDdev/ManusClaw)
[![Stars](https://img.shields.io/github/stars/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw/stargazers)
[![Forks](https://img.shields.io/github/forks/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw/network/members)
[![Issues](https://img.shields.io/github/issues/The-JDdev/ManusClaw)](https://github.com/The-JDdev/ManusClaw/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange)](https://github.com/The-JDdev/ManusClaw/pulls)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-red)](https://docs.pydantic.dev/latest/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## 📋 Table of Contents

- [What is ManusClaw?](#-what-is-manusclaw)
- [Core Architecture](#-core-architecture)
- [Feature Highlights](#-feature-highlights)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Usage](#-usage)
  - [Single-Prompt Agent (CLI)](#single-prompt-agent-cli)
  - [Planning Flow](#planning-flow)
  - [MCP Agent](#mcp-agent)
  - [MCP Server](#mcp-server)
  - [Programmatic API](#programmatic-api)
- [Agents](#-agents)
- [Tools](#-tools)
- [LLM Backends](#-llm-backends)
- [MCP Integration](#-mcp-integration)
- [Sandboxing](#-sandboxing)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Support The Vision](#-support-the-vision)

---

## 🤖 What is ManusClaw?

**ManusClaw** is a production-grade, open-source framework for building and running **general-purpose autonomous AI agents** entirely from the terminal. No GUI. No cloud lock-in. No magic boxes.

Built on a clean layered architecture, ManusClaw lets you compose powerful agents that can:

- **Browse the web** with a real Playwright-controlled browser
- **Execute Python and shell commands** in isolated subprocesses
- **Edit any file** on disk with a git-like undo history
- **Search the web** with a resilient multi-engine fallback chain
- **Generate charts and data visualisations** automatically
- **Connect to any MCP-compatible server** via stdio or SSE transport
- **Run for minutes or hours** with loop detection, retry logic, and graceful cleanup

ManusClaw is designed for developers, researchers, and power users who want an agent that is **transparent, extensible, and fully under their control**.

> **Zero credentials required to start.** The built-in `MockLLM` lets you run the full framework, test every tool, and explore the step loop without a single API key.

---

## 🏗 Core Architecture

ManusClaw follows a strict layered design. Each layer adds capability without breaking the contract of the one below it.

```
┌─────────────────────────────────────────────────────────────┐
│                        Entry Points                         │
│  main.py  ·  run_flow.py  ·  run_mcp.py  ·  run_mcp_server │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      Agent Layer                            │
│                                                             │
│  BaseAgent  →  ReActAgent  →  ToolCallAgent                 │
│                                    ↓                        │
│           Manus  ·  DataAnalysis  ·  Browser  ·  MCP        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      Tool Layer                             │
│                                                             │
│  PythonExecute  ·  Bash  ·  StrReplaceEditor               │
│  BrowserUseTool  ·  WebSearch  ·  Crawl4AI                  │
│  PlanningTool  ·  DataVisualization  ·  AskHuman  ·  Terminate │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                       LLM Layer                             │
│                                                             │
│  LLM (retry + backoff)                                      │
│  MockLLM  ·  OpenAI  ·  Azure  ·  Anthropic  ·  Ollama     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Infrastructure Layer                      │
│                                                             │
│  Config (TOML singleton)  ·  Memory (capped)               │
│  Schema (Pydantic v2)  ·  Logger (Loguru)                  │
│  DockerSandbox  ·  MCPClient  ·  MCPServer (FastAPI)        │
└─────────────────────────────────────────────────────────────┘
```

### Agent Inheritance Chain

| Class | Adds |
|---|---|
| `BaseAgent` | State machine (`IDLE→RUNNING→FINISHED/ERROR`), capped memory, loop detection, step cap |
| `ReActAgent` | `think()` + `act()` loop backed by an LLM |
| `ToolCallAgent` | Structured LLM function calling, tool routing, terminate signal |
| `Manus` | Full tool suite wired together, workspace directory management |
| `DataAnalysisAgent` | Adds `DataVisualization` tool |
| `BrowserAgent` | Browser-only tool surface |
| `MCPAgent` | Dynamic MCP server discovery + tool proxying |

### Memory Model

Messages are stored as Pydantic `Message` objects (role, content, tool_calls). The `Memory` class caps history at a configurable `max_messages` (default 100), always preserving system messages. Duplicate consecutive assistant responses trigger a nudge injection.

### Step Loop

```
while state == RUNNING and steps < max_steps:
    step()           ← think (LLM call) + act (tool calls)
    check_stuck()    ← inject nudge if repeated response
cleanup()            ← release browser, shell, MCP connections
```

---

## ✨ Feature Highlights

| Category | Feature |
|---|---|
| 🤖 **Agents** | BaseAgent → ReActAgent → ToolCallAgent → Manus hierarchy |
| 🛠 **Tools** | 10 built-in tools with consistent `BaseTool` / `ToolResult` interface |
| 🧠 **LLMs** | OpenAI, Azure, Anthropic, Ollama, and zero-credential MockLLM |
| 🌐 **Browser** | Playwright persistent session, screenshots as base64 JPEG, tab management |
| 🐍 **Python** | `multiprocessing`-isolated execution, 5 s default timeout |
| 🔍 **Search** | DuckDuckGo → Bing fallback chain, exponential backoff |
| 📁 **Editor** | View / create / str_replace / insert / undo on any file |
| 🔗 **MCP** | SSE and stdio transports, dynamic tool discovery, FastAPI server |
| 🐳 **Sandbox** | Optional Docker isolation; Daytona stub for cloud |
| 📊 **Data Viz** | Matplotlib chart generation → PNG or HTML |
| 📋 **Planning** | PlanningFlow decomposes goals into steps, dispatches to agents |
| ⚙️ **Config** | Thread-safe TOML singleton with env-var fallbacks |
| 📝 **Logging** | Loguru: colour stdout + rotating file logs to `logs/` |
| 🔁 **Retry** | Exponential backoff (1–60 s, 6 attempts) for LLM rate limits |

---

## 🚀 Installation & Setup

### Prerequisites

- Python **3.10** or higher
- `pip` or `uv`
- (Optional) Docker for sandboxed code execution
- (Optional) Node.js for MCP server integrations

### 1. Clone the repository

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

For browser automation (Playwright), install the browser binary:

```bash
playwright install chromium
```

### 4. (Optional) Install crawl4ai

```bash
pip install crawl4ai
crawl4ai-setup
```

### 5. Verify the installation

```bash
python main.py "Print 'Hello from ManusClaw!' using Python."
```

You should see the MockLLM kick in, call the `python_execute` tool, and terminate cleanly — **no API key required**.

---

## ⚙️ Configuration

All settings live in `config.toml` at the project root. Copy the provided default and customise:

```toml
[llm]
provider    = "openai"          # mock | openai | azure | anthropic | ollama
model       = "gpt-4o"
# api_key   = ""               # or set OPENAI_API_KEY env var
max_tokens  = 4096
temperature = 0.0
max_retries = 6

[browser]
headless           = true
disable_security   = false
max_content_length = 10000

[search]
engines     = ["duckduckgo", "bing"]
max_results = 10

[sandbox]
enabled      = false
docker_image = "python:3.11-slim"
memory_limit = "256m"
timeout      = 30

[runflow]
enable_data_analysis = false
timeout = 3600          # 60-minute global cap

workspace_dir = "workspace"
max_steps     = 30

# Add MCP servers:
# [[mcp_servers]]
# name      = "my-server"
# transport = "stdio"
# command   = "node"
# args      = ["path/to/mcp-server.js"]
```

### Secret management

Never put API keys directly in `config.toml`. Use environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export LLM_BASE_URL="https://..."    # Ollama or Azure
```

---

## 💻 Usage

### Single-Prompt Agent (CLI)

Run the full **Manus** agent on a task and exit:

```bash
# Provide prompt as argument
python main.py "Research the top 5 Python async frameworks and save a summary to workspace/async_frameworks.md"

# Or launch interactive prompt
python main.py
```

**Example output:**
```
2024-01-15 14:32:01 | INFO     | Starting run. Max steps: 30
2024-01-15 14:32:01 | INFO     | Step 1/30
2024-01-15 14:32:02 | INFO     | Tool call: web_search({"query": "top Python async frameworks 2024"})
2024-01-15 14:32:03 | INFO     | Tool call: str_replace_editor({"command": "create", ...})
2024-01-15 14:32:04 | INFO     | Tool call: terminate({"reason": "Summary saved to workspace/async_frameworks.md"})
============================================================
FINAL OUTPUT:
Agent terminated: Summary saved to workspace/async_frameworks.md
============================================================
```

---

### Planning Flow

Decompose a complex goal into steps and run each with the appropriate agent:

```bash
python run_flow.py "Collect the latest Bitcoin price, compute its 7-day moving average from public data, and generate a line chart saved to workspace/btc_chart.png"
```

The PlanningFlow will:
1. Call the LLM to decompose the goal into 3–6 concrete steps
2. Dispatch each step to either `Manus` or `DataAnalysisAgent` (if `enable_data_analysis = true`)
3. Log step status (not_started → in_progress → completed/blocked)
4. Enforce a global 60-minute timeout

---

### MCP Agent

Connect to a remote MCP server and run a task:

```bash
# SSE transport
python run_mcp.py \
  --connection sse \
  --server-url http://localhost:8000 \
  --prompt "List available tools and describe each one"

# stdio transport
python run_mcp.py \
  --connection stdio \
  --server-url /usr/bin/my-mcp-server \
  --prompt "Execute a shell command"

# Interactive mode
python run_mcp.py --interactive
```

---

### MCP Server

Host ManusClaw's own tools as an MCP server for external clients:

```bash
python run_mcp_server.py --host 0.0.0.0 --port 8000
```

The server exposes:
- `GET /tools/list` — discover available tools
- `POST /tools/call` — invoke a tool by name
- `GET /healthz` — health check

External agents (including other ManusClaw instances) can then connect:

```bash
python run_mcp.py --connection sse --server-url http://localhost:8000 --prompt "your task"
```

---

### Programmatic API

Use ManusClaw as a library inside your own code:

```python
import asyncio
from app.agent.manus import Manus
from app.agent.data_analysis import DataAnalysisAgent
from app.flow.planning import PlanningFlow

# Run Manus directly
async def run_manus():
    agent = Manus()
    result = await agent.run("Write a Fibonacci function in Python and save it to workspace/fib.py")
    print(result)

# Run a planning flow
async def run_flow():
    flow = PlanningFlow(timeout=600)
    result = await flow.run("Analyse sales data and produce a bar chart")
    print(result)

# Add custom tools
from app.tool.base import BaseTool, ToolCollection
from app.schema import ToolResult
from app.agent.toolcall import ToolCallAgent

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Input"}},
        "required": ["query"],
    }

    async def execute(self, query: str, **_) -> ToolResult:
        return ToolResult(output=f"Processed: {query}")

async def run_custom():
    from app.tool.terminate import Terminate
    tools = ToolCollection(MyCustomTool(), Terminate())
    agent = ToolCallAgent(tools=tools)
    result = await agent.run("Use my_tool with query='hello world'")
    print(result)

asyncio.run(run_manus())
```

---

## 🤖 Agents

| Agent | Class | Description |
|---|---|---|
| **Base** | `BaseAgent` | State machine, memory, loop detection, step cap |
| **ReAct** | `ReActAgent` | Reason + Act loop with LLM |
| **ToolCall** | `ToolCallAgent` | Structured function calling, tool routing |
| **Manus** | `Manus` | Full general-purpose agent with all tools |
| **DataAnalysis** | `DataAnalysisAgent` | Adds chart generation to Manus |
| **Browser** | `BrowserAgent` | Browser + search + crawl only |
| **MCP** | `MCPAgent` | Dynamically discovers and proxies remote MCP tools |

---

## 🛠 Tools

| Tool | Class | Description |
|---|---|---|
| `python_execute` | `PythonExecute` | Execute Python in a `multiprocessing` sandbox (5 s default timeout) |
| `bash` | `Bash` | Persistent async shell session |
| `str_replace_editor` | `StrReplaceEditor` | View / create / str_replace / insert / undo files |
| `browser_use` | `BrowserUseTool` | Playwright browser: navigate, click, type, screenshot, JS |
| `web_search` | `WebSearch` | DuckDuckGo → Bing fallback with exponential backoff |
| `crawl` | `Crawl4AITool` | Clean content extraction from JS-heavy pages |
| `planning` | `PlanningTool` | Create / update / mark_step on execution plans |
| `data_viz` | `DataVisualization` | Generate PNG / HTML charts via Matplotlib |
| `ask_human` | `AskHuman` | Interactive stdin prompt |
| `terminate` | `Terminate` | Explicit stop signal |

All tools implement `BaseTool` and return a `ToolResult(output, error, system, base64_image)`.

---

## 🧠 LLM Backends

| Provider | Config `provider` | Notes |
|---|---|---|
| **MockLLM** | `"mock"` | Zero credentials. Deterministic stub. Always available. |
| **OpenAI** | `"openai"` | GPT-4o, GPT-4 Turbo, GPT-3.5. Set `OPENAI_API_KEY`. |
| **Azure OpenAI** | `"azure"` | Set `base_url` to your Azure endpoint. |
| **Anthropic** | `"anthropic"` | Claude 3.x family. Set `ANTHROPIC_API_KEY`. |
| **Ollama** | `"ollama"` | Local models (Llama 3, Mistral, …). Set `base_url`. |

Retry logic: exponential backoff from 1 s to 60 s, up to 6 attempts. `TokenLimitExceeded` is raised immediately (non-retryable).

---

## 🔗 MCP Integration

ManusClaw implements the [Model Context Protocol](https://modelcontextprotocol.io/) on both sides:

**As a client** (`MCPClient`):
- Discovers tools from remote MCP servers via `tools/list`
- Proxies them as local `MCPProxyTool` instances
- Supports both **stdio** (subprocess) and **SSE** (HTTP) transports

**As a server** (`run_mcp_server.py`):
- Exposes local tools (Bash, Browser, Editor, Terminate) via a FastAPI app
- Fully MCP-compatible JSON-RPC interface
- Ready to plug into any MCP-aware client

Configure servers in `config.toml`:

```toml
[[mcp_servers]]
name      = "filesystem-server"
transport = "stdio"
command   = "npx"
args      = ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

[[mcp_servers]]
name      = "remote-api"
transport = "sse"
url       = "https://my-mcp-server.example.com"
```

---

## 🐳 Sandboxing

Enable Docker-based code isolation in `config.toml`:

```toml
[sandbox]
enabled      = true
docker_image = "python:3.11-slim"
memory_limit = "256m"
timeout      = 30
```

The `DockerSandbox` class runs code in a network-isolated container with a memory cap. Daytona cloud integration is stubbed and ready for implementation.

---

## 📁 Project Structure

```
ManusClaw/
├── app/
│   ├── agent/           # Agent hierarchy
│   │   ├── base.py      # BaseAgent
│   │   ├── react.py     # ReActAgent
│   │   ├── toolcall.py  # ToolCallAgent
│   │   ├── manus.py     # Main general-purpose agent
│   │   ├── data_analysis.py
│   │   ├── browser.py
│   │   └── mcp.py
│   ├── tool/            # Tool implementations
│   │   ├── base.py      # BaseTool, ToolResult, ToolCollection
│   │   ├── python_execute.py
│   │   ├── bash.py
│   │   ├── str_replace_editor.py
│   │   ├── browser_use_tool.py
│   │   ├── web_search.py
│   │   ├── crawl4ai.py
│   │   ├── planning.py
│   │   ├── data_viz.py
│   │   ├── ask_human.py
│   │   └── terminate.py
│   ├── flow/
│   │   └── planning.py  # PlanningFlow (multi-step orchestration)
│   ├── mcp/
│   │   ├── client.py    # MCPClient (stdio + SSE)
│   │   └── server.py    # FastAPI MCP server
│   ├── sandbox/
│   │   └── docker.py    # DockerSandbox + DaytonaSandbox stub
│   ├── llm/
│   │   └── llm.py       # LLM abstraction + retry + Mock
│   ├── schema.py        # Pydantic v2 models
│   ├── config.py        # TOML config singleton
│   ├── logger.py        # Loguru setup
│   └── exceptions.py    # Custom exceptions
├── main.py              # Single-prompt CLI entry point
├── run_flow.py          # PlanningFlow CLI
├── run_mcp.py           # MCP agent CLI
├── run_mcp_server.py    # MCP server host
├── config.toml          # Default configuration
├── requirements.txt
├── workspace/           # Agent output directory
├── logs/                # Rotating log files
└── README.md
```

---

## 🤝 Contributing

Contributions are warmly welcomed! Here's how to get involved:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/my-feature`
3. **Write** clean, typed Python (Pydantic v2, async-compatible)
4. **Add** or update tests in `tests/`
5. **Open** a pull request with a clear description

### Development setup

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Coding guidelines

- Follow the `BaseTool` contract for all new tools
- Use `async def` for all I/O-bound operations
- Return `ToolResult` — never raise from a tool's `execute()`
- Log with `from app.logger import logger`, never with `print()`
- Type everything with Python 3.10+ syntax

---

## 📄 License

ManusClaw is released under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 💸 Support The Vision

ManusClaw is free and open-source. If it saves you time, powers your research, or sparks your next project — consider supporting continued development. Every contribution, however small, keeps the work going.

<div align="center">

---

### 🙏 Donate & Support

| Method | Details |
|---|---|
| 🪙 **USDT (TRC20)** | `TH75J4zaMPwhyR3QxEFdwTCgU2Pp3yPUEr` |
| 💼 **WebMoney (WMT)** | `T202226490170` |
| 💵 **WebMoney (WMZ)** | `Z430378899900` |
| 📱 **bKash (BD Local)** | `01310211442` |

---

**Thank you for believing in open-source AI tooling. ❤️**

*Built with passion by [The-JDdev](https://github.com/The-JDdev) and the ManusClaw community.*

[![GitHub](https://img.shields.io/badge/GitHub-The--JDdev-181717?logo=github)](https://github.com/The-JDdev)
[![Stars](https://img.shields.io/github/stars/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw/stargazers)

</div>

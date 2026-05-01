<div align="center">

<!-- HERO IMAGE -->
<img src="https://placehold.co/1200x400/0d1117/58a6ff?text=ManusClaw+v2+%E2%80%94+Autonomous+AI+Agent+Framework&font=raleway" alt="ManusClaw Banner" width="100%" />

<h1>🦾 ManusClaw</h1>

<p><strong>An open-source, terminal-first autonomous AI agent framework.<br/>
DIY Manus · AutoGPT-class orchestration · PAORR reasoning loop · Multi-LLM · No GUI required.</strong></p>

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Build](https://img.shields.io/badge/build-passing-brightgreen?logo=github-actions)](https://github.com/The-JDdev/ManusClaw)
[![Stars](https://img.shields.io/github/stars/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw/stargazers)
[![Forks](https://img.shields.io/github/forks/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw/network/members)
[![Issues](https://img.shields.io/github/issues/The-JDdev/ManusClaw)](https://github.com/The-JDdev/ManusClaw/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange)](https://github.com/The-JDdev/ManusClaw/pulls)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-red)](https://docs.pydantic.dev/latest/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Version](https://img.shields.io/badge/version-2.0.0-blueviolet)](https://github.com/The-JDdev/ManusClaw/releases)

</div>

---

## 📋 Table of Contents

- [What is ManusClaw?](#-what-is-manusclaw)
- [The DIY Manus / AutoGPT Concept](#-the-diy-manus--autogpt-concept)
- [The PAORR Reasoning Loop](#-the-paorr-reasoning-loop)
- [Core Architecture](#-core-architecture)
  - [Agent Layer](#agent-layer)
  - [Memory System](#memory-system)
  - [Tool System](#tool-system)
  - [Planning System](#planning-system)
- [Feature Highlights](#-feature-highlights)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Usage](#-usage)
  - [Single-Prompt Agent](#single-prompt-agent-cli)
  - [Planning Flow](#planning-flow)
  - [MCP Agent](#mcp-agent)
  - [MCP Server](#mcp-server)
  - [Programmatic API](#programmatic-api)
- [Agents Reference](#-agents-reference)
- [Tools Reference](#-tools-reference)
- [LLM Backends](#-llm-backends)
- [MCP Integration](#-mcp-integration)
- [Sandboxing & Safety](#-sandboxing--safety)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Support The Vision](#-support-the-vision)

---

## 🤖 What is ManusClaw?

**ManusClaw** is a production-grade, open-source framework for building **general-purpose autonomous AI agents** that run entirely from the terminal. It is designed for developers, researchers, and power users who want a capable, transparent, and fully self-hosted alternative to commercial agent products.

ManusClaw is conceptually a **DIY Manus / open-source AutoGPT hybrid** — it combines:

- The **structured task decomposition** of Manus (plan before acting)
- The **tool-use loop** of AutoGPT / ReAct (iterative tool calling)
- A proprietary **PAORR reasoning engine** (Plan → Act → Observe → Reflect → Retry)
- A **multi-agent orchestration layer** (PlanningFlow) that dispatches sub-tasks to specialist agents

Unlike commercial alternatives, ManusClaw is:

- **100% open source and MIT licensed**
- **Zero-credential to start** — the built-in MockLLM lets you run the full framework immediately
- **Fully composable** — swap any LLM backend, add any tool, build any agent in <50 lines
- **No GUI, no cloud dependency, no telemetry**

> ManusClaw does not try to hide what it's doing. Every tool call, every retry, every reflection is logged in colour to your terminal. You always know what the agent is thinking.

---

## 🧠 The DIY Manus / AutoGPT Concept

Commercial agent products like Manus, AutoGPT, and Devin all share the same underlying structure. ManusClaw exposes that structure explicitly so you can understand, modify, and extend it.

```
Commercial Agent              ManusClaw equivalent
─────────────────────────     ──────────────────────────────────────
Task input UI              →  CLI prompt / Python API
"The AI thinks..."         →  Explicit LLM reasoning (logged)
Hidden tool calls          →  Observable ToolCollection + ToolResult
Opaque retry logic         →  MAX_TOOL_RETRIES + exponential backoff (visible)
Memory / context           →  Memory (capped, trimmed) + TaskHistory (persistent)
Sub-task routing           →  PlanningFlow + agent selector
Browser automation         →  BrowserUseTool (Playwright)
Code execution sandbox     →  PythonExecute (multiprocessing) + DockerSandbox
```

The key insight: **every commercial agent is just a loop**. ManusClaw makes that loop explicit, debuggable, and hackable.

### What makes it "AutoGPT-class"?

| Capability | ManusClaw |
|---|---|
| Multi-step autonomous reasoning | ✅ PAORR loop |
| Self-correction on tool failure | ✅ Error → LLM → corrected retry |
| Persistent task memory | ✅ TaskHistory + Memory trimming |
| Loop / stuck detection | ✅ Duplicate response + tool-call loop guards |
| Multi-agent task routing | ✅ PlanningFlow |
| Browser automation | ✅ Playwright |
| Code execution | ✅ multiprocessing + Docker sandbox |
| No API key required | ✅ MockLLM |

---

## 🔄 The PAORR Reasoning Loop

The heart of ManusClaw is the **PAORR loop** — a five-phase reasoning cycle that runs inside every agent step.

```
╔══════════════════════════════════════════════════════════════════╗
║                      PAORR CYCLE (one step)                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ┌─────────┐                                                     ║
║  │  PLAN   │  LLM decomposes task into ordered sub-goals.        ║
║  │         │  Explicit numbered plan written on first turn.      ║
║  └────┬────┘                                                     ║
║       │                                                          ║
║  ┌────▼────┐                                                     ║
║  │   ACT   │  LLM selects a tool and arguments via function      ║
║  │         │  calling. Tool is executed (with retry logic).      ║
║  └────┬────┘                                                     ║
║       │                                                          ║
║  ┌────▼────┐                                                     ║
║  │ OBSERVE │  Tool result is captured as an Observation object.  ║
║  │         │  Output, error, exit code all recorded.             ║
║  └────┬────┘                                                     ║
║       │                                                          ║
║  ┌────▼────┐    ┌─────────────────────────────────┐             ║
║  │ REFLECT │    │ Did this solve the sub-goal?     │             ║
║  │         │───▶│ yes → proceed to next sub-goal   │             ║
║  │  (LLM)  │    │ no  → diagnose + inject feedback │             ║
║  └────┬────┘    └─────────────────────────────────┘             ║
║       │ (if not solved)                                          ║
║  ┌────▼────┐                                                     ║
║  │  RETRY  │  Error text fed back to LLM verbatim.              ║
║  │         │  LLM self-corrects (different tool or args).        ║
║  │  max 4  │  Exponential backoff between retries.               ║
║  └─────────┘                                                     ║
╚══════════════════════════════════════════════════════════════════╝
```

### Why PAORR beats simple ReAct

Standard ReAct: Think → Act → Think → Act (no explicit verification)

PAORR forces the agent to **verify** every output before moving on. If verification fails, the exact error is injected back into the conversation and the agent must choose a different path — not just repeat the same call.

This eliminates two of the most common failure modes in autonomous agents:
1. **Hallucinated success** — assuming a tool worked without checking
2. **Stuck loops** — repeating the same failing call indefinitely

---

## 🏗 Core Architecture

### Agent Layer

```
BaseAgent                    ← State machine, Memory, TaskHistory, CORE_DIRECTIVES injection
    └── ReActAgent           ← think() + act() + observe() + reflect() + retry()
            └── ToolCallAgent  ← Structured function calling, _execute_with_retry, error feedback
                    └── Manus          ← Full tool suite, PAORR-aware step(), workspace management
                    └── DataAnalysisAgent  ← Adds DataVisualization tool
                    └── BrowserAgent   ← Browser + search + crawl only
                    └── MCPAgent       ← Dynamic MCP server discovery + tool proxying
```

Every agent that inherits from `BaseAgent` automatically gets:
- **CORE_DIRECTIVES** — hardcoded, aggressive reasoning rules injected into the system prompt
- **TaskHistory** — full PAORR step log (observations, reflections, outcomes)
- **Duplicate-response loop detection** — triggers a nudge to try a different strategy
- **Tool-call loop detection** — detects when the same tool fails repeatedly

### Memory System

ManusClaw implements a **two-tier memory system**:

**Tier 1 — Short-term context buffer (`Memory`)**
```python
Memory(
    messages: list[Message],   # Active conversation window
    max_messages: int = 100    # Hard cap — system messages always preserved
)
```
- Oldest non-system messages are trimmed first when the cap is reached
- Every 5 steps, a `TaskHistory.context_summary()` is injected into the conversation as a "memory refresh"
- Rough token estimate available via `Memory.token_estimate()`

**Tier 2 — Task History log (`TaskHistory`)**
```python
TaskHistory(
    task_id: str,
    original_goal: str,
    steps: list[TaskStep]          # One per PAORR cycle
)

TaskStep(
    step_number: int,
    goal: str,
    observations: list[Observation],  # Tool call results
    reflection: Optional[Reflection], # LLM verdict
    resolved: bool
)
```
The task history is serialisable (Pydantic v2), so it can be saved to disk, inspected, or replayed.

**Loop prevention**

`TaskHistory.is_looping(window=3)` checks if the last N steps all failed with the same tool — if so, an escape prompt is injected forcing the agent to switch strategy.

### Tool System

All tools share a clean, consistent interface:

```python
class BaseTool(ABC):
    name: str
    description: str
    parameters: dict          # JSON Schema for function calling

    async def execute(self, **kwargs) -> ToolResult
    async def cleanup(self)            # Release resources
    def to_openai_schema(self) -> dict # Auto-generate function-calling schema
```

`ToolCollection` manages a named registry of tools and routes calls by name:

```python
collection = ToolCollection(PythonExecute(), WebSearch(), Terminate())
result = await collection.execute("web_search", query="async Python frameworks")
```

`ToolResult` is always returned — never raised:

```python
ToolResult(
    output: Optional[str]        # Success output
    error:  Optional[str]        # Error text (fed back to LLM verbatim)
    system: Optional[str]        # Internal signal (e.g. "terminate")
    base64_image: Optional[str]  # Screenshots, charts
)
```

### Planning System

`PlanningFlow` orchestrates multi-agent task execution:

```
Goal input
    │
    ▼
LLM decomposes goal into N steps (with success criteria per step)
    │
    ▼
For each step:
    ├── Dispatch to Manus or DataAnalysisAgent (based on step content)
    ├── On failure: retry with fresh agent + "RETRY:" prefix
    ├── On second failure: mark BLOCKED, trigger LLM re-planning of remaining steps
    └── On completion: record to completed log
    │
    ▼
Summary output (completed / blocked / timed-out)
```

Re-planning is automatic — if a step is blocked, the LLM is asked to revise the remaining steps given what's already been completed.

---

## ✨ Feature Highlights

| Category | Feature | v2 Upgrade |
|---|---|---|
| 🔄 **Reasoning** | PAORR loop (Plan→Act→Observe→Reflect→Retry) | ✅ New in v2 |
| 🧠 **Directives** | Hardcoded CORE_DIRECTIVES in every agent | ✅ New in v2 |
| 💾 **Memory** | Two-tier (context buffer + TaskHistory) | ✅ New in v2 |
| 🔁 **Self-correction** | Error → LLM → corrected retry (max 4) | ✅ New in v2 |
| 🛡️ **Safety** | Dangerous command blocking, rlimit, 64 KB output cap | ✅ New in v2 |
| 📊 **Observability** | Observation + Reflection Pydantic objects | ✅ New in v2 |
| 🔀 **Re-planning** | PlanningFlow re-plans on blocked steps | ✅ New in v2 |
| 🤖 **Agents** | Manus, DataAnalysis, Browser, MCP | v1 |
| 🛠 **Tools** | 10 built-in tools | v1 |
| 🧠 **LLMs** | OpenAI, Azure, Anthropic, Ollama, MockLLM | v1 |
| 🔗 **MCP** | SSE + stdio client + FastAPI server | v1 |

---

## 🚀 Installation & Setup

### Prerequisites

- Python **3.10** or higher
- `pip` / `uv`
- (Optional) Docker — for sandboxed code execution
- (Optional) Playwright — for browser automation

### 1. Clone

```bash
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
```

### 2. Virtual environment

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Browser (optional)

```bash
playwright install chromium
```

### 5. Verify — zero credentials required

```bash
python main.py "Print 'Hello from ManusClaw!' using Python."
```

Expected output:
```
INFO  | [manus] ▶ Starting run (task_id=a1b2c3d4). max_steps=30
INFO  | [manus] ── Step 1/30 ──
INFO  | [manus] Tool call (1/4): python_execute({"code": "print('Hello from ManusClaw!')"})
INFO  | [manus] Tool result: Hello from ManusClaw!
INFO  | [manus] ── Step 2/30 ──
INFO  | [manus] Tool call (1/4): terminate({"reason": "..."})
INFO  | [manus] ■ Finished. state=AgentState.FINISHED steps=2

FINAL OUTPUT:
Hello from ManusClaw!
```

---

## ⚙️ Configuration

```toml
# config.toml

[llm]
provider    = "openai"    # mock | openai | azure | anthropic | ollama
model       = "gpt-4o"
# api_key = ""            # or OPENAI_API_KEY env var
max_tokens  = 4096
temperature = 0.0
max_retries = 6           # LLM-level retries (network/rate-limit)

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
enable_data_analysis = false   # Set true to enable DataAnalysisAgent
timeout = 3600                 # 60-minute global cap for PlanningFlow

workspace_dir = "workspace"
max_steps     = 30             # Per-agent step cap
```

**Secret management** — never put secrets in `config.toml`:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export LLM_BASE_URL="http://localhost:11434/v1"   # Ollama
```

---

## 💻 Usage

### Single-Prompt Agent (CLI)

```bash
# Argument mode
python main.py "Research the top 5 Python web frameworks, compare them, and save a markdown table to workspace/frameworks.md"

# Interactive mode
python main.py
```

### Planning Flow

```bash
# Decompose a complex goal into sub-steps
python run_flow.py "Collect the latest Bitcoin price, compute a 7-day moving average, and generate a line chart saved to workspace/btc.png"
```

**What happens internally:**
```
1. LLM decomposes goal → 4 steps with success criteria
2. Step 1 → Manus agent → web_search for BTC price
3. Step 2 → DataAnalysisAgent → python_execute to compute MA
4. Step 3 → DataAnalysisAgent → data_viz to generate chart
5. Step 4 → Manus → str_replace_editor to verify output
Summary: 4 completed, 0 blocked.
```

### MCP Agent

```bash
# SSE transport
python run_mcp.py --connection sse --server-url http://localhost:8000 --prompt "List tools"

# stdio transport
python run_mcp.py --connection stdio --server-url /path/to/server --prompt "task"

# Interactive REPL
python run_mcp.py --interactive
```

### MCP Server

```bash
# Host ManusClaw tools for external MCP clients
python run_mcp_server.py --host 0.0.0.0 --port 8000

# Then connect from another ManusClaw instance:
python run_mcp.py --connection sse --server-url http://localhost:8000 --prompt "use bash to list /tmp"
```

### Programmatic API

```python
import asyncio
from app.agent.manus import Manus
from app.tool.base import BaseTool, ToolCollection, ToolResult
from app.agent.toolcall import ToolCallAgent
from app.tool.terminate import Terminate


# ── Basic usage ────────────────────────────────────────────────────
async def basic():
    agent = Manus()
    result = await agent.run("Write and run a Fibonacci function in Python. Save output to workspace/fib.txt")
    print(result)


# ── Custom tool ────────────────────────────────────────────────────
class DatabaseQuery(BaseTool):
    name = "db_query"
    description = "Query the SQLite database and return results as JSON."
    parameters = {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "SQL query to execute."},
        },
        "required": ["sql"],
    }

    async def execute(self, sql: str, **_) -> ToolResult:
        import sqlite3, json
        try:
            conn = sqlite3.connect("my.db")
            cur = conn.execute(sql)
            rows = cur.fetchall()
            return ToolResult(output=json.dumps(rows, default=str))
        except Exception as e:
            return ToolResult(error=str(e))


async def custom_agent():
    tools = ToolCollection(DatabaseQuery(), Terminate())
    agent = ToolCallAgent(tools=tools)
    result = await agent.run("Query the users table and summarise the data.")
    print(result)


# ── Inspect task history ───────────────────────────────────────────
async def with_history():
    agent = Manus()
    await agent.run("Search for Python 3.13 release notes and summarise key changes.")
    
    if agent._task_history:
        print("\n=== Task History ===")
        for step in agent._task_history.steps:
            print(step.summary())


asyncio.run(basic())
```

---

## 🤖 Agents Reference

| Agent | Class | Key capabilities |
|---|---|---|
| **Base** | `BaseAgent` | State machine, Memory, CORE_DIRECTIVES, TaskHistory, loop detection |
| **ReAct** | `ReActAgent` | Full PAORR loop: think/act/observe/reflect/retry |
| **ToolCall** | `ToolCallAgent` | Function calling, `_execute_with_retry` (4 attempts), error self-correction |
| **Manus** | `Manus` | Full tool suite, PAORR-aware step, workspace management, plan-first prompting |
| **DataAnalysis** | `DataAnalysisAgent` | Adds `DataVisualization` tool for chart generation |
| **Browser** | `BrowserAgent` | Browser + WebSearch + Crawl4AI only |
| **MCP** | `MCPAgent` | Dynamic tool discovery from remote MCP servers (stdio/SSE) |

---

## 🛠 Tools Reference

| Tool | Timeout | Guardrails | Description |
|---|---|---|---|
| `python_execute` | 30s (max 120s) | `multiprocessing`, `rlimit` CPU+memory, 64 KB output cap | Execute Python in isolated subprocess |
| `bash` | 30s (max 300s) | Dangerous-pattern blocking, 64 KB cap, session restart on crash | Persistent shell session |
| `str_replace_editor` | — | Path validation | View / create / edit / undo files |
| `browser_use` | 30s per action | Graceful degradation if Playwright absent | Playwright browser |
| `web_search` | 10s per engine | DuckDuckGo → Bing fallback, exp. backoff | Multi-engine web search |
| `crawl` | 15s | Fallback to aiohttp + HTML strip | Clean content extraction |
| `planning` | — | — | Create / update / mark multi-step plans |
| `data_viz` | 30s | subprocess isolation | Matplotlib PNG/HTML chart generation |
| `ask_human` | ∞ (stdin) | — | Interactive user input |
| `terminate` | — | — | Explicit agent stop signal |

---

## 🧠 LLM Backends

| Provider | `provider` value | Notes |
|---|---|---|
| **MockLLM** | `"mock"` | Zero credentials. Uses python_execute on step 1, terminate on step 2. |
| **OpenAI** | `"openai"` | GPT-4o, GPT-4 Turbo, GPT-3.5. `OPENAI_API_KEY`. |
| **Azure OpenAI** | `"azure"` | Set `base_url` to Azure endpoint. |
| **Anthropic** | `"anthropic"` | Claude 3.x. `ANTHROPIC_API_KEY`. |
| **Ollama** | `"ollama"` | Local: Llama 3, Mistral, Qwen, etc. Set `base_url`. |

All providers use the same retry wrapper: exponential backoff (1–60s, 6 attempts).
`TokenLimitExceeded` is non-retryable and raised immediately.

---

## 🔗 MCP Integration

ManusClaw is a **full MCP participant** — it speaks the protocol on both sides:

**Client side** — `MCPClient` discovers and proxies remote tools:
```python
client = MCPClient(name="remote", transport="sse", url="http://server:8000")
tools = await client.connect()        # discovers tools via tools/list
result = await client.call_tool("bash", {"command": "ls /"})
```

**Server side** — `run_mcp_server.py` exposes local tools:
```
GET /tools/list   → discover Bash, BrowserUseTool, StrReplaceEditor, Terminate
POST /tools/call  → invoke any tool
GET /healthz      → liveness check
```

Supported transports: **stdio** (subprocess) and **SSE** (HTTP).

---

## 🐳 Sandboxing & Safety

### Python execution safety

- **Process isolation**: `multiprocessing.Process` — separate memory space
- **CPU limit**: `resource.setrlimit(RLIMIT_CPU)` — max 60 CPU seconds
- **Memory limit**: `resource.setrlimit(RLIMIT_AS)` — max 512 MB virtual
- **Wall-clock timeout**: configurable, hard-capped at 120s
- **Output cap**: 64 KB — prevents print-flood DoS

### Bash safety

- **Dangerous pattern detection**: `rm -rf /`, fork bombs, `dd`, `mkfs` → blocked
- **Timeout**: configurable, hard-capped at 300s — session restarted on timeout
- **Output cap**: 64 KB — truncated with notice
- **Non-zero exit code**: surfaced as `ToolResult.error` for LLM self-correction

### Docker sandbox (optional)

```toml
[sandbox]
enabled      = true
docker_image = "python:3.11-slim"
memory_limit = "256m"
timeout      = 30
```

Containers run with `--network=none` and are terminated after execution.

---

## 📁 Project Structure

```
ManusClaw/
├── app/
│   ├── agent/
│   │   ├── base.py          ← BaseAgent: state, memory, CORE_DIRECTIVES, TaskHistory
│   │   ├── react.py         ← ReActAgent: full PAORR loop with reflection
│   │   ├── toolcall.py      ← ToolCallAgent: function calling + retry + error injection
│   │   ├── manus.py         ← Manus: orchestration, plan-first prompt, periodic self-check
│   │   ├── data_analysis.py ← DataAnalysisAgent: adds DataVisualization
│   │   ├── browser.py       ← BrowserAgent: browser-only surface
│   │   └── mcp.py           ← MCPAgent: dynamic remote tool discovery
│   ├── tool/
│   │   ├── base.py          ← BaseTool, ToolResult, ToolCollection
│   │   ├── python_execute.py ← multiprocessing sandbox, rlimit, 64 KB cap
│   │   ├── bash.py          ← persistent shell, dangerous-cmd guard, timeout
│   │   ├── str_replace_editor.py
│   │   ├── browser_use_tool.py
│   │   ├── web_search.py
│   │   ├── crawl4ai.py
│   │   ├── planning.py
│   │   ├── data_viz.py
│   │   ├── ask_human.py
│   │   └── terminate.py
│   ├── flow/
│   │   └── planning.py      ← PlanningFlow: LLM planning, re-planning, agent dispatch
│   ├── mcp/
│   │   ├── client.py        ← MCPClient (stdio + SSE)
│   │   └── server.py        ← FastAPI MCP server
│   ├── sandbox/
│   │   └── docker.py        ← DockerSandbox + DaytonaSandbox stub
│   ├── llm/
│   │   └── llm.py           ← LLM + MockLLM + retry wrapper
│   ├── schema.py            ← Message, Memory, Observation, Reflection, TaskHistory
│   ├── config.py            ← TOML singleton + env var fallbacks
│   ├── logger.py            ← Loguru: colour stdout + rotating file logs
│   └── exceptions.py        ← TokenLimitExceeded, ToolError, etc.
├── main.py                  ← Single-prompt CLI
├── run_flow.py              ← PlanningFlow CLI
├── run_mcp.py               ← MCP agent CLI
├── run_mcp_server.py        ← MCP server host
├── config.toml              ← Default configuration
├── requirements.txt
├── workspace/               ← Agent output directory
└── logs/                    ← Rotating structured logs
```

---

## 🤝 Contributing

1. Fork → `git checkout -b feat/my-feature`
2. Write typed, async Python (Pydantic v2)
3. Follow `BaseTool` contract — always return `ToolResult`, never raise
4. Log with `from app.logger import logger`, not `print()`
5. Open a PR with a clear description of what and why

```bash
# Dev setup
git clone https://github.com/The-JDdev/ManusClaw.git
cd ManusClaw
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 💸 Support The Vision

ManusClaw is free, open-source, and actively developed. If it powers your research, saves you hours, or inspires your next project — consider supporting continued development.

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

**Every contribution keeps the framework alive and growing. Thank you. ❤️**

*Built with passion by [The-JDdev](https://github.com/The-JDdev) and the ManusClaw community.*

[![GitHub](https://img.shields.io/badge/GitHub-The--JDdev-181717?logo=github)](https://github.com/The-JDdev)
[![Stars](https://img.shields.io/github/stars/The-JDdev/ManusClaw?style=social)](https://github.com/The-JDdev/ManusClaw/stargazers)

</div>

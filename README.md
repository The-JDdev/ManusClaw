# ManusClaw v4.0

**The ultimate autonomous AI agent framework** by The-JDdev (SHS Shobuj).

A self-improving assistant that runs everywhere — CLI, web dashboard, messaging platforms — and gets smarter over time by creating skills from complex tasks and persisting memory across sessions.

## What's New in v4.0 (Hermes Integration)

- **Multi-Provider LLM** — OpenAI, Anthropic, Mistral, AWS Bedrock, Google Gemini + any OpenAI-compatible endpoint
- **Credential Pool** — Multiple API keys per provider with priority ordering and auto-rotation on exhaustion
- **Token Budget** — Tracks input/output/cache/reasoning tokens per session with grace call for cleanup
- **FTS5 Cross-Session Search** — Full-text search across all past sessions and tool calls
- **Session Branching** — Fork sessions with parent_session_id for parallel exploration
- **Context Compression** — Summarize context when approaching token limits, chain sessions
- **Skills System** — Create, patch, delete reusable skills (Markdown + YAML frontmatter), injected as user messages
- **Auto-Skill Suggestion** — After 5+ tool calls, agent suggests creating a skill
- **Memory CRUD** — Read/write MEMORY.md and USER.md for persistent cross-session context
- **Delegate Tool** — Spawn isolated subagents in thread pool for parallel subtasks
- **Cross-Session Search Tool** — FTS5 search across all past work
- **Image Generation** — FAL.ai integration with mock fallback
- **Node.js Execution** — Run JavaScript code alongside Python
- **Named Profiles** — `MANUSCLAW_PROFILE=work` loads `~/.manusclaw/profiles/work/`
- **Messaging Gateway** — Telegram, Discord, Slack adapters (stub no-ops when unconfigured)
- **Cron Scheduler** — croniter-based job scheduler persisted as YAML
- **Rich CLI** — prompt_toolkit input, Rich output, slash commands, animated spinner, skin engine
- **4 Built-in Skins** — default (gold), ares (red), mono (white), slate (blue)
- **Secret Redaction** — Optionally scrub API keys from logs

## Quick Start

```bash
pip install -r requirements.txt
playwright install chromium

# Interactive CLI
python -m app.cli

# Single-shot
python main.py "Analyse this CSV file: data.csv"

# Web server
python run_server.py

# With profile
MANUSCLAW_PROFILE=work python -m app.cli
```

## Configuration

Config loads in this priority order:
1. Environment variables
2. `~/.manusclaw/profiles/<MANUSCLAW_PROFILE>/.env`
3. `~/.manusclaw/profiles/<MANUSCLAW_PROFILE>/config.yaml`
4. `~/.manusclaw/.env`
5. `~/.manusclaw/config.yaml`
6. `./config.toml` (legacy)
7. Built-in defaults (MockLLM, safe for immediate use)

## PAORR Loop

Every agent step follows:
- **Plan** — Decompose task into ordered sub-goals
- **Act** — Execute one tool call
- **Observe** — Read and extract key findings from output
- **Reflect** — Did this solve the sub-goal? (scored 0-1)
- **Retry** — If not solved: diagnose, try different tool/args

## Tools

| Tool | Description |
|------|-------------|
| `python_execute` | Isolated Python subprocess |
| `node_execute` | Isolated Node.js subprocess |
| `bash` | Persistent shell |
| `str_replace_editor` | File view/create/edit |
| `browser_use` | Playwright browser automation |
| `web_search` | Multi-engine search |
| `crawl` | URL content extraction |
| `image_generate` | FAL.ai image generation |
| `memory` | Read/write MEMORY.md and USER.md |
| `skill_manager` | Create/patch/delete/list skills |
| `cross_session_search` | FTS5 search across all sessions |
| `delegate` | Spawn isolated subagent |
| `ask_human` | Request user clarification |
| `terminate` | Signal task completion |

## Testing

```bash
pytest -n 4  # 4 parallel workers
pytest tests/test_agent_loop.py -v
pytest tests/test_session_db.py -v
```

## Architecture

```
app/
  agent/       # BaseAgent, ReActAgent, ToolCallAgent, Manus, roles, orchestrator
  llm/         # LLM router, credential pool, token tracker, Mistral, Bedrock clients
  db/          # SessionDB with FTS5, WAL, branching, compression
  tool/        # All tools including memory, delegate, skills, image gen, Node.js
  skills/      # SkillEngine + built-in skills library
  messaging/   # Gateway, Telegram/Discord/Slack adapters
  flow/        # PlanningFlow with PAORR-aware step dispatch
  memory/      # ShortTermMemory, LongTermMemory
  permissions/ # PermissionGate (3-tier: allow/ask/deny)
  server/      # FastAPI server with WebSocket streaming
  config.py    # Multi-source config with named profiles
  cli.py       # Rich + prompt_toolkit interactive CLI
  cron.py      # croniter-based job scheduler
```

**Created by The-JDdev (SHS Shobuj)**

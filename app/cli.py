from __future__ import annotations

"""
ManusClaw CLI — prompt_toolkit input layer + Rich output.

Layout:
  - Fixed header: model name, session info, token usage
  - Scrollable transcript with role-emoji prefixes
  - Fixed footer input area (multi-line, slash-command autocomplete)
  - Animated spinner during API calls
  - Skin engine (YAML-based, 4 built-in skins: default/ares/mono/slate)

Slash commands:
  /model   — show/switch LLM model
  /skills  — list loaded skills
  /tools   — list available tools
  /memory  — show MEMORY.md content
  /compress — compress current session context
  /new     — start new session
  /resume  — resume a past session
  /branch  — branch current session
  /help    — show commands
  /exit    — quit
"""

import asyncio
import sys
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Skin definitions (data-driven, YAML-loadable)
# ──────────────────────────────────────────────────────────────────────────────

SKINS = {
    "default": {"border": "gold1",          "accent": "yellow",  "user": "cyan",     "agent": "green",  "tool": "magenta", "error": "red"},
    "ares":    {"border": "red1",            "accent": "red",     "user": "white",    "agent": "red",    "tool": "orange1", "error": "bright_red"},
    "mono":    {"border": "white",           "accent": "white",   "user": "white",    "agent": "bright_white", "tool": "grey70", "error": "white"},
    "slate":   {"border": "steel_blue1",     "accent": "blue",    "user": "sky_blue1","agent": "pale_green1","tool": "orchid","error": "red"},
}

ROLE_EMOJI = {"user": "👤", "assistant": "🤖", "tool": "🔧", "system": "⚙"}

SLASH_COMMANDS = [
    "/model", "/skills", "/tools", "/memory", "/compress",
    "/new", "/resume", "/branch", "/help", "/exit",
]


def _get_skin(name: str = "default") -> dict:
    """Load skin: check ~/.manusclaw/skins/<name>.yaml first, then built-ins."""
    from pathlib import Path
    import os
    skin_file = Path(os.getenv("MANUSCLAW_HOME", Path.home() / ".manusclaw")) / "skins" / f"{name}.yaml"
    if skin_file.exists():
        try:
            import yaml
            data = yaml.safe_load(skin_file.read_text()) or {}
            if data:
                return {**SKINS.get("default", {}), **data}
        except Exception:
            pass
    return SKINS.get(name, SKINS["default"])


# ──────────────────────────────────────────────────────────────────────────────
# Rich-based output helpers
# ──────────────────────────────────────────────────────────────────────────────

def _print_header(skin: dict, model: str, session_id: str, step: int = 0) -> None:
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(Panel(
            f"[bold {skin['accent']}]ManusClaw[/] | model: {model} | session: {session_id[:8]} | step: {step}",
            border_style=skin["border"],
            expand=True,
        ))
    except ImportError:
        print(f"=== ManusClaw | {model} | {session_id[:8]} ===")


def _print_message(role: str, content: str, skin: dict) -> None:
    emoji = ROLE_EMOJI.get(role, "•")
    color = skin.get(role if role in ("user", "tool", "error") else "agent", "white")
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()
        label = f"[{color}]{emoji} {role.upper()}[/{color}]"
        if role == "assistant":
            console.print(f"{label}")
            console.print(Markdown(content))
        else:
            console.print(f"{label}: {content[:2000]}")
    except ImportError:
        print(f"{emoji} {role.upper()}: {content[:500]}")


def _print_tool_activity(tool_name: str, args_preview: str, skin: dict) -> None:
    try:
        from rich.console import Console
        console = Console()
        console.print(f"  [{skin['tool']}]🔧 {tool_name}[/] — {args_preview[:80]}")
    except ImportError:
        print(f"  [TOOL] {tool_name}: {args_preview[:80]}")


# ──────────────────────────────────────────────────────────────────────────────
# Spinner context manager
# ──────────────────────────────────────────────────────────────────────────────

class Spinner:
    """Contextual spinner using Rich if available, otherwise plain text."""

    def __init__(self, verb: str = "thinking", skin: Optional[dict] = None) -> None:
        self.verb = verb
        self.skin = skin or SKINS["default"]
        self._status = None

    def __enter__(self):
        try:
            from rich.console import Console
            from rich import get_console
            self._console = Console()
            self._status = self._console.status(
                f"[{self.skin['accent']}]{self.verb}...[/]", spinner="dots"
            )
            self._status.__enter__()
        except ImportError:
            print(f"  {self.verb}...", end="", flush=True)
        return self

    def __exit__(self, *args):
        if self._status:
            self._status.__exit__(*args)
        else:
            print(" done")


# ──────────────────────────────────────────────────────────────────────────────
# Slash command handlers
# ──────────────────────────────────────────────────────────────────────────────

async def _handle_slash(cmd: str, agent=None, session_id: str = "") -> Optional[str]:
    parts = cmd.strip().split(None, 1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if command == "/help":
        return "Commands:\n" + "\n".join(f"  {c}" for c in SLASH_COMMANDS)

    if command == "/model":
        from app.config import Config
        cfg = Config.get()
        if arg:
            cfg._data.llm.model = arg
            return f"Model set to: {arg}"
        return f"Current model: {cfg.llm.model} (provider: {cfg.llm.provider})"

    if command == "/skills":
        try:
            from app.skills.skill_engine import get_skill_engine
            skills = get_skill_engine().list_skills()
            if not skills:
                return "No skills loaded."
            return "\n".join(f"  {s.name} v{s.version}: {s.description[:60]}" for s in skills)
        except Exception as e:
            return f"Skills error: {e}"

    if command == "/tools":
        if agent and hasattr(agent, "tools"):
            names = list(agent.tools._tools.keys())
            return "Tools: " + ", ".join(names)
        return "No agent active."

    if command == "/memory":
        from pathlib import Path
        mf = Path("workspace/MEMORY.md")
        if mf.exists():
            return mf.read_text()
        return "MEMORY.md is empty."

    if command == "/compress":
        if session_id and agent:
            from app.db.session import SessionDB
            db = SessionDB()
            summary = agent._task_history.context_summary() if agent._task_history else "No task history."
            await db.compress_session(session_id, summary)
            db.close()
            return f"Session {session_id[:8]} compressed."
        return "No active session."

    if command == "/new":
        return "NEW_SESSION"

    if command == "/branch":
        if session_id:
            from app.db.session import SessionDB
            db = SessionDB()
            new_sid = await db.branch_session(session_id, arg or None)
            db.close()
            return f"Branched session: {new_sid}"
        return "No active session to branch."

    if command == "/resume":
        from app.db.session import SessionDB
        db = SessionDB()
        sessions = await db.get_sessions(limit=10)
        db.close()
        if not sessions:
            return "No sessions found."
        lines = ["Recent sessions:"]
        for s in sessions:
            lines.append(f"  {s['id']} | {s['state']} | {s['goal'][:50]}")
        return "\n".join(lines)

    if command == "/exit":
        return "EXIT"

    return f"Unknown command: {command}. Type /help for help."


# ──────────────────────────────────────────────────────────────────────────────
# prompt_toolkit input layer
# ──────────────────────────────────────────────────────────────────────────────

def _get_completer():
    try:
        from prompt_toolkit.completion import WordCompleter
        return WordCompleter(SLASH_COMMANDS, pattern=r"^/\w*")
    except ImportError:
        return None


def _get_session():
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from pathlib import Path
        history_file = Path.home() / ".manusclaw" / ".cli_history"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        return PromptSession(history=FileHistory(str(history_file)))
    except ImportError:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Main interactive loop
# ──────────────────────────────────────────────────────────────────────────────

async def _interactive_loop(skin_name: str = "default") -> None:
    from app.agent.manus import Manus
    from app.config import Config

    skin = _get_skin(skin_name)
    cfg = Config.get()
    model_name = cfg.llm.model
    agent = Manus()
    session_id = ""
    pt_session = _get_session()
    completer = _get_completer()

    _print_header(skin, model_name, "new", 0)

    try:
        from rich.console import Console
        console = Console()
        console.print(f"[{skin['accent']}]ManusClaw ready. Type your task or /help for commands.[/]\n")
    except ImportError:
        print("ManusClaw ready. Type your task or /help for commands.\n")

    while True:
        try:
            if pt_session and completer:
                from prompt_toolkit import prompt
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: pt_session.prompt("You> ", completer=completer, multiline=False)
                )
            else:
                user_input = await asyncio.get_event_loop().run_in_executor(None, input, "You> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            result = await _handle_slash(user_input, agent=agent, session_id=session_id)
            if result == "EXIT":
                print("Goodbye.")
                break
            if result == "NEW_SESSION":
                agent = Manus()
                session_id = ""
                print("Started new session.")
                continue
            if result:
                _print_message("system", result, skin)
            continue

        # Regular prompt — run agent
        _print_message("user", user_input, skin)
        verb = "thinking" if "?" not in user_input else "researching"

        try:
            with Spinner(verb=verb, skin=skin):
                result = await agent.run(user_input)
            session_id = agent._session_id or ""
            _print_message("assistant", result, skin)
            _print_header(skin, model_name, session_id, agent._step_count)
        except Exception as e:
            _print_message("error", f"Error: {e}", skin)

        # Reset agent state for next prompt
        from app.schema import AgentState
        from app.memory.short_term import ShortTermMemory
        agent.state = AgentState.IDLE
        agent._step_count = 0
        agent.memory = ShortTermMemory()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="ManusClaw autonomous AI agent")
    parser.add_argument("prompt", nargs="*", help="Task prompt (omit for interactive mode)")
    parser.add_argument("--skin", default="default", choices=list(SKINS.keys()), help="UI skin")
    parser.add_argument("--model", help="Override LLM model")
    parser.add_argument("--profile", help="Config profile name")
    parser.add_argument("--no-color", action="store_true", help="Disable colors")
    args = parser.parse_args()

    if args.profile:
        import os
        os.environ["MANUSCLAW_PROFILE"] = args.profile

    if args.model:
        import os
        os.environ["LLM_MODEL_OVERRIDE"] = args.model

    if args.prompt:
        # Single-shot mode
        prompt_text = " ".join(args.prompt)

        async def _run_once():
            from app.agent.manus import Manus
            agent = Manus()
            skin = _get_skin(args.skin)
            with Spinner(verb="thinking", skin=skin):
                result = await agent.run(prompt_text)
            _print_message("assistant", result, skin)

        asyncio.run(_run_once())
    else:
        # Interactive mode
        asyncio.run(_interactive_loop(skin_name=args.skin))


if __name__ == "__main__":
    main()

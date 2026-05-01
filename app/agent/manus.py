from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.agent.toolcall import ToolCallAgent
from app.config import Config
from app.logger import logger
from app.schema import AgentState, Message, Reflection, TaskStep
from app.tool.ask_human import AskHuman
from app.tool.base import ToolCollection
from app.tool.bash import Bash
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.crawl4ai import Crawl4AITool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.terminate import Terminate
from app.tool.web_search import WebSearch


# ---------------------------------------------------------------------------
# Manus system prompt — aggressive, opinionated, directive
# ---------------------------------------------------------------------------

MANUS_SYSTEM_PROMPT = """\
You are MANUS — a general-purpose autonomous AI agent built for deep, multi-step reasoning.

Your architecture follows the PAORR loop:
  PLAN    → Decompose the task into clear, ordered sub-goals
  ACT     → Call a tool to execute one sub-goal
  OBSERVE → Read the tool output carefully and extract key findings
  REFLECT → Ask yourself: did this output solve the sub-goal? (yes/no, why)
  RETRY   → If not solved: diagnose the failure and choose a different approach

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TOOLBOX:
  • python_execute  — run isolated Python code (multiprocessing, 30s timeout)
  • bash            — persistent shell session (commands, file ops, git, etc.)
  • str_replace_editor — view / create / edit any file on disk
  • browser_use     — Playwright browser (navigate, click, screenshot, JS)
  • web_search      — multi-engine search with fallback
  • crawl           — extract clean text from any URL
  • ask_human       — request clarification from the user
  • terminate       — signal task completion (ONLY when truly done)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PLANNING PHASE (do this FIRST for any non-trivial task):
  Before using any other tool, write an explicit numbered plan in your first
  response. Example:
    1. Search for X to gather context
    2. Write a Python script that does Y
    3. Run the script and verify output
    4. Save result to workspace/result.txt
    5. Terminate with summary

REFLECTION RULES:
  - After EVERY tool call, ask: "Did this move me closer to the goal?"
  - If a tool returns an error: diagnose → change approach → retry
  - If a tool returns unexpected output: verify → extract useful parts → adapt
  - If you've tried the same approach 3 times: STOP and try something else

QUALITY RULES:
  - Never fabricate output. If a tool returns nothing, say so.
  - Always verify file writes with str_replace_editor view after creating.
  - For code, always RUN it (python_execute/bash) and check the output.
  - Save every meaningful artefact to workspace/.

TERMINATION:
  Call terminate ONLY when all sub-goals are complete and verified.
  Your terminate reason must summarize what was accomplished and where
  outputs were saved.
"""

# ---------------------------------------------------------------------------
# Reflection prompt (used by Manus.reflect_on_step)
# ---------------------------------------------------------------------------

_MANUS_REFLECT_PROMPT = """\
After the tool execution above, answer these questions internally:

1. Sub-goal status: Was this sub-goal SOLVED? (yes/no)
2. Evidence: What in the output confirms this? 
3. Next step: What is the very next sub-goal to pursue?

If the sub-goal was NOT solved, explain what went wrong and what you will try
differently. Then proceed with your next tool call.
"""


class Manus(ToolCallAgent):
    name = "manus"
    system_prompt = MANUS_SYSTEM_PROMPT

    def __init__(self) -> None:
        workspace = Path(Config.get().workspace_dir)
        workspace.mkdir(exist_ok=True)

        tools = ToolCollection(
            PythonExecute(),
            StrReplaceEditor(),
            BrowserUseTool(),
            Bash(),
            WebSearch(),
            Crawl4AITool(),
            AskHuman(),
            Terminate(),
        )
        super().__init__(tools=tools)

    # ------------------------------------------------------------------
    # Enhanced step with built-in reflection injection
    # ------------------------------------------------------------------

    async def step(self) -> Optional[str]:
        """
        PAORR step for Manus:
          1. THINK — LLM selects tool (with explicit reasoning)
          2. ACT   — tool executed with retry/error-feedback loop
          3. OBSERVE — result recorded in TaskHistory
          4. REFLECT — inject a reflection prompt to keep the LLM on track
        """
        if self._task_history:
            self._task_history.add_step(f"step {self._step_count}")

        # THINK + ACT (inherited from ToolCallAgent)
        await self.think()
        result = await self.act("")

        if self.state == AgentState.FINISHED:
            return result

        # REFLECT — inject a lightweight self-check into the conversation
        # so the LLM naturally stays on task without an extra LLM call
        if result and self._step_count % 3 == 0:
            history_ctx = (
                self._task_history.context_summary(max_steps=3)
                if self._task_history
                else ""
            )
            reflect_injection = (
                "\n[SELF-CHECK]\n"
                + (history_ctx + "\n" if history_ctx else "")
                + _MANUS_REFLECT_PROMPT
            )
            self.memory.add(Message.user(reflect_injection))

        return result

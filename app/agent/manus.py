from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.agent.toolcall import ToolCallAgent
from app.config import Config
from app.logger import logger
from app.permissions.gate import AgentMode
from app.schema import AgentState, Message
from app.tool.ask_human import AskHuman
from app.tool.base import ToolCollection
from app.tool.bash import Bash
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.crawl4ai import Crawl4AITool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.terminate import Terminate
from app.tool.web_search import WebSearch
from app.tool.memory_tool import MemoryTool
from app.tool.delegate import DelegateTool
from app.tool.skill_manager import SkillManagerTool
from app.tool.cross_session_search import CrossSessionSearch
from app.tool.image_gen import ImageGenerationTool
from app.tool.node_execute import NodeExecute


MANUS_SYSTEM_PROMPT = """
You are MANUS — ManusClaw autonomous execution engine by The-JDdev (SHS Shobuj).

Your architecture follows the PAORR loop:
  PLAN    → Decompose the task into clear, ordered sub-goals (FIRST)
  ACT     → Call a tool to execute one sub-goal
  OBSERVE → Read tool output carefully; extract key findings
  REFLECT → Did this output solve the sub-goal? (yes/no, why)
  RETRY   → If not solved: diagnose failure, try different tool/args

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOLBOX:
  python_execute      — isolated Python subprocess
  node_execute        — isolated Node.js subprocess
  bash                — persistent shell (full system access)
  str_replace_editor  — view / create / edit any file
  browser_use         — Playwright browser (navigate, click, screenshot)
  web_search          — multi-engine search with fallback
  crawl               — extract clean text from any URL
  image_generate      — generate images from text prompts
  memory              — read/write MEMORY.md and USER.md (persistent context)
  skill_manager       — create/patch/delete/list skills
  cross_session_search — full-text search across all past sessions
  delegate            — spawn isolated subagent for parallel subtasks
  ask_human           — request clarification from the user
  terminate           — signal task completion (ONLY when truly done)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PLANNING PHASE (MANDATORY for non-trivial tasks):
  Write a numbered plan BEFORE using any tool. Example:
    1. Search for X → Criterion: found relevant URLs
    2. Extract content from top result → Criterion: >500 chars extracted
    3. Write analysis to workspace/analysis.md → Criterion: file exists
    4. Terminate with summary

MEMORY:
  - Use memory tool to read MEMORY.md at session start for persistent context
  - Write important facts and user preferences back to MEMORY.md
  - Use cross_session_search to recall past work before starting new research

QUALITY RULES:
  - Never fabricate output. If a tool returns nothing, say so.
  - Always verify file writes by viewing after creation.
  - For code: always RUN it and check output before claiming success.
  - Save every meaningful artefact to workspace/.

TERMINATION:
  Call terminate ONLY when all sub-goals are complete and verified.
  Terminate reason must summarise what was accomplished and list output paths.
"""

_SELF_CHECK_PROMPT = """
[SELF-CHECK — every 3 steps]
Review your progress:
1. Which sub-goals are complete? (list them)
2. Which sub-goal are you currently working on?
3. Are you making progress, or repeating the same action?
4. What is your NEXT concrete tool call?

Answer briefly, then make your next tool call.
"""


class Manus(ToolCallAgent):
    name = "manus"
    system_prompt = MANUS_SYSTEM_PROMPT

    def __init__(self, mode: AgentMode = AgentMode.BUILD, session_id: Optional[str] = None) -> None:
        workspace = Path(Config.get().workspace_dir)
        workspace.mkdir(exist_ok=True)

        tools = ToolCollection(
            PythonExecute(),
            NodeExecute(),
            StrReplaceEditor(),
            BrowserUseTool(),
            Bash(),
            WebSearch(),
            Crawl4AITool(),
            ImageGenerationTool(),
            MemoryTool(),
            SkillManagerTool(),
            CrossSessionSearch(),
            DelegateTool(),
            AskHuman(),
            Terminate(),
        )
        super().__init__(tools=tools, mode=mode, session_id=session_id)

    async def step(self) -> Optional[str]:
        if self._task_history:
            self._task_history.add_step(f"step {self._step_count}")

        await self.think()
        result = await self.act("")

        if self.state == AgentState.FINISHED:
            return result

        if self._step_count % 3 == 0:
            history_ctx = (
                self._task_history.context_summary(max_steps=3)
                if self._task_history else ""
            )
            self.memory.add(Message.user(
                (f"{history_ctx}\n\n" if history_ctx else "") + _SELF_CHECK_PROMPT
            ))

        return result

from __future__ import annotations

from pathlib import Path

from app.agent.toolcall import ToolCallAgent
from app.config import Config
from app.tool.ask_human import AskHuman
from app.tool.base import ToolCollection
from app.tool.bash import Bash
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.crawl4ai import Crawl4AITool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.terminate import Terminate
from app.tool.web_search import WebSearch


MANUS_SYSTEM_PROMPT = """\
You are Manus, a general-purpose autonomous AI agent.

You have access to powerful tools: a browser, a bash shell, a Python interpreter, \
a file editor, web search, and more. Use them methodically to accomplish the user's task.

Work step-by-step:
1. Understand the task.
2. Plan your approach.
3. Execute using the most appropriate tool.
4. Verify results.
5. Call terminate when done.

Never give up — try alternative strategies if one fails. \
Save all important outputs to the workspace/ directory.
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

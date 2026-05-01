from __future__ import annotations

from app.agent.manus import Manus
from app.tool.base import ToolCollection
from app.tool.bash import Bash
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.crawl4ai import Crawl4AITool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.terminate import Terminate
from app.tool.web_search import WebSearch
from app.tool.ask_human import AskHuman
from app.tool.data_viz import DataVisualization


DATA_ANALYSIS_PROMPT = """\
You are a data analysis AI agent specialised in exploring datasets, computing statistics, \
and producing charts. Use Python for computation and the data_viz tool to generate charts. \
Save all outputs to workspace/.
"""


class DataAnalysisAgent(Manus):
    name = "data_analysis"
    system_prompt = DATA_ANALYSIS_PROMPT

    def __init__(self) -> None:
        # Call ToolCallAgent.__init__ directly to avoid Manus's tool setup
        from app.agent.toolcall import ToolCallAgent
        from app.agent.react import ReActAgent
        from app.agent.base import BaseAgent
        BaseAgent.__init__(self)
        from app.llm.llm import LLM
        self.llm = LLM()
        tools = ToolCollection(
            PythonExecute(),
            StrReplaceEditor(),
            BrowserUseTool(),
            Bash(),
            WebSearch(),
            Crawl4AITool(),
            DataVisualization(),
            AskHuman(),
            Terminate(),
        )
        self.tools = tools

from __future__ import annotations

import asyncio
import json
import random
from typing import Optional

from app.agent.react import ReActAgent
from app.logger import logger
from app.schema import AgentState, Message, ToolCall, Role
from app.tool.base import ToolCollection
from app.tool.selector import ToolSelector
from app.tool.terminate import Terminate


# Remaining file content unchanged...

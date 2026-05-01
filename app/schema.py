from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Roles & States
# ---------------------------------------------------------------------------

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Message primitives
# ---------------------------------------------------------------------------

class Function(BaseModel):
    name: str
    arguments: str  # JSON string


class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: Function


class Message(BaseModel):
    role: Role
    content: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(
        cls,
        content: Optional[str] = None,
        tool_calls: Optional[list[ToolCall]] = None,
    ) -> "Message":
        return cls(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)

    @classmethod
    def tool(cls, content: str, tool_call_id: str, name: str) -> "Message":
        return cls(role=Role.TOOL, content=content, tool_call_id=tool_call_id, name=name)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role.value}
        if self.content is not None:
            d["content"] = self.content
        if self.tool_calls:
            d["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


# ---------------------------------------------------------------------------
# Memory — context-window-aware
# ---------------------------------------------------------------------------

class Memory(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    max_messages: int = 100

    def add(self, message: Message) -> None:
        self.messages.append(message)
        self._trim()

    def _trim(self) -> None:
        if len(self.messages) <= self.max_messages:
            return
        # Always keep system messages; trim oldest non-system first
        system = [m for m in self.messages if m.role == Role.SYSTEM]
        rest = [m for m in self.messages if m.role != Role.SYSTEM]
        keep = max(self.max_messages - len(system), 10)
        self.messages = system + rest[-keep:]

    def to_list(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self.messages]

    def clear(self) -> None:
        self.messages = []

    def token_estimate(self) -> int:
        """Rough token estimate: ~4 chars per token."""
        total = sum(len(m.content or "") for m in self.messages)
        return total // 4


# ---------------------------------------------------------------------------
# PAORR loop primitives — Plan, Act, Observe, Reflect, Retry
# ---------------------------------------------------------------------------

class Observation(BaseModel):
    """Result of a single tool execution."""
    tool_name: str
    args: dict[str, Any]
    output: Optional[str]
    error: Optional[str]
    success: bool
    attempt: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def summary(self) -> str:
        if self.success:
            out = (self.output or "")[:400]
            return f"[{self.tool_name}] ✓ {out}"
        return f"[{self.tool_name}] ✗ ERROR: {self.error}"


class Reflection(BaseModel):
    """LLM-generated reflection on whether an observation solved the goal."""
    step_goal: str
    observation_summary: str
    solved: bool
    reason: str
    next_action: Optional[str] = None

    def to_prompt(self) -> str:
        status = "SOLVED" if self.solved else "NOT SOLVED"
        lines = [
            f"Reflection [{status}]:",
            f"  Goal: {self.step_goal}",
            f"  Observation: {self.observation_summary}",
            f"  Reason: {self.reason}",
        ]
        if self.next_action:
            lines.append(f"  Next action: {self.next_action}")
        return "\n".join(lines)


class TaskStep(BaseModel):
    """A single step in the PAORR execution history."""
    step_number: int
    goal: str
    observations: list[Observation] = Field(default_factory=list)
    reflection: Optional[Reflection] = None
    resolved: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def summary(self) -> str:
        status = "✓" if self.resolved else "✗"
        obs_summaries = " | ".join(o.summary() for o in self.observations[-3:])
        return f"Step {self.step_number} {status}: {self.goal[:60]} → {obs_summaries}"


class TaskHistory(BaseModel):
    """Persistent log of all steps across a task run."""
    task_id: str
    original_goal: str
    steps: list[TaskStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def add_step(self, goal: str) -> TaskStep:
        step = TaskStep(step_number=len(self.steps) + 1, goal=goal)
        self.steps.append(step)
        return step

    def last_step(self) -> Optional[TaskStep]:
        return self.steps[-1] if self.steps else None

    def context_summary(self, max_steps: int = 5) -> str:
        """Compact summary of recent history for injection into prompts."""
        recent = self.steps[-max_steps:]
        if not recent:
            return "No prior steps."
        lines = ["=== Task History (recent steps) ==="]
        for s in recent:
            lines.append(s.summary())
        lines.append("=== End History ===")
        return "\n".join(lines)

    def is_looping(self, window: int = 3) -> bool:
        """Detect if the last N steps all failed with the same tool."""
        if len(self.steps) < window:
            return False
        recent = self.steps[-window:]
        if all(not s.resolved for s in recent):
            tool_names = [
                o.tool_name
                for s in recent
                for o in s.observations
            ]
            if len(set(tool_names)) == 1 and tool_names:
                return True
        return False


# ---------------------------------------------------------------------------
# ToolResult
# ---------------------------------------------------------------------------

class ToolResult(BaseModel):
    output: Optional[str] = None
    error: Optional[str] = None
    system: Optional[str] = None
    base64_image: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __str__(self) -> str:
        parts = []
        if self.output:
            parts.append(self.output)
        if self.error:
            parts.append(f"ERROR: {self.error}")
        if self.system:
            parts.append(f"[system: {self.system}]")
        return "\n".join(parts) if parts else "(no output)"


# ---------------------------------------------------------------------------
# Planning primitives
# ---------------------------------------------------------------------------

class StepStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class PlanStep(BaseModel):
    id: int
    description: str
    status: StepStatus = StepStatus.NOT_STARTED
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class Plan(BaseModel):
    id: str
    title: str
    steps: list[PlanStep] = Field(default_factory=list)

    def next_step(self) -> Optional[PlanStep]:
        for step in self.steps:
            if step.status == StepStatus.NOT_STARTED:
                return step
        return None

    def is_complete(self) -> bool:
        return all(s.status == StepStatus.COMPLETED for s in self.steps)

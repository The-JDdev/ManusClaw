from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


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
    def assistant(cls, content: Optional[str] = None, tool_calls: Optional[list[ToolCall]] = None) -> "Message":
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
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


class Memory(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    max_messages: int = 100

    def add(self, message: Message) -> None:
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            keep_system = [m for m in self.messages if m.role == Role.SYSTEM]
            rest = [m for m in self.messages if m.role != Role.SYSTEM]
            trim_to = max(self.max_messages - len(keep_system), 10)
            self.messages = keep_system + rest[-trim_to:]

    def to_list(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self.messages]

    def clear(self) -> None:
        self.messages = []


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


class ToolParam(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[list[str]] = None
    default: Any = None


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

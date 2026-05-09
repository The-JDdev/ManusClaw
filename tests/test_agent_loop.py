"""Tests for the PAORR agent loop in BaseAgent."""
import pytest
from app.config import Config

Config.reset()


@pytest.mark.asyncio
async def test_agent_runs_to_completion():
    """Agent should complete a simple task using MockLLM."""
    from app.agent.manus import Manus
    from app.schema import AgentState
    agent = Manus()
    agent._max_steps = 5
    result = await agent.run("Say hello")
    assert isinstance(result, str)
    assert len(result) > 0
    assert agent.state in (AgentState.FINISHED, AgentState.ERROR)


@pytest.mark.asyncio
async def test_agent_respects_max_steps():
    """Agent should stop at max_steps even if not finished."""
    from app.agent.manus import Manus
    from app.schema import AgentState

    Config.reset()
    agent = Manus()
    agent._max_steps = 2
    result = await agent.run("Do an infinite task")
    assert agent._step_count <= 2


@pytest.mark.asyncio
async def test_agent_state_is_idle_before_run():
    from app.agent.manus import Manus
    from app.schema import AgentState
    agent = Manus()
    assert agent.state == AgentState.IDLE


@pytest.mark.asyncio
async def test_token_budget_grace_call():
    """Token budget should allow one grace call after exhaustion."""
    from app.llm.token_tracker import TokenBudget, TokenUsage
    budget = TokenBudget(max_tokens=100)
    budget._usage._replace_fields = None
    # Simulate exhaustion
    budget._usage.input_tokens = 60
    budget._usage.output_tokens = 50
    assert budget.is_exhausted
    assert not budget.grace_used
    assert budget.use_grace()
    assert budget.grace_used
    assert not budget.use_grace()  # second call returns False


@pytest.mark.asyncio
async def test_duplicate_detection():
    """Agent should detect duplicate responses."""
    from app.agent.base import BaseAgent
    from app.agent.manus import Manus
    from app.schema import Message, Role
    agent = Manus()
    for _ in range(4):
        agent.memory.add(Message(role=Role.ASSISTANT, content="same response"))
    assert agent._is_stuck_by_duplicates()

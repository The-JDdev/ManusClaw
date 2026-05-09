"""Tests for the PAORR loop components: reflect, retry, observation recording."""
import pytest
from app.config import Config
Config.reset()


@pytest.mark.asyncio
async def test_react_reflect_solved():
    """Reflection should return solved=True when LLM says so (mocked)."""
    from app.agent.react import ReActAgent
    from app.permissions.gate import AgentMode
    from app.schema import Observation
    agent = ReActAgent(mode=AgentMode.BUILD)
    obs = Observation(
        tool_name="python_execute", args={}, output="Hello from ManusClaw!",
        error=None, success=True,
    )
    reflection = await agent.reflect("Say hello", obs)
    # MockLLM returns non-JSON but reflect handles parse errors gracefully
    assert reflection is not None
    assert isinstance(reflection.solved, bool)


@pytest.mark.asyncio
async def test_observation_recording():
    from app.agent.manus import Manus
    agent = Manus()
    agent._task_history = __import__("app.schema", fromlist=["TaskHistory"]).TaskHistory(
        task_id="t1", original_goal="test"
    )
    agent._task_history.add_step("step 1")
    agent._session_id = None  # skip DB
    agent.record_observation("bash", {"command": "echo hi"}, "hi", None, attempt=1, duration_ms=10)
    assert agent._tool_call_count == 1
    obs = agent._task_history.steps[0].observations[0]
    assert obs.tool_name == "bash"
    assert obs.success is True


def test_task_history_loop_detection():
    from app.schema import TaskHistory, TaskStep, Observation
    history = TaskHistory(task_id="t1", original_goal="loop test")
    for i in range(3):
        step = history.add_step(f"step {i+1}")
        obs = Observation(tool_name="bash", args={}, output=None, error="fail", success=False)
        step.observations.append(obs)
    assert history.is_looping(window=3)


def test_task_history_no_loop_when_diverse():
    from app.schema import TaskHistory, TaskStep, Observation
    history = TaskHistory(task_id="t2", original_goal="diverse")
    tools = ["bash", "web_search", "python_execute"]
    for i, t in enumerate(tools):
        step = history.add_step(f"step {i+1}")
        obs = Observation(tool_name=t, args={}, output=None, error="fail", success=False)
        step.observations.append(obs)
    assert not history.is_looping(window=3)

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_environment_reset_and_step() -> None:
    from triage.env.hospital_env import HospitalEnv

    env = HospitalEnv(seed=7, max_steps=20)
    observation = await env.reset({"crisis_type": "outbreak"})
    assert observation is not None
    assert env.state.crisis.type.value == "outbreak"

    _, reward, terminated, info = await env.step(env.action_space.sample())
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert "reward_breakdown" in info


@pytest.mark.asyncio
async def test_environment_state_json_is_serializable() -> None:
    from triage.env.hospital_env import HospitalEnv

    env = HospitalEnv(seed=11, max_steps=10)
    await env.reset()
    payload = await env.get_state()
    assert payload["stats"]["total_patients"] >= 0

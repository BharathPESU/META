from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_reward_model_exposes_prompt_and_legacy_keys() -> None:
    from triage.env.hospital_env import HospitalEnv
    from triage.rewards.reward_model import RewardModel

    env = HospitalEnv(seed=3, max_steps=10)
    await env.reset()
    breakdown = RewardModel().compute(env.state, [], [])
    payload = breakdown.to_dict()
    for key in ["survival", "compliance", "coordination", "oversight", "depth", "adaptation", "expert_alignment"]:
        assert key in payload
    for key in ["patient_outcomes", "communication_quality", "drift_adaptation", "token_economy"]:
        assert key in payload


def test_prompt_aligned_reward_components_compute() -> None:
    from triage.env.hospital_env import HospitalEnv
    from triage.reward.components import (
        AdaptationReward,
        ComplianceReward,
        CoordinationReward,
        DepthReward,
        ExpertAlignmentReward,
        OversightReward,
        SurvivalReward,
    )

    env = HospitalEnv(seed=5, max_steps=10)
    import asyncio

    asyncio.run(env.reset())
    state = env.state
    assert isinstance(SurvivalReward().compute(state), float)
    assert isinstance(ComplianceReward().compute(state), float)
    assert isinstance(CoordinationReward().compute(state), float)
    assert isinstance(OversightReward().compute(state), float)
    assert isinstance(DepthReward().compute([]), float)
    assert isinstance(AdaptationReward().compute(state, []), float)
    assert isinstance(ExpertAlignmentReward().compute(state), float)

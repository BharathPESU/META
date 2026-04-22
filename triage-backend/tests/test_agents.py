from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_orchestrator_runs_step_and_exposes_agent_stats() -> None:
    from triage.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator(
        agents_config_path="./config/agents.yaml",
        mock_llm=True,
        seed=42,
        max_steps=15,
        difficulty=0.5,
    )
    await orchestrator.reset({"crisis_type": "mass_casualty", "difficulty": 0.5})
    result = await orchestrator.step()
    assert result.step >= 1
    assert isinstance(orchestrator.get_agent_stats(), list)


def test_strategy_memory_round_trip(tmp_path) -> None:
    from triage.agents.strategy_memory import StrategyMemory

    memory = StrategyMemory(storage_path=str(tmp_path / "memory.json"))
    memory.record(
        agent_type="cmo_oversight",
        crisis_type="outbreak",
        description="Isolate respiratory patients early",
        episode=1,
        reward=1.0,
        success=True,
    )
    memory.save()

    loaded = StrategyMemory(storage_path=str(tmp_path / "memory.json"))
    assert "Isolate respiratory patients early" in loaded.get_strategy_prompt("cmo_oversight", "outbreak")

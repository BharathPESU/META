"""Canonical trajectory collection interfaces built on EpisodeCollector."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from triage.agents.strategy_memory import StrategyMemory
from triage.env.state import CrisisType
from triage.training.episode_collector import EpisodeCollector, EpisodeResult


@dataclass
class TrajectoryStep:
    """Single step in a collected trajectory."""

    step: int
    state_summary: dict[str, Any]
    action: dict[str, Any]
    reward: float
    reward_breakdown: dict[str, Any] = field(default_factory=dict)
    drift_events: list[dict[str, Any]] = field(default_factory=list)
    terminated: bool = False


@dataclass
class Trajectory:
    """Full episode trajectory."""

    episode_id: str
    episode_num: int
    crisis_type: CrisisType
    steps: list[TrajectoryStep]
    total_reward: float
    survival_rate: float
    is_successful: bool
    agent_logs: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    strategy_memory_used: list[dict[str, Any]] = field(default_factory=list)


class TrajectoryCollector:
    """Canonical collector API that reuses the current EpisodeCollector."""

    def __init__(
        self,
        agents_config_path: str = "./config/agents.yaml",
        output_dir: str = "./data/episodes",
        mock_llm: bool = True,
        seed: int = 42,
    ) -> None:
        self.collector = EpisodeCollector(
            agents_config_path=agents_config_path,
            output_dir=output_dir,
            mock_llm=mock_llm,
            seed=seed,
        )
        self.output_dir = Path(output_dir)

    async def collect(
        self,
        env: Any = None,
        agents: Any = None,
        n_episodes: int = 1,
        crisis_types: list[CrisisType] | None = None,
        difficulty: float = 0.5,
    ) -> list[Trajectory]:
        results = await self.collector.collect_batch(
            n_episodes=n_episodes,
            crisis_types=crisis_types,
            difficulty=difficulty,
        )
        return [self._from_episode_result(result) for result in results]

    def save(self, trajectories: list[Trajectory], path: str) -> None:
        serializable = [self._to_dict(trajectory) for trajectory in trajectories]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(serializable, handle, indent=2)

    def load(self, path: str) -> list[Trajectory]:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        trajectories = []
        for item in payload:
            trajectories.append(
                Trajectory(
                    episode_id=item["episode_id"],
                    episode_num=item["episode_num"],
                    crisis_type=CrisisType(item["crisis_type"]),
                    steps=[TrajectoryStep(**step) for step in item["steps"]],
                    total_reward=item["total_reward"],
                    survival_rate=item["survival_rate"],
                    is_successful=item["is_successful"],
                    agent_logs=item.get("agent_logs", {}),
                    strategy_memory_used=item.get("strategy_memory_used", []),
                )
            )
        return trajectories

    def _from_episode_result(self, result: EpisodeResult) -> Trajectory:
        memory = StrategyMemory(storage_path=str(self.output_dir / "strategy_memory.json"))
        return Trajectory(
            episode_id=str(result.episode_id),
            episode_num=result.episode_id,
            crisis_type=CrisisType(result.crisis_type),
            steps=[TrajectoryStep(**step) for step in result.trajectory],
            total_reward=result.total_reward,
            survival_rate=result.survival_rate,
            is_successful=result.survival_rate >= 0.8 and result.total_reward > 0,
            strategy_memory_used=memory.get_all().get(
                f"cmo_oversight:{result.crisis_type}",
                [],
            ),
        )

    def _to_dict(self, trajectory: Trajectory) -> dict[str, Any]:
        return {
            "episode_id": trajectory.episode_id,
            "episode_num": trajectory.episode_num,
            "crisis_type": trajectory.crisis_type.value,
            "steps": [step.__dict__ for step in trajectory.steps],
            "total_reward": trajectory.total_reward,
            "survival_rate": trajectory.survival_rate,
            "is_successful": trajectory.is_successful,
            "agent_logs": trajectory.agent_logs,
            "strategy_memory_used": trajectory.strategy_memory_used,
        }

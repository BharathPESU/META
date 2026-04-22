"""Episode-level reward evaluation helpers."""

from __future__ import annotations

from typing import Any

from triage.env.state import EnvironmentState
from triage.rewards.reward_model import RewardModel


class EpisodeEvaluator:
    """Convenience wrapper for computing final episode reward summaries."""

    def __init__(self, reward_model: RewardModel | None = None) -> None:
        self.reward_model = reward_model or RewardModel()

    def evaluate(self, state: EnvironmentState) -> dict[str, Any]:
        return self.reward_model.compute_episode_reward(state)

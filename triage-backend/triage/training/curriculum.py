"""Adaptive curriculum scheduling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EpisodeConfig:
    """Difficulty config for an episode."""

    phase: int
    difficulty: float
    max_steps: int
    schema_drift: bool
    patient_target: int


class CurriculumScheduler:
    """Escalates or relaxes difficulty based on recent rewards."""

    PHASE_THRESHOLDS = [55.0, 70.0, 82.0, 90.0]

    def get_episode_config(self, episode: int, avg_reward: float) -> EpisodeConfig:
        if episode <= 3 or avg_reward < self.PHASE_THRESHOLDS[0]:
            return EpisodeConfig(phase=1, difficulty=0.35, max_steps=120, schema_drift=False, patient_target=15)
        if episode <= 6 or avg_reward < self.PHASE_THRESHOLDS[1]:
            return EpisodeConfig(phase=2, difficulty=0.5, max_steps=160, schema_drift=True, patient_target=25)
        if episode <= 9 or avg_reward < self.PHASE_THRESHOLDS[2]:
            return EpisodeConfig(phase=3, difficulty=0.7, max_steps=220, schema_drift=True, patient_target=35)
        return EpisodeConfig(phase=4, difficulty=0.9, max_steps=300, schema_drift=True, patient_target=45)

    def should_advance(self, recent_rewards: list[float]) -> bool:
        if len(recent_rewards) < 3:
            return False
        return sum(recent_rewards[-3:]) / 3 >= self.PHASE_THRESHOLDS[min(len(recent_rewards) // 3, 3)]

    def should_fallback(self, recent_rewards: list[float]) -> bool:
        if len(recent_rewards) < 4:
            return False
        baseline = sum(recent_rewards[:-1]) / max(len(recent_rewards) - 1, 1)
        return recent_rewards[-1] < baseline * 0.85

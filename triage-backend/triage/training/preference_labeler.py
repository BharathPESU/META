"""Automatic preference pair labeling for DPO."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from triage.training.trajectory_collector import Trajectory


@dataclass
class PreferencePair:
    """Chosen/rejected pair for DPO."""

    prompt: str
    chosen: str
    rejected: str
    reward_delta: float
    label_source: str


class PreferenceLabeler:
    """Deterministically label better trajectories as chosen examples."""

    def label_trajectories(
        self,
        trajectories: list[Trajectory],
        min_delta: float = 20.0,
    ) -> list[PreferencePair]:
        by_crisis: dict[str, list[Trajectory]] = {}
        for trajectory in trajectories:
            by_crisis.setdefault(trajectory.crisis_type.value, []).append(trajectory)

        pairs: list[PreferencePair] = []
        for crisis_type, group in by_crisis.items():
            sorted_group = sorted(group, key=lambda item: item.total_reward, reverse=True)
            for chosen, rejected in zip(sorted_group, sorted_group[1:]):
                delta = chosen.total_reward - rejected.total_reward
                if delta < min_delta:
                    continue
                pairs.append(
                    PreferencePair(
                        prompt=f"Crisis: {crisis_type}\nEpisode: {chosen.episode_num}",
                        chosen=json.dumps([step.action for step in chosen.steps[:10]]),
                        rejected=json.dumps([step.action for step in rejected.steps[:10]]),
                        reward_delta=round(delta, 4),
                        label_source=self._label_source(chosen, rejected),
                    )
                )
        return pairs

    def export_as_hf_dataset(
        self,
        pairs: list[PreferencePair],
        output_path: str,
    ) -> dict[str, list[dict[str, str]]]:
        dataset = {
            "train": [
                {
                    "prompt": pair.prompt,
                    "chosen": pair.chosen,
                    "rejected": pair.rejected,
                    "label_source": pair.label_source,
                }
                for pair in pairs
            ],
            "test": [],
        }
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(dataset, handle, indent=2)
        return dataset

    def _label_source(self, chosen: Trajectory, rejected: Trajectory) -> str:
        if chosen.survival_rate > rejected.survival_rate:
            return "survival"
        if chosen.total_reward > rejected.total_reward:
            return "reward_threshold"
        return "oversight"

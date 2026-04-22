"""Adapters for real or curated TRIAGE preference data."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class NormalizedTrainingRecord:
    """Portable training row shared by CSV, JSON, and JSONL imports."""

    scenario_context: dict[str, Any]
    patient_state: dict[str, Any]
    agent_role: str
    action_trace: list[dict[str, Any]]
    outcome: dict[str, Any]
    policy_flags: dict[str, Any] = field(default_factory=dict)
    preference_source: str = "real_dataset"

    @property
    def reward(self) -> float:
        value = self.outcome.get("reward", self.outcome.get("total_reward", 0.0))
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


class DatasetAdapter:
    """Load real or curated records and export DPO-compatible pairs."""

    REQUIRED_FIELDS = {
        "scenario_context",
        "patient_state",
        "agent_role",
        "action_trace",
        "outcome",
    }

    def load(self, path: str | Path) -> list[NormalizedTrainingRecord]:
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(f"Dataset not found: {source}")
        if source.suffix == ".jsonl":
            rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
        elif source.suffix == ".json":
            payload = json.loads(source.read_text(encoding="utf-8"))
            rows = payload if isinstance(payload, list) else payload.get("records", [])
        elif source.suffix == ".csv":
            with open(source, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        else:
            raise ValueError(f"Unsupported dataset extension: {source.suffix}")
        return [self._normalize(row) for row in rows]

    def records_to_pairs(
        self,
        records: list[NormalizedTrainingRecord],
        min_delta: float = 0.1,
    ) -> list[dict[str, str]]:
        grouped: dict[tuple[str, str], list[NormalizedTrainingRecord]] = {}
        for record in records:
            key = (json.dumps(record.scenario_context, sort_keys=True), record.agent_role)
            grouped.setdefault(key, []).append(record)

        pairs: list[dict[str, str]] = []
        for (scenario_key, role), group in grouped.items():
            ranked = sorted(group, key=lambda item: item.reward, reverse=True)
            for chosen, rejected in zip(ranked, ranked[1:]):
                delta = chosen.reward - rejected.reward
                if delta < min_delta:
                    continue
                pairs.append(
                    {
                        "prompt": self._prompt(json.loads(scenario_key), role),
                        "chosen": json.dumps(chosen.action_trace),
                        "rejected": json.dumps(rejected.action_trace),
                        "label_source": chosen.preference_source,
                        "reward_delta": round(delta, 4),
                    }
                )
        return pairs

    def mix_pairs(
        self,
        real_pairs: list[dict[str, Any]],
        synthetic_pairs: list[dict[str, Any]],
        real_fraction: float = 0.3,
    ) -> list[dict[str, Any]]:
        if not real_pairs:
            return list(synthetic_pairs)
        if not synthetic_pairs:
            return list(real_pairs)
        real_fraction = max(0.0, min(1.0, real_fraction))
        synthetic_count = len(synthetic_pairs)
        real_count = min(len(real_pairs), max(1, int((synthetic_count * real_fraction) / max(1 - real_fraction, 0.01))))
        return real_pairs[:real_count] + synthetic_pairs

    def export_preference_dataset(
        self,
        pairs: list[dict[str, Any]],
        output_path: str | Path,
    ) -> dict[str, list[dict[str, Any]]]:
        dataset = {"train": pairs, "test": []}
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
        return dataset

    def _normalize(self, row: dict[str, Any]) -> NormalizedTrainingRecord:
        missing = self.REQUIRED_FIELDS - set(row)
        if missing:
            raise ValueError(f"Dataset row missing fields: {sorted(missing)}")
        return NormalizedTrainingRecord(
            scenario_context=self._coerce_json(row["scenario_context"]),
            patient_state=self._coerce_json(row["patient_state"]),
            agent_role=str(row["agent_role"]),
            action_trace=self._coerce_json(row["action_trace"]),
            outcome=self._coerce_json(row["outcome"]),
            policy_flags=self._coerce_json(row.get("policy_flags", {})),
            preference_source=str(row.get("preference_source", "real_dataset")),
        )

    def _coerce_json(self, value: Any) -> Any:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("{") or text.startswith("["):
                return json.loads(text)
        return value

    def _prompt(self, scenario_context: dict[str, Any], agent_role: str) -> str:
        crisis = scenario_context.get("crisis_type", "unknown")
        constraints = scenario_context.get("constraints", [])
        return f"Crisis: {crisis}\nAgent role: {agent_role}\nConstraints: {json.dumps(constraints)}"

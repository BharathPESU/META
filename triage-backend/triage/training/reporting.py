"""Generate judge-facing training reports from TRIAGE artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


def generate_training_report(
    artifacts_dir: str | Path,
    output_dir: str | Path,
    training_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifacts = Path(artifacts_dir)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    rewards = _load_episode_rewards(artifacts)
    penalties = _load_penalties(artifacts)
    metrics = training_metrics or _load_json(artifacts / "model" / "training_metrics.json") or {}
    baseline, trained = _split_rewards(rewards)

    summary = {
        "artifacts_dir": str(artifacts),
        "baseline_rewards": baseline,
        "trained_rewards": trained,
        "baseline_mean_reward": round(mean(baseline), 4) if baseline else 0.0,
        "trained_mean_reward": round(mean(trained), 4) if trained else 0.0,
        "reward_delta": round((mean(trained) if trained else 0.0) - (mean(baseline) if baseline else 0.0), 4),
        "penalties": penalties,
        "training": metrics,
        "outputs": {
            "summary_json": str(target / "training_report.json"),
            "summary_md": str(target / "training_report.md"),
            "reward_chart": str(target / "before_after_rewards.svg"),
            "loss_chart": str(target / "training_loss.svg"),
            "penalty_chart": str(target / "workflow_penalties.svg"),
        },
    }

    (target / "training_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (target / "training_report.md").write_text(_markdown(summary), encoding="utf-8")
    (target / "before_after_rewards.svg").write_text(_bar_svg(baseline, trained), encoding="utf-8")
    (target / "training_loss.svg").write_text(_line_svg(metrics.get("train_loss_curve", [])), encoding="utf-8")
    (target / "workflow_penalties.svg").write_text(_penalty_svg(penalties), encoding="utf-8")
    return summary


def _load_episode_rewards(path: Path) -> list[float]:
    rewards: list[float] = []
    for summary_path in sorted(path.glob("episode_*_summary.json")):
        payload = _load_json(summary_path) or {}
        if "total_reward" in payload:
            rewards.append(float(payload["total_reward"]))
    return rewards


def _load_penalties(path: Path) -> dict[str, int]:
    totals = {
        "hallucinated_api_calls": 0,
        "chain_of_command_bypasses": 0,
        "missing_prechecks": 0,
        "override_required_blocks": 0,
        "failed_actions": 0,
    }
    for episode_path in sorted(path.glob("episode_*.jsonl")):
        for line in episode_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            step = json.loads(line)
            workflow = step.get("reward_breakdown", {}).get("details", {}).get("workflow", {})
            penalties = workflow.get("penalties", {})
            for key in totals:
                totals[key] += int(penalties.get(key, 0))
    return totals


def _split_rewards(rewards: list[float]) -> tuple[list[float], list[float]]:
    if len(rewards) < 2:
        return rewards, []
    mid = max(1, len(rewards) // 2)
    return rewards[:mid], rewards[mid:]


def _markdown(summary: dict[str, Any]) -> str:
    training = summary.get("training", {})
    return "\n".join(
        [
            "# TRIAGE Training Report",
            "",
            f"- Baseline mean reward: {summary['baseline_mean_reward']}",
            f"- Trained mean reward: {summary['trained_mean_reward']}",
            f"- Reward delta: {summary['reward_delta']}",
            f"- Training status: {training.get('status', 'unknown')}",
            f"- Preset: {training.get('preset', 'unknown')}",
            f"- Dataset size: {training.get('dataset_size', 0)}",
            "",
            "## Workflow Penalties",
            "",
            *[f"- {key}: {value}" for key, value in summary["penalties"].items()],
            "",
            "## Artifacts",
            "",
            *[f"- {key}: {value}" for key, value in summary["outputs"].items()],
            "",
        ]
    )


def _bar_svg(baseline: list[float], trained: list[float]) -> str:
    base = mean(baseline) if baseline else 0.0
    train = mean(trained) if trained else 0.0
    max_value = max(base, train, 1.0)
    base_h = int((base / max_value) * 180)
    train_h = int((train / max_value) * 180)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="520" height="280" viewBox="0 0 520 280">
<rect width="520" height="280" fill="#0f172a"/>
<text x="24" y="32" fill="#e2e8f0" font-family="monospace" font-size="16">Before vs After Reward</text>
<rect x="120" y="{230 - base_h}" width="90" height="{base_h}" fill="#64748b"/>
<rect x="300" y="{230 - train_h}" width="90" height="{train_h}" fill="#38bdf8"/>
<text x="118" y="252" fill="#e2e8f0" font-family="monospace" font-size="12">Baseline {base:.2f}</text>
<text x="298" y="252" fill="#e2e8f0" font-family="monospace" font-size="12">Trained {train:.2f}</text>
</svg>"""


def _line_svg(values: list[float]) -> str:
    if not values:
        values = [0.0]
    max_value = max(values) or 1.0
    points = []
    width = 460
    for index, value in enumerate(values):
        x = 30 + int((index / max(1, len(values) - 1)) * width)
        y = 230 - int((value / max_value) * 180)
        points.append(f"{x},{y}")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="520" height="280" viewBox="0 0 520 280">
<rect width="520" height="280" fill="#0f172a"/>
<text x="24" y="32" fill="#e2e8f0" font-family="monospace" font-size="16">Training Loss</text>
<polyline fill="none" stroke="#22c55e" stroke-width="3" points="{' '.join(points)}"/>
</svg>"""


def _penalty_svg(values: dict[str, int]) -> str:
    rows = list(values.items())
    max_value = max(values.values(), default=1) or 1
    bars = []
    for index, (key, value) in enumerate(rows):
        y = 60 + index * 34
        width = int((value / max_value) * 300)
        bars.append(f'<text x="24" y="{y + 13}" fill="#e2e8f0" font-family="monospace" font-size="11">{key}</text>')
        bars.append(f'<rect x="230" y="{y}" width="{width}" height="18" fill="#f97316"/>')
        bars.append(f'<text x="{238 + width}" y="{y + 13}" fill="#e2e8f0" font-family="monospace" font-size="11">{value}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="620" height="280" viewBox="0 0 620 280">
<rect width="620" height="280" fill="#0f172a"/>
<text x="24" y="32" fill="#e2e8f0" font-family="monospace" font-size="16">Workflow Penalties</text>
{''.join(bars)}
</svg>"""


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

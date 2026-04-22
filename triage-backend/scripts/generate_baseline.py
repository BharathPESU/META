#!/usr/bin/env python3
"""Generate baseline episode summaries for demo comparison."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage.training.trajectory_collector import TrajectoryCollector


async def _run(args: argparse.Namespace) -> None:
    collector = TrajectoryCollector(output_dir=args.output, mock_llm=True, seed=args.seed)
    trajectories = await collector.collect(n_episodes=args.episodes, difficulty=args.difficulty)
    baseline = [
        {
            "episode_id": trajectory.episode_id,
            "reward": trajectory.total_reward,
            "survival_rate": trajectory.survival_rate,
        }
        for trajectory in trajectories
    ]
    output_path = Path(args.output) / "baseline_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(baseline, handle, indent=2)
    print(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate baseline TRIAGE runs")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--difficulty", type=float, default=0.5)
    parser.add_argument("--output", type=str, default="./data/demo")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()

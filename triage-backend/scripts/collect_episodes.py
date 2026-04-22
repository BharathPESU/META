#!/usr/bin/env python3
"""
collect_episodes.py — Batch episode collection for DPO training.

Usage:
    python scripts/collect_episodes.py --episodes 20 --difficulty 0.6
    python scripts/collect_episodes.py --episodes 50 --output ./data/training
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage.env.state import CrisisType
from triage.training.episode_collector import EpisodeCollector


async def collect(args: argparse.Namespace) -> None:
    """Collect batch of episodes."""
    collector = EpisodeCollector(
        output_dir=args.output,
        mock_llm=args.mock,
        seed=args.seed,
    )

    crisis_types = None
    if args.crisis:
        crisis_types = [CrisisType(ct) for ct in args.crisis]

    print(f"\n{'='*60}")
    print(f"  TRIAGE — Episode Collection")
    print(f"{'='*60}")
    print(f"  Episodes:   {args.episodes}")
    print(f"  Difficulty: {args.difficulty}")
    print(f"  Output:     {args.output}")
    print(f"  LLM Mode:   {'Mock' if args.mock else 'Live'}")
    print(f"{'='*60}\n")

    results = await collector.collect_batch(
        n_episodes=args.episodes,
        crisis_types=crisis_types,
        difficulty=args.difficulty,
    )

    summary = collector.get_summary()

    print(f"\n{'='*60}")
    print(f"  COLLECTION COMPLETE")
    print(f"{'='*60}")
    for k, v in summary.items():
        print(f"  {k:>20s}: {v}")
    print(f"{'='*60}\n")

    # Save summary
    summary_path = Path(args.output) / "collection_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect TRIAGE episodes")
    parser.add_argument("--episodes", "-n", type=int, default=10, help="Number of episodes")
    parser.add_argument("--difficulty", type=float, default=0.5, help="Difficulty 0.0-1.0")
    parser.add_argument("--crisis", nargs="+", default=None,
                        choices=["mass_casualty", "outbreak", "equipment_failure", "staff_shortage"])
    parser.add_argument("--output", "-o", type=str, default="./data/episodes")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mock", action="store_true", default=True)
    parser.add_argument("--live", action="store_true")

    args = parser.parse_args()
    if args.live:
        args.mock = False

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
    asyncio.run(collect(args))


if __name__ == "__main__":
    main()

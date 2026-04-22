#!/usr/bin/env python3
"""
demo.py — Full demo: collect → train → serve with metrics output.

Usage:
    python scripts/demo.py
    python scripts/demo.py --episodes 5 --quick
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage.training.episode_collector import EpisodeCollector
from triage.training.dpo_trainer import DPOTrainingPipeline, DPOConfig
from triage.env.state import CrisisType


async def run_demo(args: argparse.Namespace) -> None:
    """Run end-to-end demo pipeline."""
    output_dir = "./data/demo"

    print("\n" + "=" * 70)
    print("  🏥  TRIAGE — Multi-Agent Hospital Crisis Simulation Demo")
    print("=" * 70)

    # ── Phase 1: Collect episodes ─────────────────────────────────────────
    print("\n📋 Phase 1: Collecting episodes...\n")
    collector = EpisodeCollector(
        output_dir=output_dir,
        mock_llm=True,
        seed=42,
    )

    results = await collector.collect_batch(
        n_episodes=args.episodes,
        difficulty=0.6,
    )

    summary = collector.get_summary()
    print(f"\n  ✅ {summary['episodes']} episodes collected")
    print(f"     Mean reward:   {summary['mean_reward']:.4f}")
    print(f"     Mean survival: {summary['mean_survival']:.1%}")
    print(f"     Best reward:   {summary['best_reward']:.4f}")

    # ── Phase 2: DPO Training ─────────────────────────────────────────────
    print("\n\n🧠 Phase 2: DPO Training (mock mode)...\n")
    dpo_config = DPOConfig(
        data_dir=output_dir,
        output_dir="./models/demo_output",
        mock_mode=True,
        num_epochs=3,
    )
    pipeline = DPOTrainingPipeline(dpo_config)
    train_metrics = await pipeline.train()

    print(f"  ✅ Training complete")
    print(f"     Final loss: {train_metrics.get('train_loss_final', 'N/A')}")
    print(f"     Steps:      {train_metrics.get('train_steps', 'N/A')}")

    # ── Phase 3: Summary Report ───────────────────────────────────────────
    print("\n\n📊 Phase 3: Results Summary\n")
    print("  ┌───────────────────────────────────────────────────┐")
    print("  │              HACK DEMO RESULTS                    │")
    print("  ├───────────────────────────────────────────────────┤")

    for r in results:
        status = "✅" if r.survival_rate > 0.7 else "⚠️" if r.survival_rate > 0.4 else "❌"
        print(
            f"  │ {status} Episode {r.episode_id:3d} | "
            f"{r.crisis_type:20s} | "
            f"Survival: {r.survival_rate:5.1%} | "
            f"Reward: {r.total_reward:+7.3f} │"
        )

    print("  ├───────────────────────────────────────────────────┤")
    print(f"  │ 📈 Mean Reward:       {summary['mean_reward']:>28.4f} │")
    print(f"  │ 🏥 Mean Survival:     {summary['mean_survival']:>27.1%} │")
    print(f"  │ 🧬 DPO Loss (final):  {train_metrics.get('train_loss_final', 0):>27.4f} │")
    print("  └───────────────────────────────────────────────────┘")

    # ── Save Full Report ──────────────────────────────────────────────────
    report = {
        "collection": summary,
        "training": train_metrics,
        "episodes": [r.to_dict() for r in results],
    }
    report_path = Path(output_dir) / "demo_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  📁 Full report saved to: {report_path}")
    print(f"\n  🚀 Start API server: python -m triage.api.main")
    print(f"     Then open: http://localhost:8000/docs")
    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="TRIAGE end-to-end demo")
    parser.add_argument("--episodes", "-n", type=int, default=8)
    parser.add_argument("--quick", action="store_true", help="Run minimal demo (4 episodes)")

    args = parser.parse_args()
    if args.quick:
        args.episodes = 4

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
    asyncio.run(run_demo(args))


if __name__ == "__main__":
    main()

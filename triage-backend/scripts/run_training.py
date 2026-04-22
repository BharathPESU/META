#!/usr/bin/env python3
"""Trigger the mock-first training pipeline."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage.training.dpo_trainer import DPOConfig, TRIAGEDPOTrainer
from triage.training.dataset_adapter import DatasetAdapter
from triage.training.preference_labeler import PreferenceLabeler
from triage.training.trajectory_collector import TrajectoryCollector


async def _run(args: argparse.Namespace) -> None:
    collector = TrajectoryCollector(output_dir=args.output, mock_llm=True, seed=args.seed)
    trajectories = await collector.collect(n_episodes=args.episodes, difficulty=args.difficulty)
    labeler = PreferenceLabeler()
    pairs = labeler.label_trajectories(trajectories)
    dataset = labeler.export_as_hf_dataset(pairs, str(Path(args.output) / "preference_dataset.json"))
    if args.external_dataset:
        adapter = DatasetAdapter()
        real_pairs = adapter.records_to_pairs(adapter.load(args.external_dataset))
        mixed_pairs = adapter.mix_pairs(real_pairs, dataset["train"], args.real_data_fraction)
        adapter.export_preference_dataset(mixed_pairs, str(Path(args.output) / "preference_dataset.json"))

    trainer = TRIAGEDPOTrainer(
        DPOConfig(
            preset=args.preset,
            output_dir=str(Path(args.output) / "model"),
            data_dir=args.output,
            mock_mode=args.mock,
            num_epochs=args.epochs,
        )
    )
    metrics = await trainer.train()
    print(metrics)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the TRIAGE training flow")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--difficulty", type=float, default=0.5)
    parser.add_argument("--output", type=str, default="./data/episodes")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mock", action="store_true", default=True)
    parser.add_argument("--preset", choices=["4b_reliable", "8b_showcase"], default="4b_reliable")
    parser.add_argument("--external-dataset", type=str, default=None)
    parser.add_argument("--real-data-fraction", type=float, default=0.3)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()

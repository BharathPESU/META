#!/usr/bin/env python3
"""
train_dpo.py — Run DPO fine-tuning from collected episodes.

Usage:
    python scripts/train_dpo.py --mock
    python scripts/train_dpo.py --model unsloth/gemma-3-4b-it-unsloth-bnb-4bit --epochs 3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage.training.dpo_trainer import DPOTrainingPipeline, DPOConfig


async def train(args: argparse.Namespace) -> None:
    """Run DPO training."""
    preset = "custom" if args.model != parser_default_model() and args.preset == "4b_reliable" else args.preset
    config = DPOConfig(
        preset=preset,
        model_name=args.model,
        output_dir=args.output,
        data_dir=args.data_dir,
        learning_rate=args.lr,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        mock_mode=args.mock,
    )

    print(f"\n{'='*60}")
    print(f"  TRIAGE — DPO Training Pipeline")
    print(f"{'='*60}")
    print(f"  Model:      {config.model_name}")
    print(f"  Preset:     {config.preset}")
    print(f"  Data:       {config.data_dir}")
    print(f"  Output:     {config.output_dir}")
    print(f"  Epochs:     {config.num_epochs}")
    print(f"  LR:         {config.learning_rate}")
    print(f"  Mode:       {'Mock' if config.mock_mode else 'GPU Training'}")
    print(f"{'='*60}\n")

    pipeline = DPOTrainingPipeline(config)
    metrics = await pipeline.train()

    print(f"\n{'='*60}")
    print(f"  TRAINING COMPLETE")
    print(f"{'='*60}")
    for k, v in metrics.items():
        if k == "train_loss_curve":
            print(f"  {'loss_curve':>20s}: [{v[0]:.4f}, ..., {v[-1]:.4f}] ({len(v)} steps)")
        else:
            print(f"  {k:>20s}: {v}")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DPO training")
    parser.add_argument("--model", type=str, default="unsloth/gemma-3-4b-it-unsloth-bnb-4bit")
    parser.add_argument("--preset", type=str, default="4b_reliable", choices=["4b_reliable", "8b_showcase"])
    parser.add_argument("--data-dir", type=str, default="./data/episodes")
    parser.add_argument("--output", "-o", type=str, default="./models/dpo_output")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=5e-7)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--mock", action="store_true", default=True)
    parser.add_argument("--gpu", action="store_true")

    args = parser.parse_args()
    if args.gpu:
        args.mock = False

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
    asyncio.run(train(args))


def parser_default_model() -> str:
    return "unsloth/gemma-3-4b-it-unsloth-bnb-4bit"


if __name__ == "__main__":
    main()

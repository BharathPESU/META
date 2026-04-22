#!/usr/bin/env python3
"""Run a single episode via the shared orchestrator/service layer."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage.agents.orchestrator import AgentOrchestrator


async def _run(args: argparse.Namespace) -> None:
    orchestrator = AgentOrchestrator(
        agents_config_path=str(Path(__file__).resolve().parent.parent / "config" / "agents.yaml"),
        mock_llm=args.mock,
        seed=args.seed,
        max_steps=args.steps,
        difficulty=args.difficulty,
    )
    scenario = {"difficulty": args.difficulty}
    if args.crisis:
        scenario["crisis_type"] = args.crisis
    await orchestrator.reset(scenario)
    await orchestrator.run(delay_ms=args.delay_ms, max_steps=args.steps)
    snapshot = orchestrator.build_state_snapshot()
    print(snapshot["metrics"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a TRIAGE episode")
    parser.add_argument("--crisis", type=str, default=None)
    parser.add_argument("--difficulty", type=float, default=0.5)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mock", action="store_true", default=True)
    parser.add_argument("--delay-ms", type=int, default=0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()

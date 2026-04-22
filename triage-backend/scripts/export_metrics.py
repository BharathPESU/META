#!/usr/bin/env python3
"""Export reward and baseline metrics for demos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage.api.service import backend_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Export TRIAGE metrics")
    parser.add_argument("--output", type=str, default="./data/demo/exported_metrics.json")
    args = parser.parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "reward_curve": backend_service.get_reward_curve(),
        "comparison": backend_service.get_comparison_metrics(),
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(output_path)


if __name__ == "__main__":
    main()

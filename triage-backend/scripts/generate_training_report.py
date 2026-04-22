#!/usr/bin/env python3
"""Generate TRIAGE judge-facing training report artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage.training.reporting import generate_training_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TRIAGE training report artifacts")
    parser.add_argument("--artifacts-dir", default="./data/episodes")
    parser.add_argument("--output-dir", default="./data/episodes/report")
    parser.add_argument("--metrics", default=None, help="Optional training_metrics.json path")
    args = parser.parse_args()

    metrics = None
    if args.metrics:
        metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    report = generate_training_report(args.artifacts_dir, args.output_dir, metrics)
    print(json.dumps(report["outputs"], indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
fetch_hf_dataset.py — Download real medical datasets from Hugging Face
and convert them to DPO pairs format compatible with TRIAGE training.

Sources used:
1. MedMCQA  — 194k real Indian medical exam questions (AIIMS/PGI)
              Each question has 4 options + correct answer + explanation
              → chosen = correct answer with explanation
              → rejected = most plausible wrong answer

2. MedQA    — US Medical Licensing Exam (USMLE) questions
              5-option MCQ with correct answer and step reasoning
              → Same chosen/rejected construction

The final output is merged with the existing synthetic data in
data/full_training/dpo_pairs.jsonl.

Usage:
    python scripts/fetch_hf_dataset.py --dataset medmcqa --samples 2000
    python scripts/fetch_hf_dataset.py --dataset medqa   --samples 1000
    python scripts/fetch_hf_dataset.py --dataset both    --samples 1500
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

# ─── Hospital workflow context prompt ─────────────────────────
# Wraps real medical MCQs into our multi-agent hospital workflow framing.
# This way the real data also teaches the agent about the hospital context.

HOSPITAL_CONTEXT_TEMPLATES = [
    "You are the ER_TRIAGE agent. A patient has been admitted. "
    "Assess the following clinical scenario and determine the correct action:\n\n{question}",

    "Hospital Crisis Management System — Step {step}. "
    "ICU capacity at 78%. {crisis_type} in progress. "
    "The PHARMACY agent is requesting clinical guidance:\n\n{question}",

    "CMO escalation received. Specialist consultation required. "
    "The attending physician presents the following case for triage priority:\n\n{question}",

    "Multi-agent TRIAGE system. The ICU_MANAGEMENT agent has flagged an uncertain case. "
    "Clinical decision support required:\n\n{question}",

    "Emergency department intake. Staff shortage crisis. "
    "Rapid clinical assessment needed for:\n\n{question}",
]

CRISIS_TYPES = ["mass_casualty", "outbreak", "equipment_failure", "staff_shortage"]


# ─── MedMCQA Converter ────────────────────────────────────────

def convert_medmcqa(sample: dict[str, Any], idx: int) -> dict[str, Any] | None:
    """
    Convert a MedMCQA sample to a DPO pair.

    MedMCQA fields:
        question: str
        opa, opb, opc, opd: str (four options)
        cop: int (0–3 = correct option index)
        exp: str (explanation, may be empty)
        subject_name: str
        topic_name: str

    Returns:
        DPO dict with prompt/chosen/rejected/metadata, or None if invalid.
    """
    q = sample.get("question", "").strip()
    options = [
        sample.get("opa", ""),
        sample.get("opb", ""),
        sample.get("opc", ""),
        sample.get("opd", ""),
    ]
    correct_idx = sample.get("cop", -1)
    explanation = (sample.get("exp") or "").strip()

    # Skip if missing key fields
    if not q or correct_idx not in (0, 1, 2, 3):
        return None
    if not all(options):
        return None

    correct_answer = options[correct_idx]

    # Pick a "plausible wrong" option — prefer the adjacent option (most confusing)
    wrong_candidates = [opt for i, opt in enumerate(options) if i != correct_idx and opt]
    if not wrong_candidates:
        return None
    wrong_answer = random.choice(wrong_candidates)

    # Build contextual prompt
    tmpl = random.choice(HOSPITAL_CONTEXT_TEMPLATES)
    question_block = (
        f"{q}\n\n"
        f"Options:\n"
        f"  A. {options[0]}\n"
        f"  B. {options[1]}\n"
        f"  C. {options[2]}\n"
        f"  D. {options[3]}"
    )
    prompt = tmpl.format(
        question=question_block,
        step=random.randint(5, 150),
        crisis_type=random.choice(CRISIS_TYPES),
    )

    # Build chosen (correct answer + clinical reasoning)
    if explanation:
        chosen = (
            f"Clinical Answer: {correct_answer}\n"
            f"Reasoning: {explanation[:400]}"  # cap at 400 chars
        )
    else:
        chosen = (
            f"Clinical Answer: {correct_answer}\n"
            f"Reasoning: Based on standard clinical protocols and evidence-based medicine, "
            f"{correct_answer.lower()} is the correct management for this presentation."
        )

    # Build rejected (wrong answer, no good reasoning)
    rejected = (
        f"Clinical Answer: {wrong_answer}\n"
        f"Reasoning: This seems appropriate given the clinical presentation, "
        f"proceeding without full workup to save time."
    )

    return {
        "prompt": prompt,
        "chosen": chosen,
        "rejected": rejected,
        "metadata": {
            "source": "medmcqa",
            "subject": sample.get("subject_name", ""),
            "topic": sample.get("topic_name", ""),
            "sample_idx": idx,
            "has_explanation": bool(explanation),
            "generator": "huggingface_medmcqa",
        },
    }


# ─── MedQA (USMLE) Converter ──────────────────────────────────

def convert_medqa(sample: dict[str, Any], idx: int) -> dict[str, Any] | None:
    """
    Convert a MedQA (USMLE) sample to a DPO pair.

    MedQA fields vary by split — we handle the most common:
        question: str
        options: dict[str, str]  e.g. {"A": "...", "B": "...", ...}
        answer_idx: str  e.g. "A"
        answer: str
    """
    q = (sample.get("question") or "").strip()
    options_raw = sample.get("options") or {}
    answer_key = sample.get("answer_idx") or sample.get("answer_key") or ""
    answer_text = sample.get("answer") or ""

    if not q:
        return None

    # Normalize options dict
    if isinstance(options_raw, dict):
        options = options_raw
    elif isinstance(options_raw, list):
        options = {chr(65 + i): opt for i, opt in enumerate(options_raw)}
    else:
        return None

    if not options:
        return None

    # Find correct answer
    correct_text = ""
    if answer_key and answer_key in options:
        correct_text = options[answer_key]
    elif answer_text:
        correct_text = answer_text
    else:
        return None

    # Wrong option
    wrong_candidates = [v for k, v in options.items() if v != correct_text and v]
    if not wrong_candidates:
        return None
    wrong_text = random.choice(wrong_candidates)

    # Build options block
    opts_block = "\n".join(f"  {k}. {v}" for k, v in options.items())
    tmpl = random.choice(HOSPITAL_CONTEXT_TEMPLATES)
    prompt = tmpl.format(
        question=f"{q}\n\nOptions:\n{opts_block}",
        step=random.randint(5, 150),
        crisis_type=random.choice(CRISIS_TYPES),
    )

    chosen = (
        f"Clinical Answer: {correct_text}\n"
        f"Reasoning: Based on USMLE Step clinical guidelines and current standard of care, "
        f"this is the correct management approach."
    )
    rejected = (
        f"Clinical Answer: {wrong_text}\n"
        f"Reasoning: This option was selected based on initial assessment without "
        f"complete evaluation of the clinical picture."
    )

    return {
        "prompt": prompt,
        "chosen": chosen,
        "rejected": rejected,
        "metadata": {
            "source": "medqa_usmle",
            "sample_idx": idx,
            "generator": "huggingface_medqa",
        },
    }


# ─── Dataset Fetcher ───────────────────────────────────────────

def fetch_medmcqa(n_samples: int) -> list[dict[str, Any]]:
    """Download and convert MedMCQA from Hugging Face."""
    print("  Downloading MedMCQA (194k medical exam questions)...")

    from datasets import load_dataset  # type: ignore[import-untyped]

    ds = load_dataset(
        "openlifescienceai/medmcqa",
        split="train",
        trust_remote_code=True,
    )

    print(f"  MedMCQA loaded: {len(ds):,} samples available")

    # Shuffle and take a sample
    indices = random.sample(range(len(ds)), min(n_samples * 2, len(ds)))
    pairs: list[dict[str, Any]] = []

    for i, idx in enumerate(indices):
        sample = ds[idx]
        pair = convert_medmcqa(dict(sample), idx=idx)
        if pair:
            pairs.append(pair)
        if len(pairs) >= n_samples:
            break

    return pairs


def fetch_medqa(n_samples: int) -> list[dict[str, Any]]:
    """Download and convert MedQA (USMLE) from Hugging Face."""
    print("  Downloading MedQA-USMLE dataset...")

    from datasets import load_dataset  # type: ignore[import-untyped]

    ds = load_dataset(
        "GBaker/MedQA-USMLE-4-options",
        split="train",
        trust_remote_code=True,
    )

    print(f"  MedQA loaded: {len(ds):,} samples available")

    indices = random.sample(range(len(ds)), min(n_samples * 2, len(ds)))
    pairs: list[dict[str, Any]] = []

    for i, idx in enumerate(indices):
        sample = ds[idx]
        pair = convert_medqa(dict(sample), idx=idx)
        if pair:
            pairs.append(pair)
        if len(pairs) >= n_samples:
            break

    return pairs


# ─── Merge & Write ─────────────────────────────────────────────

def merge_and_write(
    new_pairs: list[dict[str, Any]],
    output_path: Path,
    shuffle_merged: bool = True,
) -> int:
    """
    Merge new HuggingFace pairs with existing synthetic pairs.

    Returns total pair count after merge.
    """
    existing: list[dict[str, Any]] = []
    if output_path.exists():
        with output_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        existing.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        print(f"  Loaded {len(existing):,} existing synthetic pairs")

    merged = existing + new_pairs

    if shuffle_merged:
        random.shuffle(merged)
        print(f"  Shuffled {len(merged):,} total pairs (prevents ordering bias)")

    with output_path.open("w", encoding="utf-8") as f:
        for pair in merged:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    return len(merged)


# ─── Main ──────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch real medical datasets from Hugging Face for DPO training"
    )
    parser.add_argument(
        "--dataset",
        choices=["medmcqa", "medqa", "both"],
        default="medmcqa",
        help="Which dataset to download (default: medmcqa)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=2000,
        help="Number of samples to pull per dataset (default: 2000)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/full_training",
        help="Output directory (default: ./data/full_training)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=99,
        help="Random seed (default: 99)",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Write to a separate file instead of merging with existing",
    )

    args = parser.parse_args()
    random.seed(args.seed)

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.no_merge:
        output_path = output_dir / "hf_dpo_pairs.jsonl"
    else:
        output_path = output_dir / "dpo_pairs.jsonl"

    print(f"\n{'='*60}")
    print("  TRIAGE — HuggingFace Dataset Fetcher")
    print(f"{'='*60}")
    print(f"  Dataset     : {args.dataset}")
    print(f"  Samples     : {args.samples}")
    print(f"  Output      : {output_path}")
    print(f"{'='*60}\n")

    start = time.perf_counter()
    all_new_pairs: list[dict[str, Any]] = []

    # ── Download ───────────────────────────────────────────────
    if args.dataset in ("medmcqa", "both"):
        n = args.samples if args.dataset == "medmcqa" else args.samples // 2
        medmcqa_pairs = fetch_medmcqa(n)
        print(f"  ✓ MedMCQA converted: {len(medmcqa_pairs):,} pairs")
        all_new_pairs.extend(medmcqa_pairs)

    if args.dataset in ("medqa", "both"):
        n = args.samples if args.dataset == "medqa" else args.samples // 2
        medqa_pairs = fetch_medqa(n)
        print(f"  ✓ MedQA converted: {len(medqa_pairs):,} pairs")
        all_new_pairs.extend(medqa_pairs)

    if not all_new_pairs:
        print("\n[ERROR] No pairs generated. Check dataset names and try again.")
        sys.exit(1)

    # ── Merge ──────────────────────────────────────────────────
    total = merge_and_write(all_new_pairs, output_path)

    elapsed = time.perf_counter() - start
    size_kb = output_path.stat().st_size / 1024

    print(f"\n{'='*60}")
    print("  COMPLETE")
    print(f"{'='*60}")
    print(f"  New HF pairs added   : {len(all_new_pairs):,}")
    print(f"  Total pairs in file  : {total:,}")
    print(f"  File size            : {size_kb:.1f} KB ({size_kb/1024:.2f} MB)")
    print(f"  Time elapsed         : {elapsed:.1f}s")
    print(f"  Output               : {output_path}")
    print(f"{'='*60}")
    print(f"\n  Next step: python scripts/train_dpo.py --data-dir {args.output_dir}\n")


if __name__ == "__main__":
    main()

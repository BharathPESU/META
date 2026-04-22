#!/usr/bin/env python3
"""
generate_dpo_fast.py — Fast rule-based DPO dataset generator.

Generates high-quality DPO training pairs in seconds using the hospital simulation
environment and a library of pre-defined clinical reasoning templates.

For DPO training, what matters is: chosen_reward > rejected_reward.
The reward model is fully deterministic — we exploit this to generate thousands
of perfect pairs without slow LLM inference.

Usage:
    python scripts/generate_dpo_fast.py --pairs 1000
    python scripts/generate_dpo_fast.py --pairs 5000 --output-dir data/full_training
    python scripts/generate_dpo_fast.py --pairs 500 --difficulty 0.9
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from triage.env.hospital_env import HospitalEnv
from triage.env.state import (
    ActionType,
    AgentAction,
    AgentType,
    CrisisType,
    EnvironmentState,
    PatientStatus,
)
from triage.rewards.reward_model import RewardModel

logger = logging.getLogger(__name__)


# ─── Clinical Reasoning Templates ─────────────────────────────
# Each tuple: (agent_type, action_type, reasoning_template)
# These are the CHOSEN (correct) behaviors the model should learn.

CHOSEN_TEMPLATES: list[tuple[AgentType, ActionType, str]] = [
    # ── Triage Agent correct behaviors ────────────────────────
    (AgentType.ER_TRIAGE, ActionType.TRIAGE_PATIENT,
     "Patient presents with {condition} and triage score {score:.2f}; "
     "immediate triage assessment required to assign correct acuity level."),
    (AgentType.ER_TRIAGE, ActionType.ESCALATE_TO_CMO,
     "Patient {condition} requires ICU bed but chain of command requires CMO authorization "
     "before ICU_MANAGEMENT can allocate — escalating per protocol."),
    (AgentType.ER_TRIAGE, ActionType.ASSIGN_TREATMENT,
     "Initiating treatment protocol for {condition} patient; "
     "stabilizing vitals before deciding on ward transfer."),
    (AgentType.ER_TRIAGE, ActionType.FLAG_POLICY_VIOLATION,
     "Detected unauthorized direct medication order bypassing PHARMACY agent; "
     "flagging as policy violation per workflow rules."),
    (AgentType.ER_TRIAGE, ActionType.SEND_MESSAGE,
     "Notifying ICU_MANAGEMENT of incoming critical {condition} patient "
     "with triage score {score:.2f} — requires pre-authorization."),

    # ── ICU Management correct behaviors ──────────────────────
    (AgentType.ICU_MANAGEMENT, ActionType.TRANSFER_TO_ICU,
     "CMO override token received — allocating ICU bed for critical {condition} patient "
     "with triage score {score:.2f}. Ventilator pre-checked."),
    (AgentType.ICU_MANAGEMENT, ActionType.ACTIVATE_OVERFLOW,
     "ICU occupancy at {occupancy:.0f}% — activating overflow protocol "
     "to add surge beds without violating patient safety standards."),
    (AgentType.ICU_MANAGEMENT, ActionType.FLAG_POLICY_VIOLATION,
     "ER_TRIAGE attempted direct ICU bed allocation bypassing authorization chain; "
     "blocked and flagging as chain-of-command bypass."),
    (AgentType.ICU_MANAGEMENT, ActionType.ASSIGN_TREATMENT,
     "ICU patient {condition} treatment plan updated following specialist review; "
     "deterioration rate reduced with targeted intervention."),

    # ── CMO Oversight correct behaviors ───────────────────────
    (AgentType.CMO_OVERSIGHT, ActionType.OVERRIDE_DECISION,
     "Reviewing escalation request: patient {condition} with score {score:.2f} "
     "is critical. Issuing CMO override token to authorize ICU allocation."),
    (AgentType.CMO_OVERSIGHT, ActionType.FLAG_POLICY_VIOLATION,
     "Audit log shows unauthorized pharmacy dispense attempt by non-PHARMACY agent; "
     "issuing formal violation notice and alerting compliance."),
    (AgentType.CMO_OVERSIGHT, ActionType.ACTIVATE_OVERFLOW,
     "Mass casualty event exceeds ICU capacity — authorizing overflow activation "
     "to ensure critical patients receive adequate care."),
    (AgentType.CMO_OVERSIGHT, ActionType.ESCALATE_TO_CMO,
     "Multiple simultaneous critical patients detected; requesting department-wide "
     "resource audit before authorizing further ICU transfers."),

    # ── Pharmacy correct behaviors ─────────────────────────────
    (AgentType.PHARMACY, ActionType.ORDER_MEDICATION,
     "Processing medication dispense for {condition}: double-verification complete "
     "for controlled substance, allergy check cleared, authorization confirmed."),
    (AgentType.PHARMACY, ActionType.FLAG_POLICY_VIOLATION,
     "Non-PHARMACY agent attempted to order morphine without authorization; "
     "dispensing blocked and policy violation flagged to CMO."),
    (AgentType.PHARMACY, ActionType.ASSIGN_TREATMENT,
     "Medication-adjusted treatment plan issued for {condition} patient "
     "per updated formulary guidelines — dose optimized for critical status."),

    # ── HR Rostering correct behaviors ────────────────────────
    (AgentType.HR_ROSTERING, ActionType.REQUEST_STAFF,
     "Staff shortage detected in ICU ward ({occupancy:.0f}% capacity); "
     "requesting emergency rostering of on-call physicians and nurses."),
    (AgentType.HR_ROSTERING, ActionType.FLAG_POLICY_VIOLATION,
     "Staff overtime threshold violated — flagging for compliance review "
     "to prevent fatigue-related patient safety incidents."),

    # ── IT Systems correct behaviors ──────────────────────────
    (AgentType.IT_SYSTEMS, ActionType.UPDATE_EHR,
     "EHR schema updated following {condition} protocol revision; "
     "audit trail preserved and all agents notified of API changes."),
    (AgentType.IT_SYSTEMS, ActionType.FLAG_POLICY_VIOLATION,
     "Anomalous API call pattern detected — agent attempting to access "
     "restricted EHR fields without authorization; access blocked."),
]

# ─── Rejected templates (deliberate workflow violations) ───────
# These are the WRONG behaviors the model learns to avoid.

REJECTED_TEMPLATES: list[tuple[AgentType, ActionType, str]] = [
    # Chain-of-command bypasses (most common violation)
    (AgentType.ER_TRIAGE, ActionType.TRANSFER_TO_ICU,
     "Transferring patient directly to ICU — critical situation justifies "
     "skipping authorization. Will sort paperwork later."),
    (AgentType.ER_TRIAGE, ActionType.ORDER_MEDICATION,
     "Ordering morphine directly for critical patient — emergency justifies "
     "bypassing pharmacy workflow."),
    (AgentType.CMO_OVERSIGHT, ActionType.ORDER_MEDICATION,
     "CMO directly ordering medication without pharmacy review — "
     "efficiency demands we skip the standard verification process."),
    (AgentType.HR_ROSTERING, ActionType.TRANSFER_TO_ICU,
     "Assigning staff and moving patient to ICU simultaneously — HR role "
     "can cover ICU allocation when management is busy."),
    (AgentType.IT_SYSTEMS, ActionType.ORDER_MEDICATION,
     "IT agent updating medication records and dispensing simultaneously — "
     "system integration makes this efficient."),
    (AgentType.IT_SYSTEMS, ActionType.TRANSFER_TO_ICU,
     "Automated ICU transfer triggered by EHR alert — IT system can directly "
     "allocate beds based on acuity scores."),

    # Missing prechecks
    (AgentType.ICU_MANAGEMENT, ActionType.TRANSFER_TO_ICU,
     "Allocating ICU bed without waiting for CMO override token — "
     "patient is critical and time is of the essence."),
    (AgentType.PHARMACY, ActionType.ORDER_MEDICATION,
     "Dispensing controlled substance without double-verification — "
     "patient is in distress, paperwork can wait."),

    # Idle / wrong action for context
    (AgentType.ER_TRIAGE, ActionType.CLOSE_CASE,
     "Closing out patient case — removing from queue to reduce system load."),
    (AgentType.ICU_MANAGEMENT, ActionType.UPDATE_EHR,
     "Updating records instead of treating critical patient — "
     "documentation compliance is priority."),

    # Policy violation ignored
    (AgentType.CMO_OVERSIGHT, ActionType.OVERRIDE_DECISION,
     "Issuing blanket override for all medications to speed up workflow — "
     "individual case review is too slow during a crisis."),
    (AgentType.HR_ROSTERING, ActionType.ORDER_MEDICATION,
     "HR agent coordinating medication orders during staff shortage — "
     "cross-role coverage is necessary in emergencies."),
]


# ─── Action Builder ────────────────────────────────────────────

def _build_action(
    agent_type: AgentType,
    action_type: ActionType,
    reasoning: str,
    state: EnvironmentState,
    priority: int = 3,
) -> AgentAction:
    """Build an AgentAction from template + current state."""
    critical = [p for p in state.patients if p.status == PatientStatus.CRITICAL]
    target_id = 0
    if critical:
        raw_id = critical[0].id  # e.g. "patient-0001" or a UUID
        # Extract numeric part safely
        parts = raw_id.replace("-", "").replace("_", "")
        digits = "".join(c for c in parts if c.isdigit())
        target_id = int(digits[-4:], 10) % 50 if digits else 0

    return AgentAction(
        agent_type=agent_type,
        action_type=action_type,
        target_id=target_id,
        priority=priority,
        reasoning=reasoning,
        reasoning_tokens=len(reasoning.split()),
    )


def _fill_template(template: str, state: EnvironmentState) -> str:
    """Fill placeholders in a reasoning template from current state."""
    critical = [p for p in state.patients if p.status == PatientStatus.CRITICAL]
    condition = critical[0].condition if critical else "acute trauma"
    score = critical[0].triage_score if critical else 0.85
    occupancy = state.icu_occupancy * 100

    try:
        return template.format(
            condition=condition,
            score=score,
            occupancy=occupancy,
        )
    except (KeyError, IndexError):
        return template


def _format_pair(
    prompt: str,
    chosen: AgentAction,
    rejected: AgentAction,
    chosen_reward: float,
    rejected_reward: float,
    episode: int,
    step: int,
    crisis_type: str,
) -> dict[str, Any]:
    """Format into Hugging Face DPO standard format."""

    def action_to_text(action: AgentAction) -> str:
        return (
            f"Agent: {action.agent_type.value}\n"
            f"Action: {action.action_type.name}\n"
            f"Priority: {action.priority}\n"
            f"Reasoning: {action.reasoning}"
        )

    return {
        "prompt": prompt,
        "chosen": action_to_text(chosen),
        "rejected": action_to_text(rejected),
        "metadata": {
            "episode": episode,
            "step": step,
            "crisis_type": crisis_type,
            "chosen_reward": round(chosen_reward, 4),
            "rejected_reward": round(rejected_reward, 4),
            "reward_margin": round(chosen_reward - rejected_reward, 4),
            "generator": "rule_based_fast",
        },
    }


def _build_prompt(state: EnvironmentState) -> str:
    """Build a compact prompt from state — same format as the Ollama generator."""
    critical = [p for p in state.patients if p.status == PatientStatus.CRITICAL]
    serious = [p for p in state.patients if p.status == PatientStatus.SERIOUS]
    untreated = [p for p in critical if not p.treatment_plan]

    crisis_summary = (
        f"Crisis: {state.crisis.type.value} | "
        f"Step: {state.step_count} | "
        f"ICU: {state.resources.icu_beds_occupied}/{state.resources.icu_beds_total} beds | "
        f"Ventilators: {state.resources.ventilators_in_use}/{state.resources.ventilators_total}"
    )
    patient_summary = (
        f"Patients — Critical: {len(critical)}, Serious: {len(serious)}, "
        f"Untreated Critical: {len(untreated)}, Deceased: {state.deceased_count}"
    )

    focus_patient = untreated[0] if untreated else (critical[0] if critical else None)
    patient_context = ""
    if focus_patient:
        patient_context = (
            f"\nMost urgent patient: ID={focus_patient.id} "
            f"| Condition={focus_patient.condition} "
            f"| Status={focus_patient.status.value} "
            f"| Triage Score={focus_patient.triage_score:.2f}"
        )

    return (
        f"Hospital Crisis Management System — Step {state.step_count}\n"
        f"{crisis_summary}\n"
        f"{patient_summary}{patient_context}\n"
        f"Policy Violations — Injected: {state.violations_injected}, "
        f"Caught: {state.violations_caught}"
    )


# ─── Core Generator ────────────────────────────────────────────

async def generate_pairs(
    target_pairs: int,
    difficulty: float,
    seed: int,
    output_dir: Path,
) -> None:
    """Main generation loop using rule-based approach."""
    random.seed(seed)

    env = HospitalEnv(seed=seed, max_steps=100, difficulty=difficulty)
    reward_model = RewardModel()

    output_path = output_dir / "dpo_pairs.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    crisis_types = list(CrisisType)
    all_pairs: list[dict[str, Any]] = []

    stats = {
        "pairs_generated": 0,
        "pairs_skipped": 0,
        "episodes": 0,
    }

    print(f"\n{'='*60}")
    print("  TRIAGE — Fast DPO Dataset Generator")
    print(f"{'='*60}")
    print(f"  Target pairs : {target_pairs}")
    print(f"  Difficulty   : {difficulty}")
    print(f"  Seed         : {seed}")
    print(f"  Output       : {output_path}")
    print(f"{'='*60}\n")

    start_time = time.perf_counter()
    episode_idx = 0

    while stats["pairs_generated"] < target_pairs:
        # Reset env with random crisis
        scenario = {
            "crisis_type": random.choice(crisis_types).value,
            "difficulty": difficulty,
        }
        await env.reset(scenario=scenario)
        crisis_type = env.state.crisis.type.value
        stats["episodes"] += 1
        episode_idx += 1

        step = 0
        while not env.is_terminal and stats["pairs_generated"] < target_pairs:
            state = env.state

            # ── Sample a chosen + rejected template pair ───────
            chosen_tmpl = random.choice(CHOSEN_TEMPLATES)
            rejected_tmpl = random.choice(REJECTED_TEMPLATES)

            # Avoid chosen and rejected having same agent + action
            retries = 0
            while (
                chosen_tmpl[0] == rejected_tmpl[0]
                and chosen_tmpl[1] == rejected_tmpl[1]
                and retries < 5
            ):
                rejected_tmpl = random.choice(REJECTED_TEMPLATES)
                retries += 1

            chosen_reasoning = _fill_template(chosen_tmpl[2], state)
            rejected_reasoning = _fill_template(rejected_tmpl[2], state)

            chosen_action = _build_action(
                chosen_tmpl[0], chosen_tmpl[1], chosen_reasoning, state,
                priority=random.randint(2, 4),
            )
            rejected_action = _build_action(
                rejected_tmpl[0], rejected_tmpl[1], rejected_reasoning, state,
                priority=random.randint(0, 2),
            )

            # ── Score via RewardModel ──────────────────────────
            chosen_breakdown = reward_model.compute(
                state=state,
                actions=[chosen_action],
                action_result={"success": True},
            )
            rejected_breakdown = reward_model.compute(
                state=state,
                actions=[rejected_action],
                action_result={
                    "success": False,
                    "error": "Chain of command bypass blocked",
                },
                app_audits=list(state.app_audit_log),
            )

            chosen_reward = chosen_breakdown.total
            rejected_reward = rejected_breakdown.total

            # Only keep valid DPO pairs (chosen strictly better)
            if chosen_reward > rejected_reward:
                prompt = _build_prompt(state)
                pair = _format_pair(
                    prompt=prompt,
                    chosen=chosen_action,
                    rejected=rejected_action,
                    chosen_reward=chosen_reward,
                    rejected_reward=rejected_reward,
                    episode=episode_idx,
                    step=step,
                    crisis_type=crisis_type,
                )
                all_pairs.append(pair)
                stats["pairs_generated"] += 1
            else:
                stats["pairs_skipped"] += 1

            # Advance env with the chosen action (best action)
            action_dict = {
                "agent_id": list(AgentType).index(chosen_action.agent_type),
                "action_type": chosen_action.action_type.value,
                "target_id": chosen_action.target_id,
                "priority": chosen_action.priority,
                "reasoning": chosen_action.reasoning,
                "reasoning_tokens": chosen_action.reasoning_tokens,
            }
            await env.step(action_dict)
            step += 1

        # Progress every 100 pairs
        if stats["pairs_generated"] % 100 == 0 and stats["pairs_generated"] > 0:
            elapsed = time.perf_counter() - start_time
            rate = stats["pairs_generated"] / elapsed
            print(
                f"  Progress: {stats['pairs_generated']:>5}/{target_pairs} pairs | "
                f"Episodes: {stats['episodes']:>3} | "
                f"Rate: {rate:.0f} pairs/sec | "
                f"ETA: {(target_pairs - stats['pairs_generated']) / max(rate, 0.001):.0f}s"
            )

    # ── Write output ───────────────────────────────────────────
    with output_path.open("w", encoding="utf-8") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    elapsed = time.perf_counter() - start_time

    print(f"\n{'='*60}")
    print("  GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"  DPO pairs generated  : {stats['pairs_generated']}")
    print(f"  Pairs skipped        : {stats['pairs_skipped']} (reward check failed)")
    print(f"  Episodes used        : {stats['episodes']}")
    print(f"  Time elapsed         : {elapsed:.2f}s ({elapsed/60:.1f} min)")
    print(f"  Generation rate      : {stats['pairs_generated']/elapsed:.0f} pairs/sec")
    print(f"  Output file          : {output_path}")
    print(f"  File size            : {output_path.stat().st_size / 1024:.1f} KB")
    print(f"{'='*60}")
    print(f"\n  Next step: python scripts/train_dpo.py --data-dir {output_dir}\n")

    # ── Validate output ────────────────────────────────────────
    print("  Validating output format...")
    with output_path.open() as f:
        first = json.loads(f.readline())
    assert "prompt" in first, "Missing 'prompt' key"
    assert "chosen" in first, "Missing 'chosen' key"
    assert "rejected" in first, "Missing 'rejected' key"
    margin = first["metadata"]["reward_margin"]
    assert margin > 0, f"Reward margin should be positive, got {margin}"
    print(f"  ✓ Format valid — first pair reward_margin: {margin:.4f}")
    print("  ✓ Ready for DPO training!\n")


# ─── CLI ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fast rule-based DPO dataset generation for TRIAGE"
    )
    parser.add_argument(
        "--pairs",
        type=int,
        default=1000,
        help="Number of DPO pairs to generate (default: 1000)",
    )
    parser.add_argument(
        "--difficulty",
        type=float,
        default=0.6,
        help="Crisis difficulty 0.0–1.0 (default: 0.6)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/full_training",
        help="Output directory for dpo_pairs.jsonl (default: ./data/full_training)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
    )

    asyncio.run(
        generate_pairs(
            target_pairs=args.pairs,
            difficulty=args.difficulty,
            seed=args.seed,
            output_dir=Path(args.output_dir),
        )
    )


if __name__ == "__main__":
    main()

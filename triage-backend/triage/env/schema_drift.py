"""
SchemaDrift — mid-episode policy mutation engine.

Injects policy changes, expert signal shifts, and environmental perturbations
to test agent adaptability and compliance awareness.
"""

from __future__ import annotations

import random
from typing import Any

from triage.env.state import (
    EnvironmentState,
    Policy,
    PolicyChange,
)


class SchemaDrift:
    """Mutates policies and expert signals during an episode.

    Tracks all changes so the reward model can evaluate agent adaptation.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.changes: list[PolicyChange] = []
        self._drift_schedule: list[dict[str, Any]] = []

    def plan_drifts(self, episode_length: int, difficulty: float) -> None:
        """Pre-plan drift events for the episode.

        Higher difficulty → more frequent and severe drifts.
        """
        self._drift_schedule.clear()
        self.changes.clear()

        # Number of drift events scales with difficulty
        num_drifts = max(1, int(difficulty * 5))

        # Spread drifts across the episode, avoiding first 10% and last 5%
        min_step = max(3, int(episode_length * 0.1))
        max_step = int(episode_length * 0.95)

        drift_steps = sorted(
            self.rng.sample(range(min_step, max_step), k=min(num_drifts, max_step - min_step))
        )

        drift_types = [
            "policy_update",
            "expert_signal_shift",
            "resource_shock",
            "policy_addition",
            "policy_removal",
        ]

        for step in drift_steps:
            self._drift_schedule.append({
                "step": step,
                "type": self.rng.choice(drift_types),
                "applied": False,
            })

    def apply_drifts(self, state: EnvironmentState) -> list[dict[str, Any]]:
        """Apply any scheduled drifts for the current step.

        Returns list of drift events that were applied (for broadcasting to agents).
        """
        applied_events: list[dict[str, Any]] = []

        for drift in self._drift_schedule:
            if drift["applied"] or drift["step"] != state.step_count:
                continue

            drift["applied"] = True
            event = self._apply_single_drift(drift["type"], state)
            if event:
                applied_events.append(event)

        return applied_events

    def _apply_single_drift(
        self,
        drift_type: str,
        state: EnvironmentState,
    ) -> dict[str, Any] | None:
        handlers = {
            "policy_update": self._drift_policy_update,
            "expert_signal_shift": self._drift_expert_signal,
            "resource_shock": self._drift_resource_shock,
            "policy_addition": self._drift_policy_addition,
            "policy_removal": self._drift_policy_removal,
        }
        handler = handlers.get(drift_type)
        if handler:
            return handler(state)
        return None

    def _drift_policy_update(self, state: EnvironmentState) -> dict[str, Any]:
        """Modify an existing policy rule."""
        if not state.active_policies:
            return self._drift_policy_addition(state)

        policy_id = self.rng.choice(list(state.active_policies.keys()))
        policy = state.active_policies[policy_id]

        if not policy.rules:
            return {"type": "policy_update", "status": "no_rules_to_modify"}

        rule_idx = self.rng.randint(0, len(policy.rules) - 1)
        old_rule = policy.rules[rule_idx]

        # Generate a realistic rule mutation
        mutations = {
            "triage_protocol": [
                "Triage window extended to 10 minutes during surge",
                "Re-triage interval changed to 30 minutes",
                "Walking wounded may self-triage to free up staff",
            ],
            "icu_admission": [
                "ICU admission threshold lowered to triage score >= 6",
                "ICU nurse ratio relaxed to 1:3 during crisis",
                "Overflow protocol activates at 80% occupancy",
            ],
            "medication_safety": [
                "Single-verification acceptable for non-controlled substances during crisis",
                "Pharmacist may delegate verification to senior nurse",
                "Emergency drug kits may be used without prior authorization",
            ],
            "staff_fatigue": [
                "Crisis exception: physician may work up to 20 hours with CMO approval",
                "Break interval extended to 8 hours during Code Orange",
                "Fatigued staff may continue with buddy-system supervision",
            ],
            "data_privacy": [
                "Screen lock timeout extended to 5 minutes during crisis",
                "Verbal orders acceptable with documentation within 1 hour",
                "Cross-team data sharing permitted for crisis patients only",
            ],
        }

        new_rules = mutations.get(policy_id, ["Policy updated for crisis conditions"])
        new_rule = self.rng.choice(new_rules)
        policy.rules[rule_idx] = new_rule

        # Bump version
        major, minor = policy.version.split(".")
        policy.version = f"{major}.{int(minor) + 1}"

        change = PolicyChange(
            policy_id=policy_id,
            change_type="modified",
            old_value=old_rule,
            new_value=new_rule,
            episode=state.episode,
        )
        self.changes.append(change)

        return {
            "type": "policy_update",
            "policy_id": policy_id,
            "policy_name": policy.name,
            "old_rule": old_rule,
            "new_rule": new_rule,
            "new_version": policy.version,
            "message": f"⚠️ POLICY UPDATE: {policy.name} v{policy.version} — rule modified",
        }

    def _drift_expert_signal(self, state: EnvironmentState) -> dict[str, Any]:
        """Shift expert weight signals (cost vs quality vs speed)."""
        signal_key = self.rng.choice(["cost_weight", "quality_weight", "speed_weight"])
        old_value = state.expert_signals.get(signal_key, 0.33)

        # Shift by ±0.1 to ±0.3
        delta = self.rng.uniform(-0.3, 0.3)
        new_value = max(0.0, min(1.0, old_value + delta))
        state.expert_signals[signal_key] = new_value

        # Normalize so weights sum to ~1.0
        total = sum(
            state.expert_signals.get(k, 0.33)
            for k in ["cost_weight", "quality_weight", "speed_weight"]
        )
        if total > 0:
            for k in ["cost_weight", "quality_weight", "speed_weight"]:
                state.expert_signals[k] = state.expert_signals.get(k, 0.33) / total

        return {
            "type": "expert_signal_shift",
            "signal": signal_key,
            "old_value": round(old_value, 3),
            "new_value": round(new_value, 3),
            "message": f"📊 EXPERT SIGNAL: {signal_key} shifted from {old_value:.2f} → {new_value:.2f}",
        }

    def _drift_resource_shock(self, state: EnvironmentState) -> dict[str, Any]:
        """Sudden resource change — equipment failure, supply arrival, etc."""
        shocks = [
            {
                "resource": "equipment_status",
                "delta": -0.3,
                "description": "Critical equipment malfunction — 30% capacity loss",
            },
            {
                "resource": "blood_supply_oneg",
                "delta": -0.4,
                "description": "Blood bank supply critically low — O-negative shortage",
            },
            {
                "resource": "pharmacy_stock",
                "delta": -0.2,
                "description": "Pharmacy delivery delayed — stock running low",
            },
            {
                "resource": "it_uptime",
                "delta": -0.5,
                "description": "Network outage — IT systems partially offline",
            },
            {
                "resource": "staff_ratio",
                "delta": -0.25,
                "description": "Shift change gap — staff coverage dropped",
            },
            {
                "resource": "blood_supply_ab",
                "delta": 0.3,
                "description": "Emergency blood shipment arrived from Red Cross",
            },
            {
                "resource": "pharmacy_stock",
                "delta": 0.2,
                "description": "Emergency pharmaceutical delivery received",
            },
        ]

        shock = self.rng.choice(shocks)
        attr = shock["resource"]
        if hasattr(state.resources, attr):
            current = getattr(state.resources, attr)
            new_val = max(0.0, min(1.0, current + shock["delta"]))
            setattr(state.resources, attr, new_val)

        return {
            "type": "resource_shock",
            "resource": attr,
            "delta": shock["delta"],
            "description": shock["description"],
            "message": f"🔴 RESOURCE SHOCK: {shock['description']}",
        }

    def _drift_policy_addition(self, state: EnvironmentState) -> dict[str, Any]:
        """Add a new policy mid-episode."""
        new_policies = [
            Policy(
                id="POL-SURGE-001",
                name="Surge Capacity Protocol",
                version="1.0",
                rules=[
                    "Non-clinical spaces may be converted to patient holding",
                    "Discharge criteria relaxed for stable patients",
                    "Elective admissions suspended for 24 hours",
                ],
                effective_from=state.step_count,
            ),
            Policy(
                id="POL-DECON-001",
                name="Decontamination Protocol",
                version="1.0",
                rules=[
                    "All mass casualty patients require decon screening",
                    "Chemical exposure patients isolated in Zone C",
                    "PPE Level C minimum for decon team",
                ],
                effective_from=state.step_count,
            ),
            Policy(
                id="POL-COMM-001",
                name="Crisis Communication Protocol",
                version="1.0",
                rules=[
                    "All media inquiries routed to PIO only",
                    "Patient status updates every 30 minutes to family liaison",
                    "No social media posts from staff during Code Orange",
                ],
                effective_from=state.step_count,
            ),
        ]

        new_policy = self.rng.choice(new_policies)
        if new_policy.id not in state.active_policies:
            state.active_policies[new_policy.id] = new_policy
            change = PolicyChange(
                policy_id=new_policy.id,
                change_type="added",
                old_value=None,
                new_value=new_policy.name,
                episode=state.episode,
            )
            self.changes.append(change)
            return {
                "type": "policy_addition",
                "policy_id": new_policy.id,
                "policy_name": new_policy.name,
                "rules": new_policy.rules,
                "message": f"📋 NEW POLICY: {new_policy.name} now in effect",
            }

        return {"type": "policy_addition", "status": "policy_already_exists"}

    def _drift_policy_removal(self, state: EnvironmentState) -> dict[str, Any]:
        """Deactivate a policy (e.g., crisis override)."""
        removable = [
            pid for pid, p in state.active_policies.items()
            if p.is_active and pid not in ("triage_protocol", "medication_safety")
        ]
        if not removable:
            return {"type": "policy_removal", "status": "no_removable_policies"}

        pid = self.rng.choice(removable)
        policy = state.active_policies[pid]
        policy.is_active = False

        change = PolicyChange(
            policy_id=pid,
            change_type="removed",
            old_value=policy.name,
            new_value=None,
            episode=state.episode,
        )
        self.changes.append(change)

        return {
            "type": "policy_removal",
            "policy_id": pid,
            "policy_name": policy.name,
            "message": f"❌ POLICY SUSPENDED: {policy.name} — crisis override in effect",
        }

    def get_all_changes(self) -> list[dict[str, Any]]:
        return [
            {
                "policy_id": c.policy_id,
                "change_type": c.change_type,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "episode": c.episode,
            }
            for c in self.changes
        ]

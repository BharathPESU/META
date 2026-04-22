"""Policy compliance reward component."""

from __future__ import annotations

from triage.env.state import ActionType, EnvironmentState


class ComplianceReward:
    """Rewards actions that align with current policy state."""

    def compute(self, state: EnvironmentState) -> float:
        if state.violations_injected == 0:
            return 0.5

        detection_rate = state.violations_caught / max(state.violations_injected, 1)
        proactive_flags = sum(
            1 for action in state.action_history
            if action.action_type == ActionType.FLAG_POLICY_VIOLATION
        )
        own_violations = sum(agent.violations_count for agent in state.agent_states.values())
        score = detection_rate * 0.75 + min(proactive_flags * 0.05, 0.2) - own_violations * 0.01
        return max(-1.0, min(1.0, score))

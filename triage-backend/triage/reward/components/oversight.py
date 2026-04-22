"""CMO oversight reward component."""

from __future__ import annotations

from triage.env.state import ActionType, AgentType, EnvironmentState


class OversightReward:
    """Rewards the CMO for catching violations and issuing oversight actions."""

    def compute(self, state: EnvironmentState) -> float:
        if state.violations_injected == 0:
            return 0.5

        caught_rate = state.violations_caught / max(state.violations_injected, 1)
        cmo_flags = sum(
            1
            for action in state.action_history
            if action.agent_type == AgentType.CMO_OVERSIGHT
            and action.action_type in (ActionType.FLAG_POLICY_VIOLATION, ActionType.OVERRIDE_DECISION)
        )
        score = caught_rate * 0.8 + min(cmo_flags * 0.05, 0.2)
        return max(-1.0, min(1.0, score))

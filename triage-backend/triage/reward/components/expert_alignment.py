"""Expert-alignment reward component."""

from __future__ import annotations

from triage.env.state import EnvironmentState


class ExpertAlignmentReward:
    """Aligns outcomes with the simulated expert preferences."""

    def compute(self, state: EnvironmentState) -> float:
        signals = state.expert_signals
        cost_weight = signals.get("cost_weight", 0.33)
        quality_weight = signals.get("quality_weight", 0.33)
        speed_weight = signals.get("speed_weight", 0.33)

        quality_actual = state.survival_rate
        speed_actual = max(0.0, 1.0 - (state.step_count / 200))
        token_usage = sum(agent.token_usage for agent in state.agent_states.values())
        cost_actual = max(0.0, 1.0 - min(token_usage / 50_000, 1.0))

        score = (
            quality_weight * quality_actual
            + speed_weight * speed_actual
            + cost_weight * cost_actual
        )
        return max(-1.0, min(1.0, score))

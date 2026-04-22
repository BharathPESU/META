"""Reasoning depth reward component."""

from __future__ import annotations

import math

from triage.env.state import AgentAction


class DepthReward:
    """Rewards richer reasoning while capping token padding."""

    def compute(self, actions: list[AgentAction]) -> float:
        if not actions:
            return 0.0
        avg_tokens = sum(action.reasoning_tokens for action in actions) / len(actions)
        if avg_tokens <= 0:
            return 0.0
        return min(math.log(avg_tokens + 1) / math.log(500), 1.0)

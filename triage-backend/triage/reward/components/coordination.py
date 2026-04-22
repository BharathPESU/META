"""Inter-agent coordination reward component."""

from __future__ import annotations

from triage.env.state import AgentType, EnvironmentState, MessageType


class CoordinationReward:
    """Scores handoffs, alerts, and communication quality."""

    def compute(self, state: EnvironmentState) -> float:
        messages = state.message_history
        if not messages:
            return 0.0

        senders = {
            message.from_agent for message in messages if isinstance(message.from_agent, AgentType)
        }
        diversity = len(senders) / max(len(AgentType), 1)
        alerts = [message for message in messages if message.msg_type == MessageType.ALERT]
        alert_quality = (
            sum(1 for message in alerts if message.priority >= 5) / len(alerts)
            if alerts
            else 0.5
        )
        handoffs = [message for message in messages if message.msg_type == MessageType.HANDOFF]
        request_rate = min(len(handoffs) / max(len(messages), 1) * 4.0, 1.0)
        return max(-1.0, min(1.0, diversity * 0.4 + alert_quality * 0.35 + request_rate * 0.25))

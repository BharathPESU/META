"""
MessageBus — typed inter-agent communication system.

Supports:
  - Direct agent-to-agent messages
  - Broadcast to all agents
  - Priority-based message ordering
  - Token budget tracking per message
  - Message history with full audit trail
  - Async pub/sub with optional callbacks
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

from triage.env.state import AgentMessage, AgentType, MessageType

logger = logging.getLogger(__name__)

MessageCallback = Callable[[AgentMessage], Coroutine[Any, Any, None]]


class MessageBus:
    """Typed, async message bus for inter-agent communication.

    Each agent subscribes to receive messages. The bus routes messages
    by target agent or broadcasts to all subscribers.
    """

    def __init__(self, token_budget: int = 50_000) -> None:
        self._subscribers: dict[AgentType, list[MessageCallback]] = defaultdict(list)
        self._broadcast_subscribers: list[MessageCallback] = []
        self._history: list[AgentMessage] = []
        self._token_budget = token_budget
        self._tokens_used = 0
        self._message_count = 0
        self._lock = asyncio.Lock()

    # ── Subscription ─────────────────────────────────────

    def subscribe(self, agent_type: AgentType, callback: MessageCallback) -> None:
        """Subscribe an agent to receive direct messages."""
        self._subscribers[agent_type].append(callback)
        logger.debug("Agent %s subscribed to message bus", agent_type.value)

    def subscribe_broadcast(self, callback: MessageCallback) -> None:
        """Subscribe to all broadcast messages."""
        self._broadcast_subscribers.append(callback)

    def unsubscribe_all(self, agent_type: AgentType) -> None:
        """Remove all subscriptions for an agent."""
        self._subscribers.pop(agent_type, None)

    # ── Sending ──────────────────────────────────────────

    async def send(self, message: AgentMessage) -> bool:
        """Send a message to a specific agent or broadcast.

        Returns True if message was delivered, False if budget exceeded.
        """
        async with self._lock:
            # Token budget check
            if self._tokens_used + message.token_count > self._token_budget:
                logger.warning(
                    "Token budget exceeded: %d + %d > %d",
                    self._tokens_used,
                    message.token_count,
                    self._token_budget,
                )
                return False

            self._tokens_used += message.token_count
            self._message_count += 1
            self._history.append(message)

        # Route message
        if message.to_agent == "ALL" or message.msg_type == MessageType.BROADCAST:
            await self._broadcast(message)
        elif isinstance(message.to_agent, AgentType):
            await self._deliver(message.to_agent, message)
        else:
            # Try to parse string agent type
            try:
                target = AgentType(str(message.to_agent))
                await self._deliver(target, message)
            except ValueError:
                logger.warning("Unknown target agent: %s", message.to_agent)
                return False

        return True

    async def send_and_wait(
        self,
        message: AgentMessage,
        timeout: float = 30.0,
    ) -> AgentMessage | None:
        """Send a message and wait for a response.

        Returns the response message or None if timeout.
        """
        message.requires_response = True
        response_event = asyncio.Event()
        response_msg: list[AgentMessage] = []

        # Temporary subscription for the response
        async def _response_handler(msg: AgentMessage) -> None:
            if (
                msg.msg_type == MessageType.RESPONSE
                and msg.action_id == message.id
            ):
                response_msg.append(msg)
                response_event.set()

        if isinstance(message.from_agent, AgentType):
            self._subscribers[message.from_agent].append(_response_handler)

        sent = await self.send(message)
        if not sent:
            return None

        try:
            await asyncio.wait_for(response_event.wait(), timeout=timeout)
            return response_msg[0] if response_msg else None
        except asyncio.TimeoutError:
            logger.warning("Response timeout for message %s", message.id)
            return None
        finally:
            if isinstance(message.from_agent, AgentType):
                try:
                    self._subscribers[message.from_agent].remove(_response_handler)
                except ValueError:
                    pass

    # ── Query ────────────────────────────────────────────

    @property
    def history(self) -> list[AgentMessage]:
        return list(self._history)

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    @property
    def tokens_remaining(self) -> int:
        return max(0, self._token_budget - self._tokens_used)

    @property
    def message_count(self) -> int:
        return self._message_count

    def get_messages_for(
        self,
        agent_type: AgentType,
        limit: int = 50,
        msg_type: MessageType | None = None,
    ) -> list[AgentMessage]:
        """Get recent messages sent to a specific agent."""
        msgs = [
            m for m in self._history
            if (
                (isinstance(m.to_agent, AgentType) and m.to_agent == agent_type)
                or m.to_agent == "ALL"
                or m.msg_type == MessageType.BROADCAST
            )
            and (msg_type is None or m.msg_type == msg_type)
        ]
        return msgs[-limit:]

    def get_conversation(
        self,
        agent_a: AgentType,
        agent_b: AgentType,
        limit: int = 20,
    ) -> list[AgentMessage]:
        """Get message history between two agents."""
        msgs = [
            m for m in self._history
            if (
                (m.from_agent == agent_a and m.to_agent == agent_b)
                or (m.from_agent == agent_b and m.to_agent == agent_a)
            )
        ]
        return msgs[-limit:]

    def stats(self) -> dict[str, Any]:
        """Return message bus statistics."""
        by_type: dict[str, int] = defaultdict(int)
        by_agent: dict[str, int] = defaultdict(int)
        for m in self._history:
            by_type[m.msg_type.value] += 1
            sender = m.from_agent.value if isinstance(m.from_agent, AgentType) else str(m.from_agent)
            by_agent[sender] += 1

        return {
            "total_messages": self._message_count,
            "tokens_used": self._tokens_used,
            "tokens_remaining": self.tokens_remaining,
            "budget_utilization": self._tokens_used / max(self._token_budget, 1),
            "by_type": dict(by_type),
            "by_agent": dict(by_agent),
        }

    # ── Reset ────────────────────────────────────────────

    def reset(self) -> None:
        """Clear all state for a new episode."""
        self._history.clear()
        self._tokens_used = 0
        self._message_count = 0

    # ── Internal ─────────────────────────────────────────

    async def _deliver(self, target: AgentType, message: AgentMessage) -> None:
        callbacks = self._subscribers.get(target, [])
        for cb in callbacks:
            try:
                await cb(message)
            except Exception:
                logger.exception("Error delivering message to %s", target.value)

    async def _broadcast(self, message: AgentMessage) -> None:
        tasks = []
        # Deliver to all agent subscribers
        for agent_type, callbacks in self._subscribers.items():
            if isinstance(message.from_agent, AgentType) and agent_type == message.from_agent:
                continue  # don't echo back to sender
            for cb in callbacks:
                tasks.append(cb(message))

        # Also deliver to broadcast subscribers
        for cb in self._broadcast_subscribers:
            tasks.append(cb(message))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.exception("Broadcast delivery error: %s", r)

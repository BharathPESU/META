"""
StrategyMemory — cross-episode self-improvement through strategy tracking.

Each agent can:
  - Record strategies used during an episode
  - Track which strategies led to better rewards
  - Retrieve top-performing strategies for future episodes
  - Persist strategy memory to disk (JSON)

This enables the "self-improvement" loop: agents refine their
decision-making heuristics across training episodes without fine-tuning.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Strategy:
    """A single strategy entry with performance tracking."""
    id: str
    agent_type: str
    description: str
    crisis_type: str
    episode: int
    reward: float = 0.0
    times_used: int = 1
    success_rate: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "description": self.description,
            "crisis_type": self.crisis_type,
            "episode": self.episode,
            "reward": self.reward,
            "times_used": self.times_used,
            "success_rate": self.success_rate,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Strategy:
        return cls(**data)


class StrategyMemory:
    """Persistent strategy memory for cross-episode learning.

    Strategies are grouped by agent_type × crisis_type for efficient retrieval.
    """

    def __init__(self, storage_path: str = "./data/strategy_memory.json") -> None:
        self._strategies: dict[str, list[Strategy]] = {}  # key: "{agent}:{crisis}"
        self._storage_path = Path(storage_path)
        self._load()

    # ── Recording ────────────────────────────────────────

    def record(
        self,
        agent_type: str,
        crisis_type: str,
        description: str,
        episode: int,
        reward: float,
        success: bool,
        context: dict[str, Any] | None = None,
    ) -> Strategy:
        """Record a strategy used during an episode."""
        key = f"{agent_type}:{crisis_type}"
        strategy_id = f"{agent_type}-ep{episode}-{len(self._strategies.get(key, []))}"

        # Check if similar strategy already exists
        existing = self._find_similar(key, description)
        if existing:
            existing.times_used += 1
            existing.reward = (existing.reward * (existing.times_used - 1) + reward) / existing.times_used
            existing.success_rate = (
                (existing.success_rate * (existing.times_used - 1) + float(success))
                / existing.times_used
            )
            return existing

        strategy = Strategy(
            id=strategy_id,
            agent_type=agent_type,
            description=description,
            crisis_type=crisis_type,
            episode=episode,
            reward=reward,
            success_rate=float(success),
            context=context or {},
        )

        if key not in self._strategies:
            self._strategies[key] = []
        self._strategies[key].append(strategy)

        # Prune to keep top strategies
        self._prune(key, max_entries=50)

        return strategy

    # ── Retrieval ────────────────────────────────────────

    def get_top_strategies(
        self,
        agent_type: str,
        crisis_type: str,
        limit: int = 5,
    ) -> list[Strategy]:
        """Get top-performing strategies for an agent + crisis type."""
        key = f"{agent_type}:{crisis_type}"
        strategies = self._strategies.get(key, [])

        # Sort by composite score: reward × success_rate × log(times_used)
        import math
        scored = sorted(
            strategies,
            key=lambda s: s.reward * s.success_rate * (1 + math.log1p(s.times_used)),
            reverse=True,
        )
        return scored[:limit]

    def get_strategy_prompt(
        self,
        agent_type: str,
        crisis_type: str,
        limit: int = 3,
    ) -> str:
        """Generate a prompt section with top strategies for LLM context."""
        top = self.get_top_strategies(agent_type, crisis_type, limit)
        if not top:
            return "No prior strategies recorded for this scenario."

        lines = ["## Successful Strategies from Previous Episodes\n"]
        for i, s in enumerate(top, 1):
            lines.append(
                f"{i}. **{s.description}**\n"
                f"   Reward: {s.reward:.2f} | Success Rate: {s.success_rate:.0%} | "
                f"Used: {s.times_used} times\n"
            )
        return "\n".join(lines)

    def get_all(self) -> dict[str, list[dict[str, Any]]]:
        """Get all strategies as dicts."""
        return {
            key: [s.to_dict() for s in strategies]
            for key, strategies in self._strategies.items()
        }

    # ── Persistence ──────────────────────────────────────

    def save(self) -> None:
        """Persist strategies to disk."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            key: [s.to_dict() for s in strategies]
            for key, strategies in self._strategies.items()
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info("Saved %d strategy groups to %s", len(data), self._storage_path)

    def _load(self) -> None:
        """Load strategies from disk if available."""
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path) as f:
                data = json.load(f)
            for key, strategies in data.items():
                self._strategies[key] = [Strategy.from_dict(s) for s in strategies]
            logger.info("Loaded %d strategy groups from %s", len(data), self._storage_path)
        except Exception:
            logger.warning("Failed to load strategy memory from %s", self._storage_path)

    # ── Internal ─────────────────────────────────────────

    def _find_similar(self, key: str, description: str) -> Strategy | None:
        """Find a strategy with a similar description (fuzzy match)."""
        for s in self._strategies.get(key, []):
            # Simple similarity — first 50 chars match
            if s.description[:50].lower() == description[:50].lower():
                return s
        return None

    def _prune(self, key: str, max_entries: int = 50) -> None:
        """Keep only the top strategies by reward."""
        strategies = self._strategies.get(key, [])
        if len(strategies) > max_entries:
            strategies.sort(key=lambda s: s.reward * s.success_rate, reverse=True)
            self._strategies[key] = strategies[:max_entries]

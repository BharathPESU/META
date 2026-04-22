"""Official OpenEnv-facing adapter for TRIAGE."""

from __future__ import annotations

from typing import Any

from triage.env.hospital_env import HospitalEnv


try:  # pragma: no cover - import path depends on installed openenv-core release.
    from openenv.core import Environment as OpenEnvEnvironment
except Exception:  # pragma: no cover
    class OpenEnvEnvironment:  # type: ignore[no-redef]
        """Fallback base used when openenv-core is not installed locally."""


class TRIAGEOpenEnv(OpenEnvEnvironment):
    """OpenEnv-compatible wrapper that delegates to the hospital domain engine."""

    def __init__(
        self,
        seed: int | None = None,
        max_steps: int = 200,
        difficulty: float = 0.5,
    ) -> None:
        self.domain_env = HospitalEnv(seed=seed, max_steps=max_steps, difficulty=difficulty)
        self.observation_space = self.domain_env.observation_space
        self.action_space = self.domain_env.action_space

    async def reset(self, scenario: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        return await self.domain_env.reset(scenario)

    async def step(self, action: dict[str, Any]) -> tuple[dict[str, Any], float, bool, dict[str, Any]]:
        return await self.domain_env.step(action)

    async def state(self) -> dict[str, Any]:
        return await self.domain_env.get_state()

    async def close(self) -> None:
        return None

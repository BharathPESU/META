"""Unsloth model presets and launcher helpers."""

from __future__ import annotations

from typing import Any

from triage.training.dpo_trainer import DPOConfig, MODEL_PRESETS, TRIAGEDPOTrainer


def get_training_presets() -> dict[str, dict[str, Any]]:
    """Return stable judge-demo training presets."""

    return dict(MODEL_PRESETS)


def build_config(
    preset: str = "4b_reliable",
    **overrides: Any,
) -> DPOConfig:
    """Build a DPO config from a named preset plus explicit overrides."""

    config = DPOConfig(preset=preset)
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config


def setup_model(model_name: str) -> tuple[Any, Any]:
    """Best-effort model setup for notebooks and optional GPU flows."""

    trainer = TRIAGEDPOTrainer(DPOConfig(preset="custom", model_name=model_name))
    return trainer.setup_model()


async def run_training_preset(
    preset: str = "4b_reliable",
    **overrides: Any,
) -> dict[str, Any]:
    """Run the TRIAGE DPO pipeline for a named Unsloth preset."""

    trainer = TRIAGEDPOTrainer(build_config(preset=preset, **overrides))
    return await trainer.train()

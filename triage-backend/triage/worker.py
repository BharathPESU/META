"""Celery worker entrypoint for TRIAGE background jobs."""

from __future__ import annotations

import asyncio

from celery import Celery

from config.settings import Settings
from triage.training.dpo_trainer import DPOConfig, DPOTrainingPipeline


settings = Settings()
celery_app = Celery("triage", broker=settings.redis_url, backend=settings.redis_url)
app = celery_app


@celery_app.task(name="triage.run_dpo_training")
def run_dpo_training(config: dict | None = None) -> dict:
    """Run the DPO pipeline in a worker process."""

    training_config = DPOConfig(**(config or {}))
    pipeline = DPOTrainingPipeline(training_config)
    return asyncio.run(pipeline.train())

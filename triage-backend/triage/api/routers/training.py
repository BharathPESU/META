"""Training pipeline routes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from triage.api.schemas import ApiResponse, LabelingConfig, TrainingConfig
from triage.api.service import backend_service


router = APIRouter()


@router.post("/collect", response_model=ApiResponse)
async def collect_training_data(config: TrainingConfig) -> ApiResponse:
    return ApiResponse(success=True, data=await backend_service.collect_training_data(config))


@router.post("/label", response_model=ApiResponse)
async def label_preferences(config: LabelingConfig) -> ApiResponse:
    return ApiResponse(
        success=True,
        data=backend_service.label_preferences(config.output_path, min_delta=config.min_delta),
    )


@router.post("/start-dpo", response_model=ApiResponse)
async def start_dpo(config: TrainingConfig) -> ApiResponse:
    return ApiResponse(success=True, data=await backend_service.start_dpo_training(config))


@router.get("/status")
async def training_status() -> JSONResponse:
    """Return live training status — bypasses response_model to preserve nested metrics."""
    return JSONResponse(content={"success": True, "data": backend_service.get_training_status(), "error": None, "meta": None})


@router.get("/memory", response_model=ApiResponse)
async def strategy_memory() -> ApiResponse:
    return ApiResponse(success=True, data=backend_service.get_strategy_memory())

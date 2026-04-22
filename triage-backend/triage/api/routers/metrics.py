"""Metrics and charts routes."""

from __future__ import annotations

from fastapi import APIRouter

from triage.api.schemas import ApiResponse
from triage.api.service import backend_service


router = APIRouter()


@router.get("/reward-curve", response_model=ApiResponse)
async def reward_curve() -> ApiResponse:
    return ApiResponse(success=True, data=backend_service.get_reward_curve())


@router.get("/episode/{episode_id}", response_model=ApiResponse)
async def episode_metrics(episode_id: str) -> ApiResponse:
    return ApiResponse(success=True, data=backend_service.get_episode_metrics(episode_id))


@router.get("/comparison", response_model=ApiResponse)
async def comparison_metrics() -> ApiResponse:
    return ApiResponse(success=True, data=backend_service.get_comparison_metrics())


@router.get("/agents", response_model=ApiResponse)
async def agent_metrics() -> ApiResponse:
    return ApiResponse(success=True, data={"agents": backend_service.get_agent_metrics()})


@router.get("/resources", response_model=ApiResponse)
async def resource_metrics() -> ApiResponse:
    return ApiResponse(success=True, data=backend_service.get_resource_metrics())

"""Episode lifecycle routes."""

from __future__ import annotations

from fastapi import APIRouter

from triage.api.schemas import ApiResponse, EpisodeConfig, EpisodeRunRequest
from triage.api.service import backend_service


router = APIRouter()


@router.post("/start", response_model=ApiResponse)
async def start_episode(config: EpisodeConfig) -> ApiResponse:
    return ApiResponse(success=True, data=await backend_service.start_episode(config))


@router.post("/{episode_id}/step", response_model=ApiResponse)
async def step_episode(episode_id: str) -> ApiResponse:
    return ApiResponse(success=True, data=await backend_service.step_episode(episode_id))


@router.post("/{episode_id}/run", response_model=ApiResponse)
async def run_episode(episode_id: str, request: EpisodeRunRequest) -> ApiResponse:
    return ApiResponse(success=True, data=await backend_service.run_episode(episode_id, request))


@router.get("/{episode_id}/state", response_model=ApiResponse)
async def get_episode_state(episode_id: str) -> ApiResponse:
    session = backend_service.get_episode(episode_id)
    return ApiResponse(success=True, data=backend_service.build_state_payload(session))


@router.get("/{episode_id}/history", response_model=ApiResponse)
async def get_episode_history(episode_id: str) -> ApiResponse:
    session = backend_service.get_episode(episode_id)
    return ApiResponse(success=True, data=backend_service.episode_history_payload(session))


@router.post("/{episode_id}/reset", response_model=ApiResponse)
async def reset_episode(episode_id: str) -> ApiResponse:
    return ApiResponse(success=True, data=await backend_service.reset_episode(episode_id))


@router.get("/", response_model=ApiResponse)
async def list_episodes() -> ApiResponse:
    return ApiResponse(success=True, data={"episodes": backend_service.list_episodes()})

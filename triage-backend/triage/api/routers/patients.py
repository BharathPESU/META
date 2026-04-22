"""Patient data routes."""

from __future__ import annotations

from fastapi import APIRouter

from triage.api.schemas import ApiResponse
from triage.api.service import backend_service


router = APIRouter()


@router.get("/", response_model=ApiResponse)
async def list_patients() -> ApiResponse:
    return ApiResponse(success=True, data={"patients": backend_service.get_patients()})


@router.get("/critical", response_model=ApiResponse)
async def list_critical_patients() -> ApiResponse:
    return ApiResponse(success=True, data={"patients": backend_service.get_patients(critical_only=True)})


@router.get("/timeline", response_model=ApiResponse)
async def patient_timeline() -> ApiResponse:
    return ApiResponse(success=True, data={"timeline": backend_service.get_patient_timeline()})


@router.get("/{patient_id}", response_model=ApiResponse)
async def get_patient(patient_id: str) -> ApiResponse:
    return ApiResponse(success=True, data=backend_service.get_patient(patient_id))

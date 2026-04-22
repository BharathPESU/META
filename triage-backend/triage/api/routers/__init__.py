"""API router exports."""

from triage.api.routers.agents import router as agents_router
from triage.api.routers.episodes import router as episodes_router
from triage.api.routers.metrics import router as metrics_router
from triage.api.routers.patients import router as patients_router
from triage.api.routers.training import router as training_router
from triage.api.routers.websocket import router as websocket_router

__all__ = [
    "agents_router",
    "episodes_router",
    "metrics_router",
    "patients_router",
    "training_router",
    "websocket_router",
]

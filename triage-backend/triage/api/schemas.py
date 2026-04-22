"""Typed Pydantic schemas for TRIAGE API routes and WebSocket events."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────


class CrisisTypeSchema(str, Enum):
    MASS_CASUALTY = "mass_casualty"
    OUTBREAK = "outbreak"
    EQUIPMENT_FAILURE = "equipment_failure"
    STAFF_SHORTAGE = "staff_shortage"


class AgentTypeSchema(str, Enum):
    CMO_OVERSIGHT = "cmo_oversight"
    ER_TRIAGE = "er_triage"
    ICU_MANAGEMENT = "icu_management"
    PHARMACY = "pharmacy"
    HR_ROSTERING = "hr_rostering"
    IT_SYSTEMS = "it_systems"


class SimulationStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


# ── Patient and Metrics Schemas ───────────────────────────────────────────────


class PatientSnapshot(BaseModel):
    """Patient state at current step."""

    id: str
    name: str
    age: int
    condition: str
    status: str
    ward: str
    triage_score: int
    assigned_agent: str
    medications: list[str] = Field(default_factory=list)
    treatment_plan: list[str] = Field(default_factory=list)
    insurance_verified: bool = False
    icu_required: bool = False
    history: list[dict[str, Any]] = Field(default_factory=list)


class ResourceSnapshot(BaseModel):
    """Resource availability."""

    icu_beds_total: int
    icu_beds_used: int
    ventilators_total: int
    ventilators_used: int
    staff_ratio: float
    pharmacy_stock: float
    equipment_status: float
    it_uptime: float


class AgentSnapshot(BaseModel):
    """Agent state summary."""

    agent_type: str
    role: str
    actions_taken: int
    total_tokens: int
    last_action: str | None = None
    is_active: bool = True
    inbox_size: int = 0
    messages_sent: int = 0


class MetricsSnapshot(BaseModel):
    """Real-time metrics."""

    survival_rate: float
    deceased_count: int
    discharged_count: int
    critical_count: int
    alive_count: int
    icu_occupancy: float
    total_reward: float
    violations_caught: int
    violations_injected: int
    compliance_rate: float


class ActionSnapshot(BaseModel):
    """Action taken by an agent."""

    step: int
    agent: str
    action_type: str
    target: str
    reasoning: str
    reward: float
    timestamp: str


class DriftEventSnapshot(BaseModel):
    """Schema drift event."""

    step: int
    event_type: str
    description: str
    impact: str


class RewardCurvePoint(BaseModel):
    """Reward curve point."""

    episode: int | None = None
    step: int | None = None
    reward: float
    cumulative: float | None = None
    total_reward: float | None = None
    is_trained: bool | None = None


class ResourcePoint(BaseModel):
    """Resource utilization point."""

    step: int
    icu_occupancy: float
    staff_ratio: float
    pharmacy_stock: float
    equipment_status: float


class MetricsComparison(BaseModel):
    """Baseline vs trained comparison payload."""

    baseline_mean_reward: float = 0.0
    trained_mean_reward: float = 0.0
    reward_delta: float = 0.0
    baseline_mean_survival: float = 0.0
    trained_mean_survival: float = 0.0
    survival_delta: float = 0.0
    episode_counts: dict[str, int] = Field(default_factory=dict)


# ── Episode Schemas ───────────────────────────────────────────────────────────


class SimulationConfig(BaseModel):
    """Configuration for starting a new episode."""

    crisis_type: CrisisTypeSchema | None = None
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0)
    max_steps: int = Field(default=200, ge=10, le=1000)
    mock_llm: bool = True
    seed: int | None = None
    auto_step: bool = False
    step_delay_ms: int = Field(default=250, ge=0, le=10000)
    is_trained: bool = False


EpisodeConfig = SimulationConfig


class EpisodeRunRequest(BaseModel):
    """Payload for run/reset operations."""

    delay_ms: int = Field(default=0, ge=0, le=10000)
    max_steps: int | None = Field(default=None, ge=1, le=5000)


class SimulationState(BaseModel):
    """Current simulation state snapshot."""

    episode_id: str
    episode_num: int
    status: SimulationStatus
    step: int
    max_steps: int
    crisis_type: str
    difficulty: float
    patients: list[PatientSnapshot]
    resources: ResourceSnapshot
    agents: list[AgentSnapshot]
    metrics: MetricsSnapshot
    recent_actions: list[ActionSnapshot]
    drift_events: list[DriftEventSnapshot]


EpisodeState = SimulationState


class EpisodeHistory(BaseModel):
    """Episode history view."""

    episode_id: str
    steps: list[dict[str, Any]] = Field(default_factory=list)
    messages: list[dict[str, Any]] = Field(default_factory=list)


# ── Training Schemas ──────────────────────────────────────────────────────────

class TrainingConfig(BaseModel):
    """Configuration for DPO training pipeline."""

    n_episodes: int = Field(default=10, ge=1, le=100)
    crisis_types: list[CrisisTypeSchema] | None = None
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0)
    mock_llm: bool = True
    mock_training: bool = True
    model_preset: str = "4b_reliable"
    model_name: str = "unsloth/gemma-3-4b-it-unsloth-bnb-4bit"
    learning_rate: float = 5e-7
    num_epochs: int = 3
    output_dir: str = "./data/episodes"
    external_dataset_path: str | None = None
    real_data_fraction: float = Field(default=0.3, ge=0.0, le=1.0)


class LabelingConfig(BaseModel):
    """Preference labeling configuration."""

    min_delta: float = Field(default=20.0, ge=0.0)
    output_path: str = "./data/episodes/preference_pairs.json"


class TrainingStatus(BaseModel):
    """Training pipeline status."""
    phase: str  # "collecting", "training", "completed", "error"
    progress: float  # 0.0 - 1.0
    current_episode: int | None = None
    total_episodes: int | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class EpisodeSummary(BaseModel):
    """Summary of a completed episode."""

    episode_id: str
    crisis_type: str
    steps: int
    total_reward: float
    survival_rate: float
    deceased: int
    discharged: int
    duration_seconds: float


class CollectionSummary(BaseModel):
    """Summary across all collected episodes."""
    episodes: int
    mean_reward: float = 0.0
    std_reward: float = 0.0
    mean_survival: float = 0.0
    best_reward: float = 0.0
    worst_reward: float = 0.0


# ── WebSocket Schemas ─────────────────────────────────────────────────────────

class WSMessage(BaseModel):
    """WebSocket message wrapper."""

    type: str
    data: dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WSCommand(BaseModel):
    """Command from frontend via WebSocket."""

    command: str
    params: dict[str, Any] = Field(default_factory=dict)


# ── API Response Wrappers ─────────────────────────────────────────────────────

class ApiResponse(BaseModel):
    """Consistent API response shape."""

    success: bool
    data: Any = None
    error: str | None = None
    meta: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
    components: dict[str, str] = Field(default_factory=dict)


class AgentOverrideRequest(BaseModel):
    """Manual action override payload."""

    action_type: str
    target_id: int = 0
    priority: int = Field(default=5, ge=0, le=10)
    reasoning: str = "Manual override from API"
    reasoning_tokens: int = Field(default=25, ge=0, le=4000)


# Forward refs
SimulationState.model_rebuild()

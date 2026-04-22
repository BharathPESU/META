"""ICU capacity and allocation workflow simulator."""

from __future__ import annotations

from typing import Any

from triage.env.state import (
    AgentType,
    AppAuditEvent,
    EnvironmentState,
    Patient,
    PatientStatus,
    WardType,
)


class ICUManagerSystem:
    """ICU allocation workflow with capacity checks and override gates."""

    def __init__(self) -> None:
        self._capacity_checks: dict[tuple[str, str | None], int] = {}
        self._allocations: dict[str, str] = {}

    def query_capacity(
        self,
        state: EnvironmentState,
        requester: AgentType,
        patient_id: str | None = None,
    ) -> dict[str, Any]:
        self._capacity_checks[(requester.value, patient_id)] = state.step_count
        available = state.resources.icu_beds_total - state.resources.icu_beds_occupied
        queue = self._priority_queue(state)
        return self._audit(
            state,
            requester,
            "query_icu_capacity",
            patient_id,
            "approved",
            "ICU capacity queried",
            details={
                "available_beds": available,
                "occupied_beds": state.resources.icu_beds_occupied,
                "total_beds": state.resources.icu_beds_total,
                "priority_queue": queue[:5],
            },
        )

    def allocate_bed(
        self,
        patient_id: str,
        state: EnvironmentState,
        requester: AgentType,
        authorization_id: str | None = None,
    ) -> dict[str, Any]:
        patient = self._find_patient(patient_id, state)
        if patient is None:
            return self._audit(
                state,
                requester,
                "allocate_icu_bed",
                patient_id,
                "rejected_unknown_tool",
                f"Patient {patient_id} not found",
            )

        if requester != AgentType.ICU_MANAGEMENT:
            return self._audit(
                state,
                requester,
                "allocate_icu_bed",
                patient_id,
                "blocked",
                "Only ICU_MANAGEMENT can allocate ICU beds",
                details={"required_agent": AgentType.ICU_MANAGEMENT.value},
            )

        if not self._has_recent_capacity_check(requester, patient_id, state):
            return self._audit(
                state,
                requester,
                "allocate_icu_bed",
                patient_id,
                "missing_precheck",
                "Capacity query must precede ICU allocation",
                details={"required_precheck": "query_icu_capacity"},
            )

        queue = self._priority_queue(state)
        queue_index = next((idx for idx, entry in enumerate(queue) if entry["patient_id"] == patient_id), None)
        if queue_index is not None and queue_index > 0 and not state.validate_override_token(
            authorization_id,
            "icu_override",
            patient_id=patient_id,
            consume=True,
        ):
            return self._audit(
                state,
                requester,
                "allocate_icu_bed",
                patient_id,
                "blocked",
                "A higher-priority patient is ahead in the ICU queue",
                details={"queue_position": queue_index + 1, "queue": queue[:5]},
                authorization_id=authorization_id,
            )

        available = state.resources.icu_beds_total - state.resources.icu_beds_occupied
        if available <= 0:
            if not state.validate_override_token(
                authorization_id,
                "icu_override",
                patient_id=patient_id,
                consume=True,
            ):
                return self._audit(
                    state,
                    requester,
                    "allocate_icu_bed",
                    patient_id,
                    "needs_override",
                    "No ICU beds available; CMO override required",
                    details={"queue": queue[:5], "activate_overflow": True},
                    authorization_id=authorization_id,
                )
            state.resources.icu_beds_total += 1

        state.resources.icu_beds_occupied += 1
        bed_id = f"ICU-{state.resources.icu_beds_occupied:03d}"
        self._allocations[bed_id] = patient_id
        patient.ward = WardType.ICU
        patient.status = PatientStatus.CRITICAL if patient.status == PatientStatus.INCOMING else patient.status
        patient.icu_required = False
        patient.add_event("ICU_TRANSFER", f"Allocated ICU bed {bed_id}", requester)
        return self._audit(
            state,
            requester,
            "allocate_icu_bed",
            patient_id,
            "approved",
            f"Allocated ICU bed {bed_id}",
            details={"bed_id": bed_id, "remaining_beds": state.resources.icu_beds_total - state.resources.icu_beds_occupied},
            authorization_id=authorization_id,
        )

    def release_bed(
        self,
        bed_id: str,
        state: EnvironmentState,
        requester: AgentType,
    ) -> dict[str, Any]:
        patient_id = self._allocations.pop(bed_id, None)
        if patient_id is None:
            return self._audit(
                state,
                requester,
                "release_icu_bed",
                None,
                "blocked",
                f"ICU bed {bed_id} is not allocated",
            )
        state.resources.icu_beds_occupied = max(0, state.resources.icu_beds_occupied - 1)
        patient = self._find_patient(patient_id, state)
        if patient is not None:
            patient.ward = WardType.WARD_A
            patient.add_event("ICU_DISCHARGE", f"Released from {bed_id}", requester)
        return self._audit(
            state,
            requester,
            "release_icu_bed",
            patient_id,
            "approved",
            f"Released ICU bed {bed_id}",
            details={"bed_id": bed_id},
        )

    def _priority_queue(self, state: EnvironmentState) -> list[dict[str, Any]]:
        candidates: list[Patient] = [
            patient
            for patient in state.patients
            if patient.icu_required or patient.ward == WardType.ICU or patient.status == PatientStatus.CRITICAL
        ]
        ranked = sorted(
            candidates,
            key=lambda patient: (patient.triage_score, len(patient.treatment_plan) == 0, patient.status == PatientStatus.CRITICAL),
            reverse=True,
        )
        return [
            {
                "patient_id": patient.id,
                "name": patient.name,
                "triage_score": patient.triage_score,
                "status": patient.status.value,
            }
            for patient in ranked
        ]

    def _has_recent_capacity_check(
        self,
        requester: AgentType,
        patient_id: str,
        state: EnvironmentState,
    ) -> bool:
        check_step = self._capacity_checks.get((requester.value, patient_id))
        if check_step is None:
            check_step = self._capacity_checks.get((requester.value, None))
        return check_step is not None and check_step >= max(0, state.step_count - 1)

    def _find_patient(self, patient_id: str, state: EnvironmentState) -> Patient | None:
        for patient in state.patients:
            if patient.id == patient_id:
                return patient
        return None

    def _audit(
        self,
        state: EnvironmentState,
        requester: AgentType,
        tool_name: str,
        patient_id: str | None,
        status: str,
        message: str,
        details: dict[str, Any] | None = None,
        authorization_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "status": status,
            "message": message,
            "patient_id": patient_id,
            "details": details or {},
            "authorization_id": authorization_id,
        }
        state.add_app_audit(
            AppAuditEvent(
                app="icu_manager",
                tool_name=tool_name,
                requester=requester,
                patient_id=patient_id,
                status=status,
                message=message,
                details=details or {},
                authorization_id=authorization_id,
            )
        )
        return payload

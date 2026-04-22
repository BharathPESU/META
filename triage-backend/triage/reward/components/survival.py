"""Patient survival reward component."""

from __future__ import annotations

from triage.env.state import EnvironmentState, PatientStatus


class SurvivalReward:
    """Continuous reward for patient outcomes."""

    def compute(self, state: EnvironmentState) -> float:
        if state.total_patients == 0:
            return 0.0

        alive_ratio = state.alive_count / max(state.total_patients, 1)
        treatment_coverage = sum(
            1 for patient in state.patients
            if patient.status not in (PatientStatus.DECEASED, PatientStatus.DISCHARGED)
            and patient.treatment_plan
        ) / max(state.alive_count, 1)
        untreated_critical = sum(
            1 for patient in state.patients
            if patient.status == PatientStatus.CRITICAL and not patient.treatment_plan
        )
        deterioration_penalty = min(untreated_critical / max(state.total_patients, 1), 0.4)
        return max(
            -1.0,
            min(1.0, alive_ratio * 0.7 + treatment_coverage * 0.3 - deterioration_penalty),
        )

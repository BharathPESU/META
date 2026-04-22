"""Pharmacy workflow simulator with safety gates and audit trails."""

from __future__ import annotations

from typing import Any

from triage.env.state import AgentType, AppAuditEvent, EnvironmentState, Patient


class PharmacySystem:
    """Medication fulfillment workflow with mandatory safety checks."""

    _CONTROLLED_SUBSTANCES = {"morphine", "fentanyl", "ketamine", "midazolam", "propofol"}
    _ALLERGY_ALIASES = {
        "penicillin": {"antibiotics_broad", "amoxicillin"},
        "morphine": {"morphine"},
        "midazolam": {"midazolam"},
    }
    _CONDITION_CONFLICTS = {
        ("respiratory_failure", "midazolam"): "Sedation worsens respiratory compromise",
        ("respiratory_distress", "midazolam"): "Sedation requires override and monitoring",
        ("hemorrhage", "blood_thinners"): "Anticoagulants worsen active bleeding",
        ("blast_lung", "propofol"): "High sedation risk without airway support",
    }
    _INTERACTIONS = {
        tuple(sorted(("morphine", "midazolam"))): "Respiratory depression risk",
        tuple(sorted(("fentanyl", "midazolam"))): "Severe respiratory depression",
        tuple(sorted(("blood_thinners", "antibiotics_broad"))): "Dose adjustment required",
    }

    def __init__(self) -> None:
        self._dispensing_log: list[dict[str, Any]] = []
        self._prechecks: dict[tuple[str, str], dict[str, Any]] = {}

    def register_patient_lookup(
        self,
        patient_id: str,
        requester: AgentType,
        state: EnvironmentState,
    ) -> None:
        key = (requester.value, patient_id)
        entry = self._prechecks.setdefault(key, {})
        entry["lookup_step"] = state.step_count

    def check_inventory(self, state: EnvironmentState) -> dict[str, Any]:
        inventory = state.crisis.drug_inventory
        low_stock = {drug: qty for drug, qty in inventory.items() if qty < 10}
        result = {
            "status": "approved",
            "inventory": dict(inventory),
            "low_stock_alerts": low_stock,
            "total_items": sum(inventory.values()),
        }
        state.add_app_audit(
            AppAuditEvent(
                app="pharmacy",
                tool_name="check_inventory",
                requester=AgentType.PHARMACY,
                status="approved",
                message="Inventory inspected",
                details={"low_stock_count": len(low_stock)},
            )
        )
        return result

    def check_interactions(
        self,
        patient_id: str,
        medication: str,
        state: EnvironmentState,
        requester: AgentType = AgentType.PHARMACY,
    ) -> dict[str, Any]:
        patient = self._find_patient(patient_id, state)
        if patient is None:
            return self._audit(
                state,
                requester,
                "check_interactions",
                patient_id,
                "rejected_unknown_tool",
                f"Patient {patient_id} not found",
            )

        current_meds = [item.split(" (")[0] for item in patient.medications]
        interactions = self._interaction_hits(current_meds, medication)
        condition_conflicts = self._condition_hits(patient, medication)
        key = (requester.value, patient_id)
        self._prechecks.setdefault(key, {}).update(
            {
                "interaction_step": state.step_count,
                "checked_medication": medication,
                "last_interactions": interactions,
                "last_condition_conflicts": condition_conflicts,
            }
        )
        status = "approved" if not interactions and not condition_conflicts else "needs_override"
        return self._audit(
            state,
            requester,
            "check_interactions",
            patient_id,
            status,
            "Medication interactions evaluated",
            details={
                "medication": medication,
                "current_medications": current_meds,
                "interactions": interactions,
                "condition_conflicts": condition_conflicts,
            },
        )

    def dispense_medication(
        self,
        patient_id: str,
        medication: str,
        dose: str,
        state: EnvironmentState,
        requester: AgentType,
        double_verified: bool = False,
        emergency: bool = False,
        authorization_id: str | None = None,
    ) -> dict[str, Any]:
        patient = self._find_patient(patient_id, state)
        if patient is None:
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient_id,
                "rejected_unknown_tool",
                f"Patient {patient_id} not found",
            )

        if requester != AgentType.PHARMACY:
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient_id,
                "blocked",
                "Medication fulfillment must be cleared by PHARMACY",
                details={"required_agent": AgentType.PHARMACY.value},
            )

        inventory = state.crisis.drug_inventory
        if inventory.get(medication, 0) <= 0:
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient_id,
                "blocked",
                f"{medication} is out of stock",
                details={"suggested_alternative": self._suggest_alternative(medication)},
            )

        precheck_status = self._validate_prechecks(patient, medication, state, requester, emergency)
        if precheck_status is not None:
            return precheck_status

        if medication in self._CONTROLLED_SUBSTANCES and not double_verified:
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient_id,
                "blocked",
                "Controlled substance requires double verification",
                details={"policy": "POL-003", "medication": medication},
            )

        allergy_hits = self._allergy_hits(patient, medication)
        interaction_hits = self._prechecks[(requester.value, patient_id)].get("last_interactions", [])
        condition_conflicts = self._prechecks[(requester.value, patient_id)].get("last_condition_conflicts", [])
        high_risk = allergy_hits or interaction_hits or condition_conflicts
        if high_risk and not state.validate_override_token(
            authorization_id,
            "pharmacy_override",
            patient_id=patient_id,
            consume=True,
        ):
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient_id,
                "needs_override",
                "High-risk medication request requires CMO override",
                details={
                    "medication": medication,
                    "allergies": allergy_hits,
                    "interactions": interaction_hits,
                    "condition_conflicts": condition_conflicts,
                },
                authorization_id=authorization_id,
            )

        inventory[medication] -= 1
        patient.medications.append(f"{medication} ({dose})")
        patient.add_event("MEDICATION", f"Dispensed {medication} {dose}", requester)
        self._dispensing_log.append(
            {
                "patient_id": patient_id,
                "medication": medication,
                "dose": dose,
                "emergency": emergency,
                "authorization_id": authorization_id,
            }
        )
        return self._audit(
            state,
            requester,
            "dispense_medication",
            patient_id,
            "approved",
            f"Dispensed {medication} {dose}",
            details={
                "medication": medication,
                "dose": dose,
                "remaining_stock": inventory[medication],
                "double_verified": double_verified,
                "emergency": emergency,
            },
            authorization_id=authorization_id,
        )

    def _validate_prechecks(
        self,
        patient: Patient,
        medication: str,
        state: EnvironmentState,
        requester: AgentType,
        emergency: bool,
    ) -> dict[str, Any] | None:
        key = (requester.value, patient.id)
        entry = self._prechecks.get(key, {})
        if entry.get("lookup_step") is None:
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient.id,
                "missing_precheck",
                "Patient lookup is required before dispensing",
                details={"required_precheck": "lookup_patient"},
            )
        if entry.get("interaction_step") is None or entry.get("checked_medication") != medication:
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient.id,
                "missing_precheck",
                "Interaction check for the requested medication is required",
                details={"required_precheck": "check_interactions", "medication": medication},
            )
        if not emergency and not patient.insurance_verified:
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient.id,
                "blocked",
                "Non-emergency medication requires insurance verification",
                details={"required_precheck": "verify_insurance"},
            )
        if not emergency and patient.insurance_plan in {"HMO_BASIC", "UNINSURED", "EMERGENCY_ONLY"}:
            return self._audit(
                state,
                requester,
                "dispense_medication",
                patient.id,
                "blocked",
                "Plan does not cover standard pharmacy fulfillment",
                details={"insurance_plan": patient.insurance_plan},
            )
        return None

    def _find_patient(self, patient_id: str, state: EnvironmentState) -> Patient | None:
        for patient in state.patients:
            if patient.id == patient_id:
                return patient
        return None

    def _allergy_hits(self, patient: Patient, medication: str) -> list[str]:
        hits: list[str] = []
        for allergy in patient.allergies:
            aliases = self._ALLERGY_ALIASES.get(allergy.lower(), {allergy.lower()})
            if medication.lower() in aliases:
                hits.append(allergy)
        return hits

    def _interaction_hits(self, current: list[str], medication: str) -> list[dict[str, str]]:
        hits: list[dict[str, str]] = []
        for existing in current:
            pair = tuple(sorted((existing, medication)))
            risk = self._INTERACTIONS.get(pair)
            if risk:
                hits.append({"drugs": f"{existing} + {medication}", "risk": risk})
        return hits

    def _condition_hits(self, patient: Patient, medication: str) -> list[dict[str, str]]:
        hits: list[dict[str, str]] = []
        risk = self._CONDITION_CONFLICTS.get((patient.condition, medication))
        if risk:
            hits.append({"condition": patient.condition, "risk": risk})
        return hits

    def _suggest_alternative(self, medication: str) -> str | None:
        alternatives = {
            "morphine": "fentanyl",
            "fentanyl": "morphine",
            "propofol": "ketamine",
            "midazolam": "propofol",
        }
        return alternatives.get(medication)

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
                app="pharmacy",
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

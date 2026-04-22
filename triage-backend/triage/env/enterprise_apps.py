"""
Enterprise App Simulators — EHR, Pharmacy, Scheduling, Insurance, Equipment.

Each simulator provides tool-callable methods that return realistic data.
Agents call these via the tool definitions in config/agents.yaml.
The simulators maintain internal state that reflects the EnvironmentState.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

from triage.env.state import (
    AgentType,
    EnvironmentState,
    Patient,
    PatientStatus,
    WardType,
)


class EHRSystem:
    """Electronic Health Record simulator."""

    def __init__(self) -> None:
        self._access_log: list[dict[str, Any]] = []

    def lookup_patient(self, patient_id: str, state: EnvironmentState, requester: AgentType) -> dict[str, Any]:
        self._log_access(patient_id, requester, "lookup")
        patient = self._find_patient(patient_id, state)
        if not patient:
            return {"error": f"Patient {patient_id} not found in EHR"}
        return {
            "patient_id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "condition": patient.condition,
            "status": patient.status.value,
            "ward": patient.ward.value,
            "triage_score": patient.triage_score,
            "treatment_plan": patient.treatment_plan,
            "medications": patient.medications,
            "insurance_verified": patient.insurance_verified,
            "history_count": len(patient.history),
            "admitted_at": patient.admitted_at.isoformat(),
        }

    def update_record(
        self,
        patient_id: str,
        updates: dict[str, Any],
        state: EnvironmentState,
        requester: AgentType,
    ) -> dict[str, Any]:
        self._log_access(patient_id, requester, "update")
        patient = self._find_patient(patient_id, state)
        if not patient:
            return {"error": f"Patient {patient_id} not found"}

        applied: list[str] = []
        if "status" in updates:
            try:
                patient.status = PatientStatus(updates["status"])
                applied.append("status")
            except ValueError:
                pass
        if "ward" in updates:
            try:
                patient.ward = WardType(updates["ward"])
                applied.append("ward")
            except ValueError:
                pass
        if "triage_score" in updates:
            patient.triage_score = int(updates["triage_score"])
            applied.append("triage_score")
        if "treatment_plan" in updates:
            patient.treatment_plan = updates["treatment_plan"]
            applied.append("treatment_plan")
        if "medications" in updates:
            patient.medications = updates["medications"]
            applied.append("medications")
        if "insurance_verified" in updates:
            patient.insurance_verified = bool(updates["insurance_verified"])
            applied.append("insurance_verified")
        if "icu_required" in updates:
            patient.icu_required = bool(updates["icu_required"])
            applied.append("icu_required")

        patient.add_event("EHR_UPDATE", f"Fields updated: {', '.join(applied)}", requester)
        return {"success": True, "fields_updated": applied}

    def list_patients(self, state: EnvironmentState, ward: str | None = None) -> list[dict[str, Any]]:
        patients = state.patients
        if ward:
            patients = [p for p in patients if p.ward.value == ward]
        return [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status.value,
                "ward": p.ward.value,
                "triage_score": p.triage_score,
                "condition": p.condition,
            }
            for p in patients
        ]

    def get_access_log(self) -> list[dict[str, Any]]:
        return list(self._access_log)

    def _find_patient(self, patient_id: str, state: EnvironmentState) -> Patient | None:
        for p in state.patients:
            if p.id == patient_id:
                return p
        return None

    def _log_access(self, patient_id: str, requester: AgentType, action: str) -> None:
        self._access_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patient_id": patient_id,
            "requester": requester.value,
            "action": action,
        })


class PharmacySystem:
    """Pharmacy inventory and dispensing simulator."""

    def __init__(self) -> None:
        self._dispensing_log: list[dict[str, Any]] = []

    def check_inventory(self, state: EnvironmentState) -> dict[str, Any]:
        inventory = state.crisis.drug_inventory
        low_stock = {k: v for k, v in inventory.items() if v < 10}
        return {
            "inventory": dict(inventory),
            "low_stock_alerts": low_stock,
            "total_items": sum(inventory.values()),
        }

    def dispense_medication(
        self,
        patient_id: str,
        medication: str,
        dose: str,
        state: EnvironmentState,
        requester: AgentType,
        double_verified: bool = False,
    ) -> dict[str, Any]:
        inventory = state.crisis.drug_inventory

        # Check stock
        if medication not in inventory or inventory[medication] <= 0:
            return {
                "success": False,
                "error": f"{medication} is out of stock",
                "suggestion": self._suggest_alternative(medication),
            }

        # Check controlled substance verification
        controlled = {"morphine", "fentanyl", "ketamine", "midazolam", "propofol"}
        if medication in controlled and not double_verified:
            return {
                "success": False,
                "error": "Controlled substance requires double-verification (POL-003)",
                "violation_risk": True,
            }

        # Dispense
        inventory[medication] -= 1

        # Find patient and add medication
        for p in state.patients:
            if p.id == patient_id:
                p.medications.append(f"{medication} ({dose})")
                p.add_event(
                    "MEDICATION",
                    f"Dispensed {medication} {dose}",
                    requester,
                )
                break

        self._dispensing_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patient_id": patient_id,
            "medication": medication,
            "dose": dose,
            "requester": requester.value,
            "double_verified": double_verified,
        })

        return {
            "success": True,
            "medication": medication,
            "dose": dose,
            "remaining_stock": inventory[medication],
        }

    def check_interactions(
        self,
        patient_id: str,
        new_medication: str,
        state: EnvironmentState,
    ) -> dict[str, Any]:
        for p in state.patients:
            if p.id == patient_id:
                current_meds = [m.split(" (")[0] for m in p.medications]
                interactions = self._check_interaction_db(current_meds, new_medication)
                return {
                    "patient_id": patient_id,
                    "new_medication": new_medication,
                    "current_medications": current_meds,
                    "interactions": interactions,
                    "safe_to_administer": len(interactions) == 0,
                }
        return {"error": f"Patient {patient_id} not found"}

    def _suggest_alternative(self, medication: str) -> str | None:
        alternatives = {
            "morphine": "fentanyl",
            "fentanyl": "morphine",
            "propofol": "midazolam",
            "midazolam": "propofol",
        }
        return alternatives.get(medication)

    def _check_interaction_db(self, current: list[str], new: str) -> list[dict[str, str]]:
        _known_interactions = {
            ("morphine", "midazolam"): "Respiratory depression risk — requires monitoring",
            ("fentanyl", "midazolam"): "Severe respiratory depression — avoid combination",
            ("blood_thinners", "antibiotics_broad"): "Increased bleeding risk — adjust dose",
        }
        interactions = []
        for med in current:
            pair = tuple(sorted([med, new]))
            if pair in _known_interactions:
                interactions.append({
                    "drugs": f"{med} + {new}",
                    "risk": _known_interactions[pair],
                })
        return interactions


class SchedulingSystem:
    """Staff scheduling and fatigue tracking."""

    def __init__(self) -> None:
        self._shift_log: dict[str, dict[str, Any]] = {}
        self._fatigue_alerts: list[dict[str, Any]] = []

    def get_roster(self, state: EnvironmentState) -> dict[str, Any]:
        roster = state.crisis.staff_roster
        return {
            "roster": dict(roster),
            "total_staff": sum(roster.values()),
            "staff_reduction": state.crisis.staff_reduction,
            "fatigue_alerts": list(self._fatigue_alerts),
        }

    def check_staff_fatigue(
        self,
        staff_role: str,
        hours_worked: float,
    ) -> dict[str, Any]:
        is_fatigued = hours_worked > 16
        needs_break = hours_worked > 6

        result = {
            "staff_role": staff_role,
            "hours_worked": hours_worked,
            "is_fatigued": is_fatigued,
            "needs_break": needs_break,
            "recommendation": "",
        }

        if is_fatigued:
            result["recommendation"] = "CRITICAL: Staff member must be relieved immediately (POL-004)"
            self._fatigue_alerts.append({
                "role": staff_role,
                "hours": hours_worked,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        elif needs_break:
            result["recommendation"] = "Schedule 30-minute break at next opportunity"

        return result

    def request_additional_staff(
        self,
        role: str,
        count: int,
        state: EnvironmentState,
    ) -> dict[str, Any]:
        roster = state.crisis.staff_roster
        current = roster.get(role, 0)
        # Simulate callback response (partial fulfillment)
        available = random.randint(0, count)
        roster[role] = current + available

        return {
            "role": role,
            "requested": count,
            "fulfilled": available,
            "new_total": roster[role],
            "note": "Full callback typically takes 45-90 minutes" if available < count else "Request fulfilled",
        }


class InsuranceVerifier:
    """Insurance verification simulator."""

    _PLAN_DB = {
        "PPO_GOLD": {"coverage": 0.90, "icu_covered": True, "pharmacy_covered": True},
        "HMO_BASIC": {"coverage": 0.70, "icu_covered": True, "pharmacy_covered": False},
        "MEDICAID": {"coverage": 0.95, "icu_covered": True, "pharmacy_covered": True},
        "UNINSURED": {"coverage": 0.00, "icu_covered": False, "pharmacy_covered": False},
        "EMERGENCY_ONLY": {"coverage": 0.50, "icu_covered": True, "pharmacy_covered": False},
    }

    def verify_patient(
        self,
        patient_id: str,
        state: EnvironmentState,
    ) -> dict[str, Any]:
        for p in state.patients:
            if p.id == patient_id:
                plan_name = random.choice(list(self._PLAN_DB.keys()))
                plan = self._PLAN_DB[plan_name]
                p.insurance_verified = True
                p.add_event("INSURANCE", f"Verified: {plan_name}")
                return {
                    "patient_id": patient_id,
                    "verified": True,
                    "plan": plan_name,
                    "coverage_percent": plan["coverage"],
                    "icu_covered": plan["icu_covered"],
                    "pharmacy_covered": plan["pharmacy_covered"],
                    "authorization_number": str(uuid.uuid4())[:12].upper(),
                }
        return {"error": f"Patient {patient_id} not found"}

    def check_authorization(
        self,
        patient_id: str,
        procedure: str,
    ) -> dict[str, Any]:
        # In a crisis, emergency procedures are pre-authorized
        return {
            "patient_id": patient_id,
            "procedure": procedure,
            "pre_authorized": True,
            "reason": "Emergency protocol — pre-authorization waived",
        }


class EquipmentTracker:
    """Medical equipment status and allocation."""

    def __init__(self) -> None:
        self._allocations: dict[str, str] = {}  # equipment_id -> patient_id

    def get_status(self, state: EnvironmentState) -> dict[str, Any]:
        return {
            "ventilators": {
                "total": state.resources.ventilators_total,
                "in_use": state.resources.ventilators_in_use,
                "available": state.resources.ventilators_total - state.resources.ventilators_in_use,
            },
            "icu_beds": {
                "total": state.resources.icu_beds_total,
                "occupied": state.resources.icu_beds_occupied,
                "available": state.resources.icu_beds_total - state.resources.icu_beds_occupied,
            },
            "equipment_status": state.resources.equipment_status,
            "it_uptime": state.resources.it_uptime,
            "allocations": dict(self._allocations),
        }

    def allocate_ventilator(
        self,
        patient_id: str,
        state: EnvironmentState,
    ) -> dict[str, Any]:
        available = state.resources.ventilators_total - state.resources.ventilators_in_use
        if available <= 0:
            return {
                "success": False,
                "error": "No ventilators available",
                "suggestion": "Consider non-invasive ventilation or patient transfer",
            }
        state.resources.ventilators_in_use += 1
        equip_id = f"VENT-{state.resources.ventilators_in_use:03d}"
        self._allocations[equip_id] = patient_id
        return {
            "success": True,
            "equipment_id": equip_id,
            "patient_id": patient_id,
            "remaining_ventilators": available - 1,
        }

    def allocate_icu_bed(
        self,
        patient_id: str,
        state: EnvironmentState,
    ) -> dict[str, Any]:
        available = state.resources.icu_beds_total - state.resources.icu_beds_occupied
        if available <= 0:
            occupancy = state.resources.icu_beds_occupied / max(state.resources.icu_beds_total, 1)
            return {
                "success": False,
                "error": "No ICU beds available",
                "occupancy": occupancy,
                "suggestion": "Activate overflow protocol" if occupancy >= 0.9 else "Transfer to step-down unit",
            }
        state.resources.icu_beds_occupied += 1
        bed_id = f"ICU-{state.resources.icu_beds_occupied:03d}"
        self._allocations[bed_id] = patient_id

        # Move patient to ICU ward
        for p in state.patients:
            if p.id == patient_id:
                p.ward = WardType.ICU
                p.add_event("TRANSFER", f"Admitted to ICU bed {bed_id}")
                break

        return {
            "success": True,
            "bed_id": bed_id,
            "patient_id": patient_id,
            "remaining_beds": available - 1,
        }

    def release_equipment(
        self,
        equipment_id: str,
        state: EnvironmentState,
    ) -> dict[str, Any]:
        if equipment_id not in self._allocations:
            return {"error": f"Equipment {equipment_id} not found in allocations"}

        patient_id = self._allocations.pop(equipment_id)
        if equipment_id.startswith("VENT"):
            state.resources.ventilators_in_use = max(0, state.resources.ventilators_in_use - 1)
        elif equipment_id.startswith("ICU"):
            state.resources.icu_beds_occupied = max(0, state.resources.icu_beds_occupied - 1)

        return {
            "success": True,
            "equipment_id": equipment_id,
            "released_from_patient": patient_id,
        }


# ─── App Registry ────────────────────────────────────────────

class EnterpriseAppRegistry:
    """Central registry for all enterprise app simulators."""

    def __init__(self) -> None:
        self.ehr = EHRSystem()
        self.pharmacy = PharmacySystem()
        self.scheduling = SchedulingSystem()
        self.insurance = InsuranceVerifier()
        self.equipment = EquipmentTracker()

    def reset(self) -> None:
        self.ehr = EHRSystem()
        self.pharmacy = PharmacySystem()
        self.scheduling = SchedulingSystem()
        self.insurance = InsuranceVerifier()
        self.equipment = EquipmentTracker()

    def execute_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
        state: EnvironmentState,
        requester: AgentType,
    ) -> dict[str, Any]:
        """Route a tool call to the appropriate enterprise app."""
        tool_map: dict[str, Any] = {
            "lookup_patient": lambda: self.ehr.lookup_patient(
                params["patient_id"], state, requester
            ),
            "update_record": lambda: self.ehr.update_record(
                params["patient_id"], params.get("updates", {}), state, requester
            ),
            "list_patients": lambda: self.ehr.list_patients(
                state, params.get("ward")
            ),
            "check_inventory": lambda: self.pharmacy.check_inventory(state),
            "dispense_medication": lambda: self.pharmacy.dispense_medication(
                params["patient_id"],
                params["medication"],
                params.get("dose", "standard"),
                state,
                requester,
                params.get("double_verified", False),
            ),
            "check_interactions": lambda: self.pharmacy.check_interactions(
                params["patient_id"], params["medication"], state
            ),
            "get_roster": lambda: self.scheduling.get_roster(state),
            "check_staff_fatigue": lambda: self.scheduling.check_staff_fatigue(
                params["role"], params.get("hours_worked", 0)
            ),
            "request_staff": lambda: self.scheduling.request_additional_staff(
                params["role"], params.get("count", 1), state
            ),
            "verify_insurance": lambda: self.insurance.verify_patient(
                params["patient_id"], state
            ),
            "check_authorization": lambda: self.insurance.check_authorization(
                params["patient_id"], params.get("procedure", "emergency")
            ),
            "get_equipment_status": lambda: self.equipment.get_status(state),
            "allocate_ventilator": lambda: self.equipment.allocate_ventilator(
                params["patient_id"], state
            ),
            "allocate_icu_bed": lambda: self.equipment.allocate_icu_bed(
                params["patient_id"], state
            ),
            "release_equipment": lambda: self.equipment.release_equipment(
                params["equipment_id"], state
            ),
        }

        handler = tool_map.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}", "available_tools": list(tool_map.keys())}

        try:
            return handler()
        except Exception as e:
            return {"error": f"Tool execution failed: {e!s}", "tool": tool_name}

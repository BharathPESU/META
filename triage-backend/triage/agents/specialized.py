"""
Specialized Hospital Agents — all 6 agents with rule-based fallbacks.

Agent Hierarchy:
  CMO_OVERSIGHT (supervisor) → oversees all agents, handles escalations
  ER_TRIAGE → patient triage and initial assessment
  ICU_MANAGEMENT → ICU bed allocation, ventilator management
  PHARMACY → medication dispensing, interaction checks
  HR_ROSTERING → staff scheduling, fatigue monitoring
  IT_SYSTEMS → EHR integrity, policy compliance, system monitoring
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from triage.agents.base_agent import BaseAgent
from triage.agents.message_bus import MessageBus
from triage.env.state import (
    ActionType,
    AgentAction,
    AgentMessage,
    AgentType,
    EnvironmentState,
    MessageType,
    PatientStatus,
)

logger = logging.getLogger(__name__)


# ─── CMO Oversight Agent ────────────────────────────────────

class CMOOversightAgent(BaseAgent):
    """Chief Medical Officer — supervisor agent.

    Responsibilities:
    - Monitor all agent activities
    - Handle escalations from other agents
    - Override decisions when necessary
    - Activate emergency protocols
    - Ensure policy compliance across the board
    """

    def __init__(self, config: dict[str, Any], bus: MessageBus, mock_llm: bool = True) -> None:
        super().__init__(AgentType.CMO_OVERSIGHT, config, bus, mock_llm)

    async def decide(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        context = self._build_state_context(state)
        prompt = self._build_cmo_prompt(state, inbox)
        response = await self._call_llm(prompt, context)
        return self._parse_actions(response, state)

    def _rule_based_decision(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        actions: list[AgentAction] = []

        # Handle escalations first
        for msg in inbox:
            if msg.msg_type == MessageType.ALERT and msg.priority >= 5:
                if msg.patient_id:
                    scope = msg.payload.get("scope", "") if msg.payload else ""
                    reason = f"CMO override based on escalation: {msg.content[:100]}"
                    if scope:
                        reason = f"{reason} | scope={scope}"
                    actions.append(AgentAction(
                        agent_type=self.agent_type,
                        action_type=ActionType.OVERRIDE_DECISION,
                        target_id=self._patient_idx(msg.patient_id, state),
                        priority=msg.priority,
                        reasoning=reason,
                    ))

        # Activate overflow if ICU is near capacity
        if state.icu_occupancy > 0.9 and not any(
            a.action_type == ActionType.ACTIVATE_OVERFLOW for a in state.action_history[-10:]
        ):
            actions.append(AgentAction(
                agent_type=self.agent_type,
                action_type=ActionType.ACTIVATE_OVERFLOW,
                priority=8,
                reasoning="ICU occupancy >90% — activating overflow protocol",
            ))

        # Check for untreated critical patients
        for i, p in enumerate(state.patients):
            if p.status == PatientStatus.CRITICAL and not p.treatment_plan and len(p.history) > 3:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType.ASSIGN_TREATMENT,
                    target_id=i,
                    priority=9,
                    reasoning=f"CMO emergency intervention — untreated critical patient {p.name}",
                ))
                break  # one at a time

        return actions

    def _build_cmo_prompt(self, state: EnvironmentState, inbox: list[AgentMessage]) -> str:
        escalations = [m for m in inbox if m.msg_type == MessageType.ALERT]
        return f"""
You are the CMO overseeing the hospital crisis response.

Escalations received: {len(escalations)}
{chr(10).join(f'- From {m.from_agent}: {m.content}' for m in escalations[:5])}

Critical patients without treatment: {sum(1 for p in state.patients if p.status == PatientStatus.CRITICAL and not p.treatment_plan)}
ICU occupancy: {state.icu_occupancy:.1%}

Decide what actions to take. Prioritize life-saving interventions.
"""

    def _parse_actions(self, response: dict[str, Any], state: EnvironmentState) -> list[AgentAction]:
        actions = []
        for a in response.get("actions", []):
            try:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType[a.get("action_type", "ESCALATE_TO_CMO")],
                    target_id=int(a.get("target_id", 0)),
                    priority=int(a.get("priority", 5)),
                    reasoning=a.get("reasoning", ""),
                ))
            except (KeyError, ValueError):
                continue
        return actions

    def _patient_idx(self, patient_id: str, state: EnvironmentState) -> int:
        for i, p in enumerate(state.patients):
            if p.id == patient_id:
                return i
        return 0


# ─── ER Triage Agent ────────────────────────────────────────

class ERTriageAgent(BaseAgent):
    """Emergency Room triage specialist.

    Responsibilities:
    - Assess incoming patients
    - Assign triage scores (1-10)
    - Route patients to appropriate wards
    - Escalate critical cases to ICU or CMO
    """

    def __init__(self, config: dict[str, Any], bus: MessageBus, mock_llm: bool = True) -> None:
        super().__init__(AgentType.ER_TRIAGE, config, bus, mock_llm)

    async def decide(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        context = self._build_state_context(state)
        prompt = "Triage incoming patients. Assign scores and route to appropriate care."
        response = await self._call_llm(prompt, context)
        return self._parse_actions(response, state)

    def _rule_based_decision(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        actions: list[AgentAction] = []

        for i, p in enumerate(state.patients):
            # Triage new incoming patients
            if p.status == PatientStatus.INCOMING:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType.TRIAGE_PATIENT,
                    target_id=i,
                    priority=p.triage_score,
                    reasoning=f"Triaging incoming patient {p.name} — condition: {p.condition}",
                ))
                # Route critical to ICU
                if p.triage_score >= 8:
                    actions.append(AgentAction(
                        agent_type=self.agent_type,
                        action_type=ActionType.TRANSFER_TO_ICU,
                        target_id=i,
                        priority=9,
                        reasoning=f"Critical patient {p.name} (score {p.triage_score}) requires ICU",
                    ))

            # Escalate deteriorating patients
            elif p.status == PatientStatus.CRITICAL and not p.treatment_plan:
                try:
                    asyncio.ensure_future(self.escalate(
                        f"Critical patient {p.name} [{p.id}] has no treatment plan",
                        p.id,
                        priority=8,
                    ))
                except RuntimeError:
                    pass  # No running loop — skip async escalation

        return actions[:5]  # limit actions per step

    def _parse_actions(self, response: dict[str, Any], state: EnvironmentState) -> list[AgentAction]:
        actions = []
        for a in response.get("actions", []):
            try:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType[a.get("action_type", "TRIAGE_PATIENT")],
                    target_id=int(a.get("target_id", 0)),
                    priority=int(a.get("priority", 5)),
                    reasoning=a.get("reasoning", ""),
                ))
            except (KeyError, ValueError):
                continue
        return actions


# ─── ICU Management Agent ───────────────────────────────────

class ICUManagementAgent(BaseAgent):
    """ICU bed and ventilator management specialist.

    Responsibilities:
    - Manage ICU bed allocation
    - Ventilator assignment and monitoring
    - Discharge planning for stable ICU patients
    - Overflow protocol management
    """

    def __init__(self, config: dict[str, Any], bus: MessageBus, mock_llm: bool = True) -> None:
        super().__init__(AgentType.ICU_MANAGEMENT, config, bus, mock_llm)

    async def decide(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        context = self._build_state_context(state)
        prompt = "Manage ICU resources. Allocate beds, ventilators, and plan discharges."
        response = await self._call_llm(prompt, context)
        return self._parse_actions(response, state)

    def _rule_based_decision(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        actions: list[AgentAction] = []

        for msg in inbox:
            if msg.request_type == "icu_bed_request" and msg.patient_id:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType.TRANSFER_TO_ICU,
                    target_id=self._patient_idx(msg.patient_id, state),
                    priority=max(msg.priority, 8),
                    reasoning=f"ICU_MANAGER accepted delegated bed request: {msg.content[:100]}",
                ))

        # Assign treatment to critical patients in ICU
        for i, p in enumerate(state.patients):
            if p.ward.value == "ICU" and p.status == PatientStatus.CRITICAL and not p.treatment_plan:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType.ASSIGN_TREATMENT,
                    target_id=i,
                    priority=8,
                    reasoning=f"Assigning ICU treatment plan for {p.name}",
                ))

            # Discharge stable ICU patients to free beds
            elif p.ward.value == "ICU" and p.status == PatientStatus.STABLE:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType.TRANSFER_TO_WARD,
                    target_id=i,
                    priority=3,
                    reasoning=f"Transferring stable patient {p.name} out of ICU",
                ))

        # Request specialist if many critical patients
        critical_icu = sum(
            1 for p in state.patients
            if p.ward.value == "ICU" and p.status == PatientStatus.CRITICAL
        )
        if critical_icu > 5:
            actions.append(AgentAction(
                agent_type=self.agent_type,
                action_type=ActionType.REQUEST_SPECIALIST,
                priority=7,
                reasoning=f"High ICU critical load ({critical_icu}) — requesting specialist backup",
            ))

        return actions[:4]

    def _parse_actions(self, response: dict[str, Any], state: EnvironmentState) -> list[AgentAction]:
        actions = []
        for a in response.get("actions", []):
            try:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType[a.get("action_type", "ASSIGN_TREATMENT")],
                    target_id=int(a.get("target_id", 0)),
                    priority=int(a.get("priority", 5)),
                    reasoning=a.get("reasoning", ""),
                ))
            except (KeyError, ValueError):
                continue
        return actions

    def _patient_idx(self, patient_id: str, state: EnvironmentState) -> int:
        for i, p in enumerate(state.patients):
            if p.id == patient_id:
                return i
        return 0


# ─── Pharmacy Agent ─────────────────────────────────────────

class PharmacyAgent(BaseAgent):
    """Pharmacy operations and medication safety.

    Responsibilities:
    - Process medication orders
    - Check drug interactions
    - Monitor inventory levels
    - Enforce double-verification for controlled substances
    """

    def __init__(self, config: dict[str, Any], bus: MessageBus, mock_llm: bool = True) -> None:
        super().__init__(AgentType.PHARMACY, config, bus, mock_llm)

    async def decide(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        context = self._build_state_context(state)
        prompt = "Manage pharmacy operations. Process orders, check interactions, monitor stock."
        response = await self._call_llm(prompt, context)
        return self._parse_actions(response, state)

    def _rule_based_decision(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        actions: list[AgentAction] = []

        for msg in inbox:
            if msg.request_type == "medication_request" and msg.patient_id:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType.ORDER_MEDICATION,
                    target_id=self._patient_idx(msg.patient_id, state),
                    priority=max(msg.priority, 7),
                    reasoning=f"PHARMACY accepted delegated medication request: {msg.content[:100]}",
                ))

        # Order medications for patients with treatment plans but no meds
        for i, p in enumerate(state.patients):
            if p.treatment_plan and not p.medications and p.status != PatientStatus.DECEASED:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType.ORDER_MEDICATION,
                    target_id=i,
                    priority=6,
                    reasoning=f"Filling medication order for {p.name} — treatment: {p.treatment_plan[0] if p.treatment_plan else 'generic'}",
                ))

        # Check for low stock items and alert
        low_stock = {k: v for k, v in state.crisis.drug_inventory.items() if v < 5}
        if low_stock:
            for drug, qty in list(low_stock.items())[:2]:
                try:
                    asyncio.ensure_future(self.broadcast(
                        f"⚠️ LOW STOCK ALERT: {drug} — only {qty} units remaining",
                        MessageType.ALERT,
                        priority=6,
                    ))
                except RuntimeError:
                    pass  # No running loop

        return actions[:3]

    def _parse_actions(self, response: dict[str, Any], state: EnvironmentState) -> list[AgentAction]:
        actions = []
        for a in response.get("actions", []):
            try:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType[a.get("action_type", "ORDER_MEDICATION")],
                    target_id=int(a.get("target_id", 0)),
                    priority=int(a.get("priority", 5)),
                    reasoning=a.get("reasoning", ""),
                ))
            except (KeyError, ValueError):
                continue
        return actions

    def _patient_idx(self, patient_id: str, state: EnvironmentState) -> int:
        for i, p in enumerate(state.patients):
            if p.id == patient_id:
                return i
        return 0


# ─── HR Rostering Agent ─────────────────────────────────────

class HRRosteringAgent(BaseAgent):
    """Human resources and staff scheduling.

    Responsibilities:
    - Monitor staff fatigue levels
    - Manage shift rotations
    - Request additional staff during surges
    - Enforce work-hour limits
    """

    def __init__(self, config: dict[str, Any], bus: MessageBus, mock_llm: bool = True) -> None:
        super().__init__(AgentType.HR_ROSTERING, config, bus, mock_llm)

    async def decide(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        context = self._build_state_context(state)
        prompt = "Manage staff scheduling. Monitor fatigue, request reinforcements if needed."
        response = await self._call_llm(prompt, context)
        return self._parse_actions(response, state)

    def _rule_based_decision(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        actions: list[AgentAction] = []

        # Request staff if ratio is low
        if state.resources.staff_ratio < 0.6:
            actions.append(AgentAction(
                agent_type=self.agent_type,
                action_type=ActionType.REQUEST_STAFF,
                priority=7,
                reasoning=f"Staff ratio critically low ({state.resources.staff_ratio:.0%}) — requesting emergency callback",
            ))
            try:
                asyncio.ensure_future(self.escalate(
                    f"Staff ratio at {state.resources.staff_ratio:.0%} — requesting CMO authorization for extended shifts",
                    priority=7,
                ))
            except RuntimeError:
                pass

        # Flag potential fatigue violations (simulated check every 15 steps)
        if state.step_count % 15 == 0 and state.step_count > 0:
            # Simulate detecting a fatigued staff member
            actions.append(AgentAction(
                agent_type=self.agent_type,
                action_type=ActionType.FLAG_POLICY_VIOLATION,
                priority=5,
                reasoning="Periodic fatigue check — flagging potential POL-004 violation",
            ))

        return actions[:2]

    def _parse_actions(self, response: dict[str, Any], state: EnvironmentState) -> list[AgentAction]:
        actions = []
        for a in response.get("actions", []):
            try:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType[a.get("action_type", "REQUEST_STAFF")],
                    target_id=int(a.get("target_id", 0)),
                    priority=int(a.get("priority", 5)),
                    reasoning=a.get("reasoning", ""),
                ))
            except (KeyError, ValueError):
                continue
        return actions


# ─── IT Systems Agent ───────────────────────────────────────

class ITSystemsAgent(BaseAgent):
    """IT infrastructure and compliance monitoring.

    Responsibilities:
    - Monitor EHR system integrity
    - Detect policy violations from access logs
    - Manage IT uptime and backups
    - Enforce data privacy (HIPAA) compliance
    - Respond to schema drift / policy changes
    """

    def __init__(self, config: dict[str, Any], bus: MessageBus, mock_llm: bool = True) -> None:
        super().__init__(AgentType.IT_SYSTEMS, config, bus, mock_llm)

    async def decide(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        context = self._build_state_context(state)
        prompt = "Monitor IT systems. Check for policy violations, EHR access anomalies, and system health."
        response = await self._call_llm(prompt, context)
        return self._parse_actions(response, state)

    def _rule_based_decision(self, state: EnvironmentState, inbox: list[AgentMessage]) -> list[AgentAction]:
        actions: list[AgentAction] = []

        # Monitor IT uptime
        if state.resources.it_uptime < 0.8:
            try:
                asyncio.ensure_future(self.broadcast(
                    f"🔴 IT ALERT: System uptime at {state.resources.it_uptime:.0%} — degraded performance expected",
                    MessageType.ALERT,
                    priority=7,
                ))
            except RuntimeError:
                pass

        # Detect injected violations
        if state.violations_injected > state.violations_caught:
            actions.append(AgentAction(
                agent_type=self.agent_type,
                action_type=ActionType.FLAG_POLICY_VIOLATION,
                priority=6,
                reasoning="Compliance scan detected policy violation in system logs",
            ))

        # Update EHR for patients with missing records
        for i, p in enumerate(state.patients):
            if not p.insurance_verified and p.status not in (PatientStatus.DECEASED, PatientStatus.DISCHARGED):
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType.VERIFY_INSURANCE,
                    target_id=i,
                    priority=3,
                    reasoning=f"Insurance verification pending for {p.name}",
                ))
                break  # one at a time

        # Respond to policy change messages
        for msg in inbox:
            if "POLICY" in msg.content.upper():
                try:
                    asyncio.ensure_future(self.broadcast(
                        f"📋 IT acknowledges policy change: {msg.content[:100]}",
                        MessageType.RESPONSE,
                        priority=4,
                    ))
                except RuntimeError:
                    pass

        return actions[:3]

    def _parse_actions(self, response: dict[str, Any], state: EnvironmentState) -> list[AgentAction]:
        actions = []
        for a in response.get("actions", []):
            try:
                actions.append(AgentAction(
                    agent_type=self.agent_type,
                    action_type=ActionType[a.get("action_type", "UPDATE_EHR")],
                    target_id=int(a.get("target_id", 0)),
                    priority=int(a.get("priority", 5)),
                    reasoning=a.get("reasoning", ""),
                ))
            except (KeyError, ValueError):
                continue
        return actions


# ─── Agent Factory ───────────────────────────────────────────

AGENT_CLASSES: dict[AgentType, type[BaseAgent]] = {
    AgentType.CMO_OVERSIGHT: CMOOversightAgent,
    AgentType.ER_TRIAGE: ERTriageAgent,
    AgentType.ICU_MANAGEMENT: ICUManagementAgent,
    AgentType.PHARMACY: PharmacyAgent,
    AgentType.HR_ROSTERING: HRRosteringAgent,
    AgentType.IT_SYSTEMS: ITSystemsAgent,
}


def create_agent(
    agent_type: AgentType,
    config: dict[str, Any],
    bus: MessageBus,
    mock_llm: bool = True,
) -> BaseAgent:
    """Factory function to create typed agents."""
    cls = AGENT_CLASSES.get(agent_type)
    if cls is None:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return cls(config=config, bus=bus, mock_llm=mock_llm)


def create_all_agents(
    configs: dict[str, Any],
    bus: MessageBus,
    mock_llm: bool = True,
) -> dict[AgentType, BaseAgent]:
    """Create all 6 agents from the agents.yaml config."""
    agents = {}
    for agent_type in AgentType:
        agent_config = configs.get("agents", {}).get(agent_type.value, {})
        agents[agent_type] = create_agent(agent_type, agent_config, bus, mock_llm)
        logger.info("Created agent: %s (mock_llm=%s)", agent_type.value, mock_llm)
    return agents

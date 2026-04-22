from __future__ import annotations

import json

import pytest


@pytest.mark.asyncio
async def test_pharmacy_requires_prechecks_and_override() -> None:
    from triage.env.hospital_env import HospitalEnv
    from triage.env.state import AgentType

    env = HospitalEnv(seed=12, max_steps=20)
    await env.reset({"crisis_type": "mass_casualty"})
    patient = env.state.patients[0]
    patient.allergies = ["morphine"]
    patient.insurance_verified = True
    patient.insurance_plan = "PPO_GOLD"

    missing = await env.execute_tool(
        "dispense_medication",
        {"patient_id": patient.id, "medication": "morphine"},
        AgentType.PHARMACY,
    )
    assert missing["status"] == "missing_precheck"

    await env.execute_tool("lookup_patient", {"patient_id": patient.id}, AgentType.PHARMACY)
    await env.execute_tool(
        "check_interactions",
        {"patient_id": patient.id, "medication": "morphine"},
        AgentType.PHARMACY,
    )
    blocked = await env.execute_tool(
        "dispense_medication",
        {
            "patient_id": patient.id,
            "medication": "morphine",
            "double_verified": True,
            "emergency": True,
        },
        AgentType.PHARMACY,
    )
    assert blocked["status"] == "needs_override"

    token = env.state.issue_override_token("pharmacy_override", "CMO approved allergy exception", patient.id)
    approved = await env.execute_tool(
        "dispense_medication",
        {
            "patient_id": patient.id,
            "medication": "morphine",
            "double_verified": True,
            "emergency": True,
            "authorization_id": token.id,
        },
        AgentType.PHARMACY,
    )
    assert approved["status"] == "approved"


@pytest.mark.asyncio
async def test_icu_requires_owner_and_capacity_query() -> None:
    from triage.env.hospital_env import HospitalEnv
    from triage.env.state import AgentType

    env = HospitalEnv(seed=13, max_steps=20)
    await env.reset({"crisis_type": "mass_casualty"})
    patient = env.state.patients[0]

    unauthorized = await env.execute_tool(
        "allocate_icu_bed",
        {"patient_id": patient.id},
        AgentType.ER_TRIAGE,
    )
    assert unauthorized["status"] == "blocked"

    missing = await env.execute_tool(
        "allocate_icu_bed",
        {"patient_id": patient.id},
        AgentType.ICU_MANAGEMENT,
    )
    assert missing["status"] == "missing_precheck"

    await env.execute_tool("query_icu_capacity", {"patient_id": patient.id}, AgentType.ICU_MANAGEMENT)
    approved = await env.execute_tool(
        "allocate_icu_bed",
        {"patient_id": patient.id},
        AgentType.ICU_MANAGEMENT,
    )
    assert approved["status"] == "approved"


@pytest.mark.asyncio
async def test_orchestrator_converts_er_icu_attempt_to_delegation() -> None:
    from triage.agents.orchestrator import AgentOrchestrator
    from triage.env.state import ActionType, AgentAction, AgentType

    orchestrator = AgentOrchestrator(
        agents_config_path="./config/agents.yaml",
        mock_llm=True,
        seed=14,
        max_steps=20,
    )
    await orchestrator.reset({"crisis_type": "mass_casualty"})
    prepared = await orchestrator._prepare_action(
        orchestrator.state,
        AgentAction(
            agent_type=AgentType.ER_TRIAGE,
            action_type=ActionType.TRANSFER_TO_ICU,
            target_id=0,
            priority=9,
            reasoning="critical patient needs ICU",
        ),
    )
    assert prepared is False
    assert any(message.request_type == "icu_bed_request" for message in orchestrator.bus.history)


@pytest.mark.asyncio
async def test_openenv_adapter_smoke() -> None:
    from triage.env import TRIAGEOpenEnv

    env = TRIAGEOpenEnv(seed=15, max_steps=5)
    obs = await env.reset({"crisis_type": "outbreak"})
    assert "json" in obs
    _, reward, terminated, info = await env.step(env.action_space.sample())
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert "action_result" in info


def test_dataset_adapter_and_training_report(tmp_path) -> None:
    from triage.training.dataset_adapter import DatasetAdapter
    from triage.training.reporting import generate_training_report

    source = tmp_path / "real.jsonl"
    row_a = {
        "scenario_context": {"crisis_type": "outbreak"},
        "patient_state": {"status": "CRITICAL"},
        "agent_role": "cmo_oversight",
        "action_trace": [{"action_type": "ESCALATE_TO_CMO"}],
        "outcome": {"reward": 2.0},
        "policy_flags": {"safe": True},
        "preference_source": "curated_real",
    }
    row_b = {**row_a, "action_trace": [{"action_type": "BYPASS"}], "outcome": {"reward": 0.5}}
    source.write_text(json.dumps(row_a) + "\n" + json.dumps(row_b), encoding="utf-8")

    adapter = DatasetAdapter()
    pairs = adapter.records_to_pairs(adapter.load(source))
    assert len(pairs) == 1

    summary = tmp_path / "episode_0001_summary.json"
    summary.write_text(json.dumps({"total_reward": 1.0}), encoding="utf-8")
    metrics = {"status": "completed_mock", "preset": "4b_reliable", "dataset_size": 1, "train_loss_curve": [0.8, 0.4]}
    report = generate_training_report(tmp_path, tmp_path / "report", metrics)
    assert (tmp_path / "report" / "training_report.json").exists()
    assert report["training"]["preset"] == "4b_reliable"

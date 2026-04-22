from __future__ import annotations

from fastapi.testclient import TestClient

from triage.api.main import app


def test_health_route() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_episode_routes_and_simulation_aliases() -> None:
    with TestClient(app) as client:
        started = client.post(
            "/api/episodes/start",
            json={
                "crisis_type": "mass_casualty",
                "difficulty": 0.5,
                "max_steps": 15,
                "mock_llm": True,
                "auto_step": False,
            },
        )
        assert started.status_code == 200
        episode_id = started.json()["data"]["episode_id"]

        stepped = client.post(f"/api/episodes/{episode_id}/step")
        assert stepped.status_code == 200
        state = client.get(f"/api/episodes/{episode_id}/state")
        assert state.status_code == 200
        history = client.get(f"/api/episodes/{episode_id}/history")
        assert history.status_code == 200

        compat_state = client.get("/api/simulation/state")
        assert compat_state.status_code == 200


def test_training_and_metrics_routes() -> None:
    with TestClient(app) as client:
        status = client.get("/api/training/status")
        assert status.status_code == 200

        reward_curve = client.get("/api/metrics/reward-curve")
        assert reward_curve.status_code == 200

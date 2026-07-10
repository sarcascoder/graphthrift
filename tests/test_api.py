from fastapi.testclient import TestClient

from graphthrift.api.app import create_app

client = TestClient(create_app())


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_config_and_dataset():
    assert client.get("/v1/config").status_code == 200
    d = client.get("/v1/dataset").json()
    assert d["episodes"] > 0 and d["gold_triples"] > 0


def test_create_and_fetch_run():
    r = client.post("/v1/runs", json={"scenario": "safe", "monthly_volume": 500000})
    assert r.status_code == 200
    body = r.json()
    assert body["gate"]["passed"] is True
    run_id = body["run_id"]

    lst = client.get("/v1/runs").json()
    assert any(x["run_id"] == run_id for x in lst)

    detail = client.get(f"/v1/runs/{run_id}").json()
    assert detail["run_id"] == run_id and "report" in detail

    traces = client.get(f"/v1/runs/{run_id}/traces").json()
    assert "candidate_by_stage" in traces


def test_aggressive_run_flagged_unsafe():
    body = client.post("/v1/runs", json={"scenario": "aggressive"}).json()
    assert body["gate"]["passed"] is False


def test_metrics_endpoint():
    assert "graphthrift_" in client.get("/metrics").text


def test_missing_run_404():
    assert client.get("/v1/runs/deadbeef").status_code == 404

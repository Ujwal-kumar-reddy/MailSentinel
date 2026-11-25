import os

import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from backend.main import MAX_BYTES, create_app
from ml.train import ARTIFACT, pipeline


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    path = tmp_path_factory.mktemp("tests") / "fixture.joblib"
    model = pipeline(LogisticRegression()).fit(["agenda meeting", "meeting notes", "prize lottery", "win lottery"], [0, 0, 1, 1])
    joblib.dump({"model": model, "report": {"winner": "Fixture", "validation": {"Fixture": {}}}}, path)
    with TestClient(create_app(path)) as c:
        yield c


def test_inference(client):
    msg = {"subject": "urgent", "body": "claim your prize https://example.invalid"}
    one = client.post("/predict", json=msg).json()
    assert 0 <= one["spam_probability"] <= 1
    assert one["label"] == ("spam" if one["spam_probability"] > .5 else "legitimate")
    assert "Urgency language" in one["indicators"]
    batch = client.post("/predict-batch", json={"emails": [msg, {"body": "agenda"}]}).json()["results"]
    assert batch[0] == one and len(batch) == 2
    assert "subject" not in one and "body" not in one


@pytest.mark.parametrize("route,payload", [
    ("/predict", {}), ("/predict", {"body": "   "}), ("/predict", {"subject": "X"*501}),
    ("/predict", {"body": "X"*50001}), ("/predict", {"body": "sensitive", "unknown": True}),
    ("/predict-batch", {"emails": []}), ("/predict-batch", {"emails": [{"body": "a"}]*101})])
def test_invalid(client, route, payload):
    response = client.post(route, json=payload)
    assert response.status_code == 422 and "sensitive" not in response.text


def test_size_cap(client):
    assert client.post("/predict", content=b"x"*(MAX_BYTES+1)).status_code == 413


def test_metadata(client):
    assert client.get("/health").json()["status"] == "ready"
    assert client.get("/metrics").json()["winner"] == client.get("/models").json()["selected"]


def test_release():
    if not ARTIFACT.exists() and not os.getenv("REQUIRE_RELEASE"):
        pytest.skip("Train the corpus release to run this integration test")
    with TestClient(create_app()) as c:
        report = c.get("/metrics").json()
        assert len(report["validation"]) == 4
        assert sum(map(sum, report["test"]["confusion"])) == sum(report["splits"]["test"].values())
        assert c.post("/predict", json={"subject": "Team agenda"}).json()["model"] == report["winner"]

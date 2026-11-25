import numpy as np
import joblib
from fastapi.testclient import TestClient

from backend.main import create_app
from ml.corpus import read_email
from ml.features import visible_text
from ml.scoring import is_spam, spam_probability
from ml.text import combine
from ml.train import ARTIFACT

MEETING = {"subject": "Tomorrow's project meeting", "body": "Hi team, our project review meeting is scheduled for tomorrow at 10 AM. Please bring your progress reports and prepare a short update on your assigned tasks. Thank you."}
PRIZE = {"subject": "Congratulations! You have won $50,000", "body": "You have been selected as our lucky winner! Claim your $50,000 cash prize immediately. This exclusive offer expires in 24 hours. Send your bank account details to receive your reward."}


def test_release_predicts_reported_examples_and_preserves_scores():
    release = joblib.load(ARTIFACT)
    emails = [MEETING, PRIZE]
    scores = spam_probability(release["model"], [combine(**email) for email in emails])
    with TestClient(create_app()) as client:
        batch = client.post("/predict-batch", json={"emails": emails}).json()["results"]
        for email, result, label, score in zip(emails, batch, ["legitimate", "spam"], scores):
            single = client.post("/predict", json=email).json()
            assert single["label"] == result["label"] == label
            assert np.isclose(single["spam_probability"], score)
            assert np.isclose(result["spam_probability"], score)
            assert (label == "spam") == (score > release["report"]["threshold"])


def test_training_mime_and_form_text_agree():
    raw = b"From: routing@example.invalid\nX-Spam-Status: Yes\nSubject: =?utf-8?q?Caf=C3=A9?=\nContent-Type: text/plain; charset=utf-8\nContent-Transfer-Encoding: quoted-printable\n\nLunch =26 tea\n"
    from_archive = combine(*read_email(raw))
    assert visible_text(from_archive) == visible_text(combine("Caf\u00e9", "Lunch & tea"))
    assert visible_text(combine("Menu", "Lunch & tea\n> Click here\n-- \nlist footer")) == "menu lunch & tea"


def test_spam_column_and_threshold_are_independent():
    class ReverseOrder:
        classes_ = [1, 0]

        def predict_proba(self, texts):
            return np.array([[.57, .43], [.65, .35], [.9, .1]])

    scores = spam_probability(ReverseOrder(), ["a", "b", "c"])
    assert scores.tolist() == [.57, .65, .9]
    assert is_spam(scores, .65).tolist() == [False, False, True]


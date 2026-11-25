import csv
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss, confusion_matrix, f1_score, precision_score, recall_score
from ml.scoring import is_spam
from ml.text import combine

EXAMPLES = Path(__file__).with_name("examples")


def examples(filename, split=None):
    with (EXAMPLES / filename).open(encoding="utf8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream, delimiter="\t") if split is None or r["split"] == split]
    return [combine(r["subject"], r["body"]) for r in rows], [int(r["label"]) for r in rows]


def metrics(labels, probabilities, threshold):
    predicted = is_spam(probabilities, threshold)
    cm = confusion_matrix(labels, predicted, labels=[0, 1])
    return {"accuracy": accuracy_score(labels, predicted), "precision": precision_score(labels, predicted, zero_division=0),
            "recall": recall_score(labels, predicted), "f1": f1_score(labels, predicted),
            "confusion": cm.tolist(), "fpr": cm[0, 1] / cm[0].sum(), "brier": brier_score_loss(labels, probabilities)}


def cost(labels, scores, threshold):
    labels = np.asarray(labels)
    pred = is_spam(scores, threshold)
    return 4 * pred[labels == 0].mean() + (1 - pred[labels == 1].mean())


def policy_cost(y, p, short_y, short_p, threshold):
    # Give the archive and short-message validation panels equal influence.
    return (cost(y, p, threshold) + cost(short_y, short_p, threshold)) / 2


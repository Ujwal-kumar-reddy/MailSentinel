import json
import os
import tempfile
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

from ml.corpus import distribution, load
from ml.experiment import examples, metrics, policy_cost
from ml.features import visible_text
from ml.scoring import spam_probability

ARTIFACT = Path(__file__).resolve().parent / "artifacts" / "release.joblib"
SEED = 42


def pipeline(estimator):
    return make_pipeline(TfidfVectorizer(preprocessor=visible_text, ngram_range=(1, 2),
                         min_df=1, max_features=30000, sublinear_tf=True), estimator)


def unique_partition(texts, labels, reserved):
    kept_x, kept_y = [], []
    for text, label in zip(texts, labels):
        key = visible_text(text)
        if key and key not in reserved:
            reserved.add(key)
            kept_x.append(text)
            kept_y.append(label)
    return kept_x, kept_y


def train():
    texts, labels, eda = load()
    dev, test, yd, yt = train_test_split(texts, labels, test_size=.15, stratify=labels, random_state=SEED)
    train_x, val, y, yv = train_test_split(dev, yd, test_size=15/85, stratify=yd, random_state=SEED)
    extra, ye = examples("development.tsv", "train")
    short, ys = examples("development.tsv", "validation")
    challenge, yc = examples("challenge.tsv")
    reserved = {visible_text(t) for t in test + short + challenge}
    val, yv = unique_partition(val, yv, reserved)
    train_x, y = unique_partition(train_x + extra, y + ye, reserved)
    candidates = {"Multinomial Naive Bayes": MultinomialNB(alpha=.1),
                  "Logistic Regression": LogisticRegression(C=4, max_iter=500, random_state=SEED),
                  "Linear SVM": LinearSVC(C=1, random_state=SEED),
                  "Random Forest": RandomForestClassifier(n_estimators=120, random_state=SEED, n_jobs=1)}
    report = {"dataset": eda, "seed": SEED, "sklearn": sklearn.__version__,
              "splits": {k: distribution(v) for k, v in [("train", y), ("validation", yv), ("short_validation", ys), ("test", yt), ("challenge", yc)]},
              "validation": {}, "short_validation": {}, "train": {}, "thresholds": {}, "policy_cost": {},
              "test_all": {}, "challenge": {}}
    models = {}
    for name, estimator in candidates.items():
        model = CalibratedClassifierCV(pipeline(estimator), method="sigmoid", cv=3, ensemble=False).fit(train_x, y)
        p, ps = spam_probability(model, val), spam_probability(model, short)
        # Lowest cost, then closest to the usual 0.5 cutoff to break flat ties.
        cost, _, threshold = min((policy_cost(yv, p, ys, ps, t), abs(t-.5), t) for t in np.arange(5, 100, 5)/100)
        report["thresholds"][name] = threshold
        report["policy_cost"][name] = cost
        report["validation"][name] = metrics(yv, p, threshold)
        report["short_validation"][name] = metrics(ys, ps, threshold)
        report["train"][name] = metrics(y, spam_probability(model, train_x), threshold)
        models[name] = model
        print(name, threshold, cost, flush=True)
    winner = min(models, key=lambda n: (report["policy_cost"][n], -report["validation"][n]["f1"]))
    reported, _ = examples("reported.tsv")
    report["reported_spam_probabilities"] = {}
    for name, model in models.items():
        threshold = report["thresholds"][name]
        report["reported_spam_probabilities"][name] = spam_probability(model, reported).tolist()
        report["test_all"][name] = metrics(yt, spam_probability(model, test), threshold)
        report["challenge"][name] = metrics(yc, spam_probability(model, challenge), threshold)
    report.update(winner=winner, threshold=report["thresholds"][winner], test=report["test_all"][winner])
    ARTIFACT.parent.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=ARTIFACT.parent, delete=False) as f:
        tmp = f.name
    try:
        joblib.dump({"model": models[winner], "report": report}, tmp, compress=3)
        os.replace(tmp, ARTIFACT)
    finally:
        Path(tmp).unlink(missing_ok=True)
    ARTIFACT.with_name("metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(train(), indent=2))


"""Recreate the original 85%-fit models, or evaluate cached original models."""
import argparse
import json
from pathlib import Path

import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC
from ml.corpus import load
from ml.experiment import examples, metrics
from ml.features import BOUNDARY, ROUTING
from ml.scoring import spam_probability
from ml.text import normalize
from ml.train import ARTIFACT


def compare(cache=None):
    x, y, _ = load()
    dev, test, yd, yt = train_test_split(x, y, test_size=.15, stratify=y, random_state=42)
    challenge, yc = examples("challenge.tsv")
    meeting = "Tomorrow's project meeting\nHi team, our project review meeting is scheduled for tomorrow at 10 AM. Please bring your progress reports and prepare a short update on your assigned tasks. Thank you."
    result = {"archive": {}, "challenge": {}, "meeting": {}, "corpus_audit": {}}
    candidates = {"Linear SVM": LinearSVC(C=1, random_state=42), "Multinomial Naive Bayes": MultinomialNB(alpha=.1),
                  "Logistic Regression": LogisticRegression(C=4, max_iter=500, random_state=42),
                  "Random Forest": RandomForestClassifier(n_estimators=120, n_jobs=1, random_state=42)}
    for name, clf in candidates.items():
        if cache:
            model = joblib.load(cache / (name + ".joblib"))
        else:
            vector = TfidfVectorizer(preprocessor=normalize, ngram_range=(1,2), min_df=2, max_features=30000, sublinear_tf=True)
            model = CalibratedClassifierCV(make_pipeline(vector, clf), method="sigmoid", cv=3, ensemble=False).fit(dev, yd)
        result["archive"][name] = metrics(yt, spam_probability(model, test), .5)
        result["challenge"][name] = metrics(yc, spam_probability(model, challenge), .5)
        result["meeting"][name] = float(spam_probability(model, [meeting])[0])
        if name == "Linear SVM":
            vec, svm = model.calibrated_classifiers_[0].estimator.steps
            vec, svm = vec[1], svm[1]
            weights = svm.coef_[0]
            terms = vec.get_feature_names_out()
            result["svm_most_legitimate_terms"] = terms[weights.argsort()[:20]].tolist()
            row = vec.transform([meeting]).tocoo()
            contributions = sorted(zip(row.data * weights[row.col], terms[row.col]))
            result["meeting_positive_features"] = [(s, float(w)) for w,s in contributions[-6:][::-1]]
            result["meeting_margin"] = float(svm.decision_function(vec.transform([meeting]))[0])
    for label in [0,1]:
        sample = [t.partition("\n")[2].splitlines() for t,l in zip(x,y) if l==label]
        result["corpus_audit"][str(label)] = {
            "messages": len(sample),
            "quoted": sum(any(l.lstrip().startswith(">") for l in lines) for lines in sample),
            "reply_or_footer_boundary": sum(any(BOUNDARY.match(l) for l in lines) for lines in sample),
            "embedded_routing": sum(any(ROUTING.match(l) for l in lines) for lines in sample)}
    ARTIFACT.with_name("baseline.json").write_text(json.dumps(result,indent=2), encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path)
    compare(parser.parse_args().cache)


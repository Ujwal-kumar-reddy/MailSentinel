import numpy as np


def spam_probability(model, texts):
    classes = list(model.classes_)
    if sorted(classes) != [0, 1]:
        raise ValueError("Expected legitimate=0 and spam=1.")
    return model.predict_proba(texts)[:, classes.index(1)]


def is_spam(probabilities, threshold):
    return np.asarray(probabilities) > threshold


"""
deps.py

Owns the single TriageClassifier instance. Loaded once at startup via a
FastAPI lifespan handler in main.py, which must call load_classifier() and
verify normalizer_loaded() -- if the normalizer failed to import inside
predict.py, predict.py silently falls back to scoring UNNORMALIZED text
(its `from normalize import normalize_message` is wrapped in a bare
`except Exception` that sets normalize_message = None). Since the model was
trained on normalized text, that fallback makes every prediction invalid
with no error raised -- so the app must refuse to boot rather than run in
that state.
"""

from api import paths  # noqa: F401  -- MUST run before the src imports below

import predict as _predict  # src/predict.py
from predict import TriageClassifier

from api import config

_classifier = None


def load_classifier():
    global _classifier
    if _classifier is None:
        _classifier = TriageClassifier(config.MODEL_PATH)
    return _classifier


def get_classifier():
    if _classifier is None:
        raise RuntimeError("Classifier not loaded -- load_classifier() was not called at startup")
    return _classifier


def normalizer_loaded():
    return _predict.normalize_message is not None

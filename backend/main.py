import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import joblib
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ml.text import combine
from ml.scoring import is_spam, spam_probability

MAX_BYTES = 2_000_000
DEFAULT_RELEASE = Path(__file__).resolve().parents[1] / "ml/artifacts/release.joblib"


class LimitBody:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            packet = await receive()
            if packet["type"] == "http.disconnect":
                return
            body.extend(packet.get("body", b""))
            if len(body) > MAX_BYTES:
                return await JSONResponse({"detail": "Request exceeds 2 MB."}, 413)(scope, receive, send)
            if not packet.get("more_body"):
                break

        async def replay():
            nonlocal body
            if body is None:
                return await receive()
            data, body = bytes(body), None
            return {"type": "http.request", "body": data, "more_body": False}
        await self.app(scope, replay, send)


class Email(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    subject: str = Field(default="", max_length=500)
    body: str = Field(default="", max_length=50000)

    @model_validator(mode="after")
    def check_content(self):
        if not self.subject and not self.body:
            raise ValueError("Provide a subject or body.")
        return self


class Batch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    emails: Annotated[list[Email], Field(min_length=1, max_length=100)]


RULES = {"Urgency language": re.compile(r"\b(urgent|act now|immediately|last chance)\b", re.I),
         "Credential request": re.compile(r"\b(verify|confirm|enter|send)\b.{0,45}\b(password|credentials|login details)\b", re.I),
         "Prize language": re.compile(r"\b(jackpot|lottery|claim your prize)\b", re.I),
         "Contains a web address": re.compile(r"https?://|www\.", re.I)}


def create_app(artifact=DEFAULT_RELEASE):
    @asynccontextmanager
    async def lifespan(app):
        # Only load an operator-controlled release from disk.
        release = joblib.load(artifact)
        app.state.model = release["model"]
        app.state.report = release["report"]
        yield
        del app.state.model

    app = FastAPI(title="MailSentinel", version="1.0", lifespan=lifespan)
    app.add_middleware(LimitBody)
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in origins.split(",") if s.strip()],
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, exc: RequestValidationError):
        return JSONResponse({"detail": "Check email fields, lengths and batch size."}, 422)

    def classify(items):
        texts = [combine(e.subject, e.body) for e in items]
        probabilities = spam_probability(app.state.model, texts)
        decisions = is_spam(probabilities, app.state.report.get("threshold", .5))
        return [{"label": "spam" if decision else "legitimate", "spam_probability": float(p),
                 "model": app.state.report["winner"], "indicators": [k for k, rule in RULES.items() if rule.search(t)]}
                for t, p, decision in zip(texts, probabilities, decisions)]

    @app.get("/health")
    def health():
        return {"status": "ready", "model": app.state.report["winner"]}

    @app.get("/metrics")
    def metrics():
        return app.state.report

    @app.get("/models")
    def models():
        report = app.state.report
        return {"selected": report["winner"], "models": list(report["validation"])}

    @app.post("/predict")
    def predict(email: Email):
        return classify([email])[0]

    @app.post("/predict-batch")
    def predict_batch(batch: Batch):
        return {"results": classify(batch.emails)}

    return app


app = create_app()

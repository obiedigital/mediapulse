from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from .routers import analytics, articles, auth, briefs, health

app = FastAPI(title="MediaPulse BW API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if get_settings().env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(articles.router)
app.include_router(analytics.router)
app.include_router(briefs.router)
app.include_router(health.router)

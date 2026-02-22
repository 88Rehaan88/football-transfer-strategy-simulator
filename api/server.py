"""
FastAPI application factory.

Kept separate from routes so the app instance can be imported cleanly
by uvicorn without triggering route registration side effects.
"""

from dotenv import load_dotenv
load_dotenv()  # Must run before any module reads GEMINI_API_KEY

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Football Transfer Simulator",
        description="Rule-based transfer strategy simulator with AI-powered analysis",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # Serve the frontend from /
    frontend_dir = Path(__file__).parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app


app = create_app()

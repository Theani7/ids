"""
IntruML — FastAPI application entry point.

Start with:
    sudo uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
import signal
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router, broadcast_results, shutdown_broadcast_task, shutdown_event
from backend.db.database import init_db
from backend.config import CORS_ORIGINS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IntruML",
    description="SaaS Intrusion Detection System backed by XGBoost & CIC-IDS2017",
    version="1.0.0",
)

shutdown_requested = False


def get_cors_origins() -> list:
    """Get CORS origins from environment or use defaults."""
    if CORS_ORIGINS:
        return [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def startup():
    logger.info("Initializing database ...")
    init_db()

    logger.info("Starting background broadcast task ...")
    asyncio.create_task(broadcast_results())

    logger.info("IntruML backend is ready.")

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating shutdown...")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.create_task(shutdown_broadcast_task())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down background tasks...")
    await shutdown_broadcast_task()

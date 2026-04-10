"""
IntruML — FastAPI application entry point.

Start with:
    sudo uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router, broadcast_results
from backend.db.database import init_db

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
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

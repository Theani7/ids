import asyncio
import logging
import json
from typing import List, Any
from fastapi import WebSocket
from backend.ml.geolocation import get_geolocation_for_ip
from backend.crud.alerts import create_alert, create_dns_query, create_http_request
from backend.db.database import SessionLocal
from backend.notifications.telegram_bot import TelegramNotifier

logger = logging.getLogger(__name__)
notifier = TelegramNotifier()

async def process_flow_result(result: dict, websocket_clients: List[WebSocket]):
    """
    Handles a single flow result by broadcasting it immediately 
    and then asynchronously performing geolocation and persistence.
    """
    # 1. Immediate broadcast for low latency (without geo data first)
    # We broadcast immediately so the dashboard updates even if geo/db are slow
    await broadcast_to_clients(result, websocket_clients)

    # 2. Offload heavier tasks to the background
    asyncio.create_task(_handle_background_tasks(result, websocket_clients))

async def _handle_background_tasks(result: dict, websocket_clients: List[WebSocket]):
    """Performs geolocation, database persistence, and notifications in the background."""
    # 1. Geolocation Injection
    try:
        geo_data = await get_geolocation_for_ip(result.get("src_ip", ""))
        result["src_lat"] = geo_data["lat"]
        result["src_lon"] = geo_data["lon"]
        result["src_country"] = geo_data["country"]
        result["src_city"] = geo_data["city"]
    except Exception as e:
        logger.debug(f"Geolocation error: {e}")

    # 2. Persist to DB
    db = SessionLocal()
    try:
        alert = create_alert(db, result)
        result["id"] = alert.id
        if alert.timestamp:
            result["timestamp"] = alert.timestamp.isoformat()
    except Exception as exc:
        logger.error("DB persist error: %s", exc)
    finally:
        db.close()

    # 3. Telegram notification
    if result.get("label") == "MALICIOUS":
        try:
            await notifier.notify(result)
        except Exception as exc:
            logger.debug("Telegram notification error: %s", exc)

    # 4. Optional: Send an update broadcast with geo data
    # (Optional because the frontend might not need a second update for the same flow)
    # For now, we'll skip the second broadcast to save bandwidth unless malicious
    if result.get("label") == "MALICIOUS":
        await broadcast_to_clients(result, websocket_clients)

async def process_dns_result(result: dict, websocket_clients: List[WebSocket]):
    db = SessionLocal()
    try:
        create_dns_query(db, result)
        logger.info(f"Saved DNS: {result.get('query_name')}")
    except Exception as exc:
        logger.error(f"DNS persist error: {exc}")
    finally:
        db.close()
    # Optional: Broadcast DNS if needed

async def process_http_result(result: dict, websocket_clients: List[WebSocket]):
    db = SessionLocal()
    try:
        create_http_request(db, result)
        logger.info(f"Saved HTTP: {result.get('method')} {result.get('host')}")
    except Exception as exc:
        logger.error(f"HTTP persist error: {exc}")
    finally:
        db.close()
    # Optional: Broadcast HTTP if needed

async def broadcast_to_clients(data: Any, clients: List[WebSocket]):
    disconnected: List[WebSocket] = []
    payload = json.dumps(data)
    clients_snapshot = list(clients)
    for ws in clients_snapshot:
        try:
            if ws in clients:
                await ws.send_text(payload)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        try:
            if ws in clients:
                clients.remove(ws)
        except ValueError:
            pass

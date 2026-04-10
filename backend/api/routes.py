"""
FastAPI router — REST endpoints + WebSocket for the IDS dashboard.
"""

import asyncio
import json
import logging
import threading
from typing import List, Optional

import psutil
import pandas as pd
import io
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.config import NETWORK_INTERFACE
from backend.db.database import get_db
from backend.db.models import Alert
from backend.capture.packet_sniffer import PacketSniffer
from backend.ml.predict import predictor
from backend.notifications.telegram_bot import TelegramNotifier
from backend.api.schemas import (
    AlertResponse,
    StatsResponse,
    StatusResponse,
    CaptureStartRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

sniffer: Optional[PacketSniffer] = None
sniffer_thread: Optional[threading.Thread] = None
result_queue: asyncio.Queue = asyncio.Queue()
websocket_clients: List[WebSocket] = []
capturing: bool = False
notifier = TelegramNotifier()

# ---------------------------------------------------------------------------
# Background task — pulls from the queue and broadcasts
# ---------------------------------------------------------------------------


async def broadcast_results():
    """Infinite loop: drain *result_queue*, persist, notify, broadcast."""
    while True:
        try:
            result = await asyncio.wait_for(result_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
        except Exception:
            await asyncio.sleep(0.5)
            continue

        # 1. Geolocation Injection
        from backend.ml.geolocation import get_geolocation_for_ip
        geo_data = await get_geolocation_for_ip(result.get("src_ip", ""))
        result["src_lat"] = geo_data["lat"]
        result["src_lon"] = geo_data["lon"]
        result["src_country"] = geo_data["country"]
        result["src_city"] = geo_data["city"]

        # 2. Persist to DB
        try:
            from backend.db.database import SessionLocal

            db = SessionLocal()
            alert = Alert(
                src_ip=result.get("src_ip", ""),
                dst_ip=result.get("dst_ip", ""),
                src_port=result.get("src_port", 0),
                dst_port=result.get("dst_port", 0),
                protocol=result.get("protocol", ""),
                src_lat=result.get("src_lat"),
                src_lon=result.get("src_lon"),
                src_country=result.get("src_country"),
                src_city=result.get("src_city"),
                label=result.get("label", "NORMAL"),
                confidence=result.get("confidence", 0.0),
                attack_type=result.get("attack_type"),
            )
            db.add(alert)
            db.commit()
            # Attach the generated id / timestamp to the broadcast payload
            result["id"] = alert.id
            if alert.timestamp:
                result["timestamp"] = alert.timestamp.isoformat()
            db.close()
        except Exception as exc:
            logger.error("DB persist error: %s", exc)

        # 2. Telegram notification
        try:
            await notifier.notify(result)
        except Exception as exc:
            logger.debug("Telegram notification error: %s", exc)

        # 3. WebSocket broadcast
        disconnected: List[WebSocket] = []
        payload = json.dumps(result)
        for ws in websocket_clients:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            try:
                websocket_clients.remove(ws)
            except ValueError:
                pass


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------





@router.get("/api/health")
async def health_check():
    return {"status": "ok"}


@router.get("/api/status", response_model=StatusResponse)
async def get_status():
    return StatusResponse(
        capturing=capturing,
        model_loaded=predictor.is_loaded,
        interface=NETWORK_INTERFACE if not capturing else (sniffer.interface if sniffer else NETWORK_INTERFACE),
        websocket_clients=len(websocket_clients),
    )


@router.get("/api/interfaces")
async def get_interfaces():
    """List available network interfaces."""
    try:
        interfaces = list(psutil.net_if_addrs().keys())
    except Exception:
        interfaces = ["eth0", "lo"]
    return {"interfaces": interfaces}


@router.post("/api/capture/start")
async def start_capture(body: CaptureStartRequest):
    global sniffer, sniffer_thread, capturing

    if capturing:
        return {"status": "already_running", "interface": sniffer.interface if sniffer else ""}

    loop = asyncio.get_event_loop()
    sniffer = PacketSniffer(
        interface=body.interface,
        result_queue=result_queue,
        loop=loop,
    )

    sniffer_thread = threading.Thread(target=sniffer.start, daemon=True)
    sniffer_thread.start()
    capturing = True

    return {"status": "started", "interface": body.interface}


@router.post("/api/capture/stop")
async def stop_capture():
    global sniffer, sniffer_thread, capturing

    if not capturing or sniffer is None:
        return {"status": "not_running"}

    sniffer.stop()
    if sniffer_thread and sniffer_thread.is_alive():
        sniffer_thread.join(timeout=5)

    capturing = False
    sniffer = None
    sniffer_thread = None

    return {"status": "stopped"}


@router.get("/api/alerts")
async def get_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    filter: str = Query("all"),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)

    if filter == "malicious":
        query = query.filter(Alert.label == "MALICIOUS")
    elif filter == "normal":
        query = query.filter(Alert.label == "NORMAL")

    total = query.count()
    alerts = (
        query.order_by(Alert.timestamp.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "alerts": [a.to_dict() for a in alerts],
    }


@router.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Alert.id)).scalar() or 0
    malicious = db.query(func.count(Alert.id)).filter(Alert.label == "MALICIOUS").scalar() or 0
    normal = total - malicious
    detection_rate = round(malicious / total * 100, 2) if total > 0 else 0.0

    return StatsResponse(
        total_flows=total,
        malicious_count=malicious,
        normal_count=normal,
        detection_rate=detection_rate,
    )

@router.post("/api/batch-analyze")
async def batch_analyze(file: UploadFile = File(...)):
    # Handle CSV upload and analysis
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents), encoding="utf-8", encoding_errors="replace", low_memory=False)
        df.columns = df.columns.str.strip()
        
        # We don't need label column for predicting, but if it's there we should ignore it
        label_col = None
        for col in df.columns:
            if col.strip().lower() == "label":
                label_col = col
                break
                
        results = predictor.predict_batch(df)
        
        # Optionally send a Telegram summary alert if threats were found
        if results.get("malicious", 0) > 0:
            msg = (
                f"🚨 <b>BATCH ANALYSIS INTRUSION WARNING</b>\n\n"
                f"📁 File: {file.filename}\n"
                f"🛑 Malicious Flows Detected: {results['malicious']}\n"
                f"✅ Normal Flows: {results['normal']}\n\n"
                f"Review the IntruML Dashboard for details."
            )
            import asyncio
            asyncio.create_task(notifier._send_message(msg))
            
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


@router.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await ws.accept()
    websocket_clients.append(ws)
    logger.info("WebSocket client connected (%d total)", len(websocket_clients))

    try:
        while True:
            # Keep alive — the client can also send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            websocket_clients.remove(ws)
        except ValueError:
            pass
        logger.info("WebSocket client disconnected (%d remaining)", len(websocket_clients))

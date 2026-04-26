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
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, UploadFile, File, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.config import NETWORK_INTERFACE, TIMEZONE
from backend.db.database import get_db
from backend.db.models import Alert, TrafficStats, ProtocolStats, DNSQuery, HTTPRequest
from backend.api.rate_limit import check_rate_limit
from backend.capture.packet_sniffer import PacketSniffer
from backend.ml.predict import predictor
from backend.notifications.telegram_bot import TelegramNotifier
from backend.api.schemas import (
    AlertResponse,
    StatsResponse,
    StatusResponse,
    CaptureStartRequest,
    TrafficStatsResponse,
    ProtocolStatsResponse,
    TrendDataResponse,
    GeoDataResponse,
    DNSQueryResponse,
    HTTPRequestResponse,
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
shutdown_event: asyncio.Event = asyncio.Event()

# ---------------------------------------------------------------------------
# Background task — pulls from the queue and broadcasts
# ---------------------------------------------------------------------------


async def broadcast_results():
    """Infinite loop: drain *result_queue*, persist, notify, broadcast."""
    logger.info("Background broadcast task started")
    while not shutdown_event.is_set():
        try:
            result = await asyncio.wait_for(result_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
        except Exception:
            await asyncio.sleep(0.5)
            continue
        
        if shutdown_event.is_set():
            break

        result_type = result.get("type", "flow")

        # Handle different result types
        if result_type == "dns":
            await _persist_dns(result)
        elif result_type == "http":
            await _persist_http(result)
        else:
            # Flow/Alert result (existing behavior)
            await _persist_flow(result)

    logger.info("Background broadcast task stopped")


async def shutdown_broadcast_task():
    """Gracefully shutdown the broadcast task."""
    logger.info("Initiating broadcast task shutdown...")
    shutdown_event.set()
    await asyncio.sleep(1.5)


async def _persist_dns(result: dict) -> None:
    """Persist DNS query to database."""
    from backend.db.database import SessionLocal
    from backend.config import TIMEZONE
    from datetime import datetime
    
    db = SessionLocal()
    try:
        timestamp = result.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        dns = DNSQuery(
            timestamp=timestamp or datetime.now(TIMEZONE),
            src_ip=result.get("src_ip", ""),
            dst_ip=result.get("dst_ip", ""),
            query_name=result.get("query_name", ""),
            query_type=result.get("query_type", ""),
            is_malicious=result.get("is_malicious", False),
        )
        db.add(dns)
        db.commit()
        logger.info(f"Saved DNS: {result.get('query_name')} ({result.get('query_type')})")
    except Exception as exc:
        logger.error(f"DNS persist error: {exc}")
    finally:
        db.close()


async def _persist_http(result: dict) -> None:
    """Persist HTTP request to database."""
    from backend.db.database import SessionLocal
    from backend.config import TIMEZONE
    from datetime import datetime
    
    db = SessionLocal()
    try:
        timestamp = result.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        http = HTTPRequest(
            timestamp=timestamp or datetime.now(TIMEZONE),
            src_ip=result.get("src_ip", ""),
            dst_ip=result.get("dst_ip", ""),
            src_port=result.get("src_port", 0),
            dst_port=result.get("dst_port", 0),
            method=result.get("method", ""),
            host=result.get("host", ""),
            uri=result.get("uri", ""),
            user_agent=result.get("user_agent", ""),
            is_suspicious=result.get("is_suspicious", False),
        )
        db.add(http)
        db.commit()
        logger.info(f"Saved HTTP: {result.get('method')} {result.get('host')}{result.get('uri', '')[:30]}")
    except Exception as exc:
        logger.error(f"HTTP persist error: {exc}")
    finally:
        db.close()


async def _persist_flow(result: dict) -> None:
    """Persist flow result as Alert and broadcast via WebSocket."""
    # 1. Geolocation Injection
    from backend.ml.geolocation import get_geolocation_for_ip
    geo_data = await get_geolocation_for_ip(result.get("src_ip", ""))
    result["src_lat"] = geo_data["lat"]
    result["src_lon"] = geo_data["lon"]
    result["src_country"] = geo_data["country"]
    result["src_city"] = geo_data["city"]

    # 2. Persist to DB
    from backend.db.database import SessionLocal

    db = SessionLocal()
    try:
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
        result["id"] = alert.id
        if alert.timestamp:
            result["timestamp"] = alert.timestamp.isoformat()
    except Exception as exc:
        logger.error("DB persist error: %s", exc)
    finally:
        db.close()

    # 3. Telegram notification (only for malicious flows)
    if result.get("label") == "MALICIOUS":
        try:
            await notifier.notify(result)
        except Exception as exc:
            logger.debug("Telegram notification error: %s", exc)

    # 4. WebSocket broadcast
    disconnected: List[WebSocket] = []
    payload = json.dumps(result)
    clients_snapshot = list(websocket_clients)
    for ws in clients_snapshot:
        try:
            if ws in websocket_clients:
                await ws.send_text(payload)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        try:
            if ws in websocket_clients:
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
async def start_capture(body: CaptureStartRequest, request: Request):
    global sniffer, sniffer_thread, capturing

    # Rate limiting: max 10 capture starts per minute
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"capture:{client_ip}", max_requests=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many capture requests. Please wait.")

    if capturing:
        return {"status": "already_running", "interface": sniffer.interface if sniffer else ""}

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    
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
async def batch_analyze(file: UploadFile = File(...), request: Request = None):
    # Rate limiting: max 5 batch uploads per minute
    if request:
        client_ip = request.client.host if request.client else "unknown"
        if not check_rate_limit(f"batch:{client_ip}", max_requests=5, window_seconds=60):
            raise HTTPException(status_code=429, detail="Too many batch requests. Please wait.")
    
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


# ---------------------------------------------------------------------------
# Traffic & Protocol Statistics
# ---------------------------------------------------------------------------

@router.get("/api/traffic", response_model=TrafficStatsResponse)
async def get_traffic_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get traffic bandwidth statistics for the last N hours."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    
    cutoff = datetime.now(TIMEZONE) - timedelta(hours=hours)
    stats = db.query(TrafficStats).filter(TrafficStats.timestamp >= cutoff).order_by(TrafficStats.timestamp).all()
    
    # Aggregate by hour
    hourly_data = {}
    for stat in stats:
        hour_key = stat.timestamp.strftime("%Y-%m-%d %H:00")
        if hour_key not in hourly_data:
            hourly_data[hour_key] = {"bytes_in": 0, "bytes_out": 0, "packets_in": 0, "packets_out": 0}
        hourly_data[hour_key]["bytes_in"] += stat.bytes_in
        hourly_data[hour_key]["bytes_out"] += stat.bytes_out
        hourly_data[hour_key]["packets_in"] += stat.packets_in
        hourly_data[hour_key]["packets_out"] += stat.packets_out
    
    return {
        "intervals": list(hourly_data.keys()),
        "bytes_in": [v["bytes_in"] for v in hourly_data.values()],
        "bytes_out": [v["bytes_out"] for v in hourly_data.values()],
        "packets_in": [v["packets_in"] for v in hourly_data.values()],
        "packets_out": [v["packets_out"] for v in hourly_data.values()],
    }


@router.get("/api/protocols", response_model=ProtocolStatsResponse)
async def get_protocol_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get protocol distribution statistics."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    
    cutoff = datetime.now(TIMEZONE) - timedelta(hours=hours)
    stats = db.query(ProtocolStats).filter(ProtocolStats.timestamp >= cutoff).all()
    
    # Aggregate by protocol
    protocol_data = {}
    for stat in stats:
        proto = stat.protocol
        if proto not in protocol_data:
            protocol_data[proto] = {"count": 0, "bytes": 0}
        protocol_data[proto]["count"] += stat.count
        protocol_data[proto]["bytes"] += stat.bytes_total
    
    # Get top ports
    port_stats = db.query(
        ProtocolStats.port,
        ProtocolStats.protocol,
        func.sum(ProtocolStats.count).label("total_count")
    ).filter(
        ProtocolStats.timestamp >= cutoff,
        ProtocolStats.port is not None
    ).group_by(ProtocolStats.port, ProtocolStats.protocol).order_by(func.sum(ProtocolStats.count).desc()).limit(10).all()
    
    return {
        "protocols": list(protocol_data.keys()),
        "counts": [v["count"] for v in protocol_data.values()],
        "bytes": [v["bytes"] for v in protocol_data.values()],
        "top_ports": [{"port": p.port, "protocol": p.protocol, "count": p.total_count} for p in port_stats],
    }


# ---------------------------------------------------------------------------
# Attack Trends & Geographic Analysis
# ---------------------------------------------------------------------------

@router.get("/api/trends", response_model=TrendDataResponse)
async def get_attack_trends(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get attack trends over time (hourly and daily aggregation)."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from sqlalchemy import func
    
    cutoff = datetime.now(TIMEZONE) - timedelta(days=days)
    
    # Hourly trends
    hourly = db.query(
        func.strftime("%Y-%m-%d %H:00", Alert.timestamp).label("hour"),
        func.count(Alert.id).label("total"),
        func.sum(func.case([(Alert.label == "MALICIOUS", 1)], else_=0)).label("malicious")
    ).filter(Alert.timestamp >= cutoff).group_by("hour").order_by("hour").all()
    
    # Daily trends
    daily = db.query(
        func.strftime("%Y-%m-%d", Alert.timestamp).label("day"),
        func.count(Alert.id).label("total"),
        func.sum(func.case([(Alert.label == "MALICIOUS", 1)], else_=0)).label("malicious")
    ).filter(Alert.timestamp >= cutoff).group_by("day").order_by("day").all()
    
    # Attack type distribution
    attack_types = db.query(
        Alert.attack_type,
        func.count(Alert.id).label("count")
    ).filter(
        Alert.timestamp >= cutoff,
        Alert.label == "MALICIOUS",
        Alert.attack_type is not None
    ).group_by(Alert.attack_type).order_by(func.count(Alert.id).desc()).all()
    
    return {
        "hourly": {
            "labels": [row[0] for row in hourly],
            "total": [row[1] for row in hourly],
            "malicious": [row[2] for row in hourly],
        },
        "daily": {
            "labels": [row[0] for row in daily],
            "total": [row[1] for row in daily],
            "malicious": [row[2] for row in daily],
        },
        "attack_types": {
            "types": [row[0] for row in attack_types],
            "counts": [row[1] for row in attack_types],
        },
    }


@router.get("/api/geography", response_model=GeoDataResponse)
async def get_geographic_data(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get geographic distribution of attacks."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from sqlalchemy import func
    
    cutoff = datetime.now(TIMEZONE) - timedelta(days=days)
    
    # Country distribution
    countries = db.query(
        Alert.src_country,
        func.count(Alert.id).label("count"),
        func.sum(func.case([(Alert.label == "MALICIOUS", 1)], else_=0)).label("attacks")
    ).filter(
        Alert.timestamp >= cutoff,
        Alert.src_country is not None
    ).group_by(Alert.src_country).order_by(func.count(Alert.id).desc()).limit(20).all()
    
    # City distribution
    cities = db.query(
        Alert.src_city,
        Alert.src_country,
        func.count(Alert.id).label("count"),
        func.sum(func.case([(Alert.label == "MALICIOUS", 1)], else_=0)).label("attacks")
    ).filter(
        Alert.timestamp >= cutoff,
        Alert.src_city is not None
    ).group_by(Alert.src_city, Alert.src_country).order_by(func.count(Alert.id).desc()).limit(20).all()
    
    # Map points (for scatter map)
    map_points = db.query(Alert).filter(
        Alert.timestamp >= cutoff,
        Alert.src_lat is not None,
        Alert.src_lon is not None,
        Alert.label == "MALICIOUS"
    ).all()
    
    return {
        "countries": [
            {"name": c.src_country, "total": c.count, "attacks": c.attacks}
            for c in countries
        ],
        "cities": [
            {"name": ct.src_city, "country": ct.src_country, "total": ct.count, "attacks": ct.attacks}
            for ct in cities
        ],
        "map_points": [
            {"lat": p.src_lat, "lon": p.src_lon, "country": p.src_country, "city": p.src_city, "ip": p.src_ip}
            for p in map_points
        ],
    }


# ---------------------------------------------------------------------------
# DNS & HTTP Monitoring
# ---------------------------------------------------------------------------

@router.get("/api/dns", response_model=DNSQueryResponse)
async def get_dns_queries(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    filter: str = Query("all"),  # all, malicious
    db: Session = Depends(get_db)
):
    """Get DNS query monitoring data."""
    query = db.query(DNSQuery)
    
    if filter == "malicious":
        query = query.filter(DNSQuery.is_malicious == True)
    
    total = query.count()
    queries = query.order_by(DNSQuery.timestamp.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # Top queried domains
    top_domains = db.query(
        DNSQuery.query_name,
        func.count(DNSQuery.id).label("count")
    ).group_by(DNSQuery.query_name).order_by(func.count(DNSQuery.id).desc()).limit(10).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "queries": [q.to_dict() for q in queries],
        "top_domains": [{"domain": d.query_name, "count": d.count} for d in top_domains],
    }


@router.get("/api/http", response_model=HTTPRequestResponse)
async def get_http_requests(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    filter: str = Query("all"),  # all, suspicious
    db: Session = Depends(get_db)
):
    """Get HTTP request monitoring data."""
    query = db.query(HTTPRequest)
    
    if filter == "suspicious":
        query = query.filter(HTTPRequest.is_suspicious == True)
    
    total = query.count()
    requests = query.order_by(HTTPRequest.timestamp.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # Top hosts
    top_hosts = db.query(
        HTTPRequest.host,
        func.count(HTTPRequest.id).label("count")
    ).filter(HTTPRequest.host is not None).group_by(HTTPRequest.host).order_by(func.count(HTTPRequest.id).desc()).limit(10).all()
    
    # Method distribution
    methods = db.query(
        HTTPRequest.method,
        func.count(HTTPRequest.id).label("count")
    ).group_by(HTTPRequest.method).order_by(func.count(HTTPRequest.id).desc()).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "requests": [r.to_dict() for r in requests],
        "top_hosts": [{"host": h.host, "count": h.count} for h in top_hosts],
        "methods": [{"method": m.method, "count": m.count} for m in methods],
    }


# ---------------------------------------------------------------------------
# Debug endpoint - check database counts
# ---------------------------------------------------------------------------

@router.get("/api/debug/counts")
async def debug_counts(db: Session = Depends(get_db)):
    """Debug: Get row counts for all tables."""
    alert_count = db.query(Alert).count()
    dns_count = db.query(DNSQuery).count()
    http_count = db.query(HTTPRequest).count()
    
    # Get recent DNS samples
    recent_dns = db.query(DNSQuery).order_by(DNSQuery.timestamp.desc()).limit(5).all()
    recent_http = db.query(HTTPRequest).order_by(HTTPRequest.timestamp.desc()).limit(5).all()
    
    return {
        "alerts": alert_count,
        "dns_queries": dns_count,
        "http_requests": http_count,
        "recent_dns": [d.to_dict() for d in recent_dns],
        "recent_http": [h.to_dict() for h in recent_http],
    }


# ---------------------------------------------------------------------------
# Export Reports
# ---------------------------------------------------------------------------

@router.get("/api/export/csv")
async def export_csv(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Export alerts as CSV."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    cutoff = datetime.now(TIMEZONE) - timedelta(days=days)
    alerts = db.query(Alert).filter(Alert.timestamp >= cutoff).order_by(Alert.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Source IP", "Dest IP", "Source Port", "Dest Port", 
                     "Protocol", "Country", "City", "Label", "Confidence", "Attack Type"])
    
    for alert in alerts:
        writer.writerow([
            alert.id,
            alert.timestamp.isoformat() if alert.timestamp else "",
            alert.src_ip,
            alert.dst_ip,
            alert.src_port,
            alert.dst_port,
            alert.protocol,
            alert.src_country or "",
            alert.src_city or "",
            alert.label,
            alert.confidence,
            alert.attack_type or "",
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ids_alerts_{days}days.csv"}
    )


@router.get("/api/export/json")
async def export_json(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Export alerts as JSON."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from fastapi.responses import JSONResponse
    
    cutoff = datetime.now(TIMEZONE) - timedelta(days=days)
    alerts = db.query(Alert).filter(Alert.timestamp >= cutoff).order_by(Alert.timestamp.desc()).all()
    
    return JSONResponse(content={
        "exported_at": datetime.now(TIMEZONE).isoformat(),
        "days": days,
        "total": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    })


# ---------------------------------------------------------------------------
# VPN/Tunnel Detection
# ---------------------------------------------------------------------------

@router.get("/api/vpn-tunnels")
async def detect_vpn_tunnels(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Detect potential VPN and tunnel traffic."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from sqlalchemy import func
    
    cutoff = datetime.now(TIMEZONE) - timedelta(hours=hours)
    
    # Common VPN ports
    vpn_ports = [1194, 1723, 500, 4500, 1701, 443, 22, 8080, 51820]
    
    # Check for VPN protocol signatures
    vpn_protocols = db.query(
        Alert.dst_port,
        Alert.protocol,
        func.count(Alert.id).label("count"),
        func.sum(func.case([(Alert.label == "MALICIOUS", 1)], else_=0)).label("suspicious")
    ).filter(
        Alert.timestamp >= cutoff,
        Alert.dst_port.in_(vpn_ports)
    ).group_by(Alert.dst_port, Alert.protocol).order_by(func.count(Alert.id).desc()).all()
    
    # High entropy / unusual traffic patterns (potential tunnels)
    potential_tunnels = db.query(Alert).filter(
        Alert.timestamp >= cutoff,
        Alert.label == "MALICIOUS",
        Alert.dst_port.in_([443, 80, 8080, 8443])
    ).order_by(Alert.timestamp.desc()).limit(50).all()
    
    # DNS tunneling detection (high volume of DNS queries from single IP)
    dns_tunnel_candidates = db.query(
        DNSQuery.src_ip,
        func.count(DNSQuery.id).label("query_count")
    ).filter(
        DNSQuery.timestamp >= cutoff
    ).group_by(DNSQuery.src_ip).having(func.count(DNSQuery.id) > 100).order_by(func.count(DNSQuery.id).desc()).all()
    
    return {
        "vpn_protocols": [
            {"port": p.dst_port, "protocol": p.protocol, "count": p.count, "suspicious": p.suspicious}
            for p in vpn_protocols
        ],
        "potential_tunnels": [a.to_dict() for a in potential_tunnels],
        "dns_tunnel_candidates": [
            {"ip": d.src_ip, "query_count": d.query_count}
            for d in dns_tunnel_candidates
        ],
        "summary": {
            "total_vpn_connections": sum(p.count for p in vpn_protocols),
            "suspicious_tunnels": len(potential_tunnels),
            "dns_tunnel_candidates": len(dns_tunnel_candidates),
        },
    }


# ---------------------------------------------------------------------------
# PCAP Upload & Analysis
# ---------------------------------------------------------------------------

@router.post("/api/pcap/upload")
async def upload_pcap(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and analyze PCAP file."""
    import tempfile
    import os
    
    if not file.filename.endswith(".pcap") and not file.filename.endswith(".pcapng"):
        raise HTTPException(status_code=400, detail="Only .pcap or .pcapng files are supported")
    
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pcap") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Analyze PCAP
        from backend.capture.packet_sniffer import analyze_pcap_file
        results = analyze_pcap_file(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "flows_analyzed": results["flow_count"],
            "malicious_detected": results["malicious_count"],
            "protocols": results["protocols"],
            "top_talkers": results["top_talkers"],
            "alerts": results["alerts"],
        }
    except Exception as e:
        logger.error(f"PCAP analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

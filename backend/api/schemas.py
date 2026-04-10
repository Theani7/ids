"""Pydantic models for the IDS REST / WebSocket API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    src_lat: Optional[float] = None
    src_lon: Optional[float] = None
    src_country: Optional[str] = None
    src_city: Optional[str] = None
    label: str
    confidence: float
    attack_type: Optional[str] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_flows: int
    malicious_count: int
    normal_count: int
    detection_rate: float


class StatusResponse(BaseModel):
    capturing: bool
    model_loaded: bool
    interface: str
    websocket_clients: int


class CaptureStartRequest(BaseModel):
    interface: str


class FlowResult(BaseModel):
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    label: str
    confidence: float
    timestamp: str


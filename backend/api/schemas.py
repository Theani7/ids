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


class TrafficStatsResponse(BaseModel):
    intervals: list[str]
    bytes_in: list[int]
    bytes_out: list[int]
    packets_in: list[int]
    packets_out: list[int]


class ProtocolPortStat(BaseModel):
    port: int
    protocol: str
    count: int


class ProtocolStatsResponse(BaseModel):
    protocols: list[str]
    counts: list[int]
    bytes: list[int]
    top_ports: list[ProtocolPortStat]


class HourlyTrend(BaseModel):
    labels: list[str]
    total: list[int]
    malicious: list[int]


class AttackTypeDist(BaseModel):
    types: list[str]
    counts: list[int]


class TrendDataResponse(BaseModel):
    hourly: HourlyTrend
    daily: HourlyTrend
    attack_types: AttackTypeDist


class CountryStat(BaseModel):
    name: str
    total: int
    attacks: int


class CityStat(BaseModel):
    name: str
    country: str
    total: int
    attacks: int


class MapPoint(BaseModel):
    lat: float
    lon: float
    country: str
    city: str
    ip: str


class GeoDataResponse(BaseModel):
    countries: list[CountryStat]
    cities: list[CityStat]
    map_points: list[MapPoint]


class TopDomain(BaseModel):
    domain: str
    count: int


class DNSQueryResponse(BaseModel):
    total: int
    page: int
    limit: int
    queries: list[dict]
    top_domains: list[TopDomain]


class TopHost(BaseModel):
    host: str
    count: int


class MethodStat(BaseModel):
    method: str
    count: int


class HTTPRequestResponse(BaseModel):
    total: int
    page: int
    limit: int
    requests: list[dict]
    top_hosts: list[TopHost]
    methods: list[MethodStat]


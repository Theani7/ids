from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from backend.db.database import Base


class Alert(Base):
    """Stores every detected flow with classification results."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    src_ip = Column(String, nullable=False)
    dst_ip = Column(String, nullable=False)
    src_port = Column(Integer, nullable=False)
    dst_port = Column(Integer, nullable=False)
    protocol = Column(String, nullable=False)
    src_lat = Column(Float, nullable=True)
    src_lon = Column(Float, nullable=True)
    src_country = Column(String, nullable=True)
    src_city = Column(String, nullable=True)
    label = Column(String, nullable=False)  # "NORMAL" or "MALICIOUS"
    confidence = Column(Float, nullable=False)
    attack_type = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol,
            "src_lat": self.src_lat,
            "src_lon": self.src_lon,
            "src_country": self.src_country,
            "src_city": self.src_city,
            "label": self.label,
            "confidence": self.confidence,
            "attack_type": self.attack_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class TrafficStats(Base):
    """Stores traffic bandwidth statistics per time interval."""
    __tablename__ = "traffic_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    interface = Column(String, nullable=False)
    bytes_in = Column(BigInteger, default=0)
    bytes_out = Column(BigInteger, default=0)
    packets_in = Column(Integer, default=0)
    packets_out = Column(Integer, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "interface": self.interface,
            "bytes_in": self.bytes_in,
            "bytes_out": self.bytes_out,
            "packets_in": self.packets_in,
            "packets_out": self.packets_out,
        }


class ProtocolStats(Base):
    """Stores protocol distribution statistics."""
    __tablename__ = "protocol_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    protocol = Column(String, nullable=False)  # TCP, UDP, ICMP, etc.
    port = Column(Integer, nullable=True)
    count = Column(Integer, default=0)
    bytes_total = Column(BigInteger, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "protocol": self.protocol,
            "port": self.port,
            "count": self.count,
            "bytes_total": self.bytes_total,
        }


class DNSQuery(Base):
    """Stores DNS query monitoring data."""
    __tablename__ = "dns_queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    src_ip = Column(String, nullable=False)
    dst_ip = Column(String, nullable=True)
    query_name = Column(String, nullable=False)
    query_type = Column(String, nullable=False)  # A, AAAA, MX, etc.
    response_code = Column(String, nullable=True)
    is_malicious = Column(Integer, default=0)  # 0 or 1
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "query_name": self.query_name,
            "query_type": self.query_type,
            "response_code": self.response_code,
            "is_malicious": bool(self.is_malicious),
        }


class HTTPRequest(Base):
    """Stores HTTP request monitoring data."""
    __tablename__ = "http_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    src_ip = Column(String, nullable=False)
    dst_ip = Column(String, nullable=True)
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    method = Column(String, nullable=False)  # GET, POST, etc.
    host = Column(String, nullable=True)
    uri = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    content_type = Column(String, nullable=True)
    is_suspicious = Column(Integer, default=0)  # 0 or 1
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "method": self.method,
            "host": self.host,
            "uri": self.uri,
            "user_agent": self.user_agent,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "is_suspicious": bool(self.is_suspicious),
        }


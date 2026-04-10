from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Float, DateTime
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


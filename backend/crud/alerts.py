from sqlalchemy.orm import Session
from backend.db.models import Alert, DNSQuery, HTTPRequest

def create_alert(db: Session, alert_data: dict) -> Alert:
    alert = Alert(
        src_ip=alert_data.get("src_ip", ""),
        dst_ip=alert_data.get("dst_ip", ""),
        src_port=alert_data.get("src_port", 0),
        dst_port=alert_data.get("dst_port", 0),
        protocol=alert_data.get("protocol", ""),
        src_lat=alert_data.get("src_lat"),
        src_lon=alert_data.get("src_lon"),
        src_country=alert_data.get("src_country"),
        src_city=alert_data.get("src_city"),
        label=alert_data.get("label", "NORMAL"),
        confidence=alert_data.get("confidence", 0.0),
        attack_type=alert_data.get("attack_type"),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def create_dns_query(db: Session, dns_data: dict) -> DNSQuery:
    dns = DNSQuery(
        timestamp=dns_data.get("timestamp"),
        src_ip=dns_data.get("src_ip", ""),
        dst_ip=dns_data.get("dst_ip", ""),
        query_name=dns_data.get("query_name", ""),
        query_type=dns_data.get("query_type", ""),
        is_malicious=dns_data.get("is_malicious", False),
    )
    db.add(dns)
    db.commit()
    db.refresh(dns)
    return dns

def create_http_request(db: Session, http_data: dict) -> HTTPRequest:
    http = HTTPRequest(
        timestamp=http_data.get("timestamp"),
        src_ip=http_data.get("src_ip", ""),
        dst_ip=http_data.get("dst_ip", ""),
        src_port=http_data.get("src_port", 0),
        dst_port=http_data.get("dst_port", 0),
        method=http_data.get("method", ""),
        host=http_data.get("host", ""),
        uri=http_data.get("uri", ""),
        user_agent=http_data.get("user_agent", ""),
        is_suspicious=http_data.get("is_suspicious", False),
    )
    db.add(http)
    db.commit()
    db.refresh(http)
    return http

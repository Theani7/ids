"""
Real-time packet sniffer using Scapy.

Runs in a daemon thread and pushes classified flow results into an
``asyncio.Queue`` so the FastAPI event loop can broadcast them over
WebSocket and persist them to the database.
"""

import asyncio
import logging
import threading
from datetime import datetime
from typing import Optional

from backend.ml.feature_extractor import FlowTracker
from backend.ml.predict import predictor
from backend.config import TIMEZONE

logger = logging.getLogger(__name__)


class PacketSniffer:
    """Scapy-based packet sniffer that runs in a background thread."""

    def __init__(
        self,
        interface: str,
        result_queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
    ):
        self.interface = interface
        self.result_queue = result_queue
        self.loop = loop
        self.tracker = FlowTracker()
        self._stop_event = threading.Event()
        self._packet_count = 0
        self._last_log_time = datetime.now()

    # ------------------------------------------------------------------
    # Async helper — called from the *event-loop* thread via
    # ``loop.call_soon_threadsafe``.
    # ------------------------------------------------------------------

    async def _put_result(self, result: dict) -> None:
        """Put a result dict on the asyncio queue."""
        await self.result_queue.put(result)

    # ------------------------------------------------------------------
    # Packet handling (runs in the sniffer thread)
    # ------------------------------------------------------------------

    def _packet_callback(self, packet) -> None:
        """Called by Scapy for every captured packet."""
        try:
            self._packet_count += 1
            
            # Log every 100 packets to verify capture is working
            now = datetime.now()
            if (now - self._last_log_time).seconds >= 5:
                logger.info(f"Captured {self._packet_count} packets on {self.interface}")
                self._last_log_time = now
            
            self.tracker.add_packet(packet)
            self._check_completed_flows()
            self._extract_dns_http(packet)
        except Exception as exc:
            logger.debug("Error processing packet: %s", exc)

    def _extract_dns_http(self, packet) -> None:
        """Extract DNS queries and HTTP requests from packets."""
        from scapy.all import TCP, IP, Raw
        from scapy.layers.dns import DNS, DNSQR
        from datetime import datetime
        
        # Extract DNS queries
        if packet.haslayer(DNS) and packet.haslayer(DNSQR):
            try:
                dns = packet[DNS]
                dns_qr = packet[DNSQR]
                
                if dns_qr.qname:
                    query_name = dns_qr.qname.decode() if isinstance(dns_qr.qname, bytes) else str(dns_qr.qname)
                    query_name = query_name.rstrip('.')
                    query_type = self._get_dns_type(dns_qr.qtype)
                    
                    # Check for suspicious DNS (long queries, high entropy, etc)
                    is_malicious = len(query_name) > 50 or query_name.count('.') > 5
                    
                    logger.info(f"DNS QUERY: {query_name} (type: {query_type}) from {packet[IP].src if packet.haslayer(IP) else '?'}")
                    
                    result = {
                        "type": "dns",
                        "timestamp": datetime.now(TIMEZONE).isoformat(),
                        "src_ip": packet[IP].src if packet.haslayer(IP) else "",
                        "dst_ip": packet[IP].dst if packet.haslayer(IP) else "",
                        "query_name": query_name,
                        "query_type": query_type,
                        "is_malicious": is_malicious,
                    }
                    
                    # Thread-safe transfer
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self._put_result(result),
                            self.loop
                        )
                    except RuntimeError:
                        pass
            except Exception as exc:
                logger.error(f"Error extracting DNS: {exc}")
        
        # Extract HTTP requests (only on port 80 or common HTTP ports)
        if packet.haslayer(TCP) and packet.haslayer(Raw) and packet.haslayer(IP):
            try:
                tcp = packet[TCP]
                # Only check common HTTP ports
                if tcp.dport not in [80, 8080, 8000, 3000, 5000, 5173] and tcp.sport not in [80, 8080, 8000, 3000, 5000, 5173]:
                    return
                    
                payload = packet[Raw].load.decode('utf-8', errors='ignore')
                
                # Check if it's an HTTP request (look for HTTP method at start)
                http_methods = ('GET ', 'POST ', 'PUT ', 'DELETE ', 'PATCH ', 'HEAD ', 'OPTIONS ')
                if any(payload.startswith(m) for m in http_methods):
                    lines = payload.split('\r\n')
                    request_line = lines[0]
                    parts = request_line.split(' ')
                    
                    if len(parts) >= 2:
                        method = parts[0]
                        uri = parts[1]
                        
                        # Extract headers
                        headers = {}
                        for line in lines[1:]:
                            if ':' in line:
                                key, value = line.split(':', 1)
                                headers[key.strip().lower()] = value.strip()
                        
                        host = headers.get('host', packet[IP].dst)
                        user_agent = headers.get('user-agent', '')
                        
                        logger.info(f"HTTP {method}: {host}{uri[:50]} from {packet[IP].src}")
                        
                        # Check for suspicious patterns
                        suspicious_patterns = ['sql', 'union', 'select', 'insert', 'delete', 'drop', 'script', 'onload', 'onerror']
                        is_suspicious = any(p in uri.lower() or p in payload.lower() for p in suspicious_patterns)
                        
                        result = {
                            "type": "http",
                            "timestamp": datetime.now(TIMEZONE).isoformat(),
                            "src_ip": packet[IP].src,
                            "dst_ip": packet[IP].dst,
                            "src_port": tcp.sport,
                            "dst_port": tcp.dport,
                            "method": method,
                            "host": host,
                            "uri": uri[:200],
                            "user_agent": user_agent[:200],
                            "is_suspicious": is_suspicious,
                        }
                        
                        # Thread-safe transfer
                        try:
                            asyncio.run_coroutine_threadsafe(
                                self._put_result(result),
                                self.loop
                            )
                        except RuntimeError:
                            pass
            except Exception as exc:
                logger.error(f"Error extracting HTTP: {exc}")

    def _get_dns_type(self, qtype: int) -> str:
        """Convert DNS query type number to string."""
        types = {1: 'A', 2: 'NS', 5: 'CNAME', 6: 'SOA', 12: 'PTR', 
                 15: 'MX', 16: 'TXT', 28: 'AAAA', 33: 'SRV', 255: 'ANY'}
        return types.get(qtype, f'TYPE{qtype}')

    def _check_completed_flows(self) -> None:
        """Extract completed flows, classify them, and queue results."""
        completed = self.tracker.get_completed_flows()
        for flow in completed:
            metadata = flow["metadata"]
            features = flow["features"]

            prediction = predictor.predict(features)

            result = {
                "src_ip": metadata["src_ip"],
                "dst_ip": metadata["dst_ip"],
                "src_port": metadata["src_port"],
                "dst_port": metadata["dst_port"],
                "protocol": metadata["protocol"],
                "label": prediction["label"],
                "confidence": prediction["confidence"],
                "attack_type": prediction.get("attack_type"),
                "timestamp": datetime.now(TIMEZONE).isoformat(),
            }

            # Thread-safe transfer into the async world
            try:
                asyncio.run_coroutine_threadsafe(
                    self._put_result(result),
                    self.loop
                )
            except RuntimeError:
                # Event loop might have closed during shutdown
                pass

    # ------------------------------------------------------------------
    # Start / stop
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Blocking call — run from a daemon thread."""
        try:
            from scapy.all import sniff, get_if_list
        except ImportError:
            logger.error(
                "Scapy is not installed. Install it with: pip install scapy"
            )
            return

        # Validate interface exists
        try:
            available_interfaces = get_if_list()
            if self.interface not in available_interfaces:
                logger.error(
                    "Interface '%s' not found. Available interfaces: %s",
                    self.interface,
                    ", ".join(available_interfaces) if available_interfaces else "none"
                )
                return
        except Exception as e:
            logger.warning("Could not validate interface: %s", e)

        logger.info("Starting packet capture on interface '%s' ...", self.interface)

        try:
            sniff(
                iface=self.interface,
                prn=self._packet_callback,
                store=False,
                stop_filter=lambda _p: self._stop_event.is_set(),
            )
        except PermissionError:
            logger.error(
                "Permission denied — Scapy requires root/admin privileges. "
                "Run the backend with: sudo uvicorn backend.main:app ..."
            )
        except OSError as exc:
            logger.error("Sniffer OS error (bad interface?): %s", exc)
        except Exception as exc:
            logger.error("Sniffer error: %s", exc)
        finally:
            logger.info("Packet capture stopped on '%s'.", self.interface)

    def stop(self) -> None:
        """Signal the sniffer thread to stop."""
        self._stop_event.set()


def analyze_pcap_file(pcap_path: str) -> dict:
    """Analyze a PCAP file and return statistics."""
    from scapy.all import rdpcap
    from collections import Counter
    from backend.ml.feature_extractor import FlowTracker
    from backend.ml.predict import predictor
    
    logger.info(f"Analyzing PCAP file: {pcap_path}")
    
    try:
        packets = rdpcap(pcap_path)
        logger.info(f"Loaded {len(packets)} packets from PCAP")
    except Exception as e:
        logger.error(f"Failed to read PCAP file: {e}")
        raise
    
    tracker = FlowTracker()
    protocols = Counter()
    top_talkers = Counter()
    skipped = 0
    
    for packet in packets:
        try:
            tracker.add_packet(packet)
            
            if packet.haslayer("IP"):
                proto = "TCP" if packet.haslayer("TCP") else "UDP" if packet.haslayer("UDP") else "OTHER"
                protocols[proto] += 1
                top_talkers[packet["IP"].src] += 1
        except Exception:
            skipped += 1
    
    logger.info(f"Processed packets, skipped {skipped}, active flows: {len(tracker.active_flows)}")
    
    completed_flows = tracker.get_all_flows()
    logger.info(f"Found {len(completed_flows)} total flows")
    
    malicious_count = 0
    alerts = []
    model_loaded = predictor.is_loaded
    
    for flow in completed_flows:
        try:
            metadata = flow["metadata"]
            features = flow["features"]
            prediction = predictor.predict(features)
            
            if prediction["label"] == "MALICIOUS":
                malicious_count += 1
                alerts.append({
                    "src_ip": metadata["src_ip"],
                    "dst_ip": metadata["dst_ip"],
                    "src_port": metadata["src_port"],
                    "dst_port": metadata["dst_port"],
                    "protocol": metadata["protocol"],
                    "confidence": prediction["confidence"],
                })
        except Exception as e:
            logger.error(f"Flow prediction error: {e}")
    
    logger.info(f"PCAP analysis complete: {malicious_count} malicious out of {len(completed_flows)} flows (model loaded: {model_loaded})")
    
    tracker.clear()
    
    return {
        "flow_count": len(completed_flows),
        "malicious_count": malicious_count,
        "protocols": dict(protocols),
        "top_talkers": [{"ip": ip, "packets": count} for ip, count in top_talkers.most_common(10)],
        "alerts": alerts[:50],
    }

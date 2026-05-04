"""
Flow-level feature extractor that mirrors the CIC-IDS2017 feature set.

Tracks active network flows keyed by 5-tuple and computes ~80 statistical
features for each completed flow, enabling direct use with models trained
on CIC-IDS2017 data.
"""

import time
import math
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any

from backend.config import FLOW_TIMEOUT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division that returns *default* when the denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def safe_mean(values: List[float], default: float = 0.0) -> float:
    if not values:
        return default
    return sum(values) / len(values)


def safe_std(values: List[float], default: float = 0.0) -> float:
    if len(values) < 2:
        return default
    return statistics.stdev(values)


def safe_min(values: List[float], default: float = 0.0) -> float:
    if not values:
        return default
    return min(values)


def safe_max(values: List[float], default: float = 0.0) -> float:
    if not values:
        return default
    return max(values)


def safe_variance(values: List[float], default: float = 0.0) -> float:
    if len(values) < 2:
        return default
    return statistics.variance(values)


def compute_iat(timestamps: List[float]) -> List[float]:
    """Compute inter-arrival times from a sorted list of timestamps."""
    if len(timestamps) < 2:
        return []
    return [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]


# ---------------------------------------------------------------------------
# Packet info container
# ---------------------------------------------------------------------------

class PacketInfo:
    """Lightweight container for the fields we extract from each packet."""

    __slots__ = (
        "timestamp", "length", "src_ip", "dst_ip",
        "src_port", "dst_port", "protocol",
        "tcp_flags", "header_length", "ip_header_length",
        "tcp_window",
    )

    def __init__(
        self,
        timestamp: float,
        length: int,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: str,
        tcp_flags: int = 0,
        header_length: int = 0,
        ip_header_length: int = 0,
        tcp_window: int = 0,
    ):
        self.timestamp = timestamp
        self.length = length
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.protocol = protocol
        self.tcp_flags = tcp_flags
        self.header_length = header_length
        self.ip_header_length = ip_header_length
        self.tcp_window = tcp_window


# ---------------------------------------------------------------------------
# TCP flag masks
# ---------------------------------------------------------------------------

FIN = 0x01
SYN = 0x02
RST = 0x04
PSH = 0x08
ACK = 0x10
URG = 0x20
ECE = 0x40
CWR = 0x80


# ---------------------------------------------------------------------------
# Flow data aggregator
# ---------------------------------------------------------------------------

class FlowData:
    """Accumulates per-flow statistics for a single network flow."""

    def __init__(self, first_packet: PacketInfo):
        self.src_ip = first_packet.src_ip
        self.dst_ip = first_packet.dst_ip
        self.src_port = first_packet.src_port
        self.dst_port = first_packet.dst_port
        self.protocol = first_packet.protocol
        
        # Numeric protocol for ML model (TCP=6, UDP=17, etc.)
        self.protocol_num = 6 if self.protocol == "TCP" else 17 if self.protocol == "UDP" else 0

        # Direction: forward == same direction as the first packet
        self.fwd_packets: List[PacketInfo] = []
        self.bwd_packets: List[PacketInfo] = []
        self.all_timestamps: List[float] = []

        self.start_time: float = first_packet.timestamp
        self.last_seen: float = first_packet.timestamp

        # TCP flag counters (across all packets)
        self.fin_count = 0
        self.syn_count = 0
        self.rst_count = 0
        self.psh_count = 0
        self.ack_count = 0
        self.urg_count = 0
        self.cwe_count = 0
        self.ece_count = 0

        # Fwd/Bwd specific flag counters
        self.fwd_psh_flags = 0
        self.bwd_psh_flags = 0
        self.fwd_urg_flags = 0
        self.bwd_urg_flags = 0

        # Initial TCP window sizes
        self.init_win_fwd: int = 0
        self.init_win_bwd: int = 0
        self._fwd_win_set = False
        self._bwd_win_set = False

        # Active/Idle tracking
        self.active_times: List[float] = []
        self.idle_times: List[float] = []
        self._activity_threshold = 1.0  # 1 second
        self._last_active_start: float = first_packet.timestamp
        self._last_active_end: float = first_packet.timestamp

        # fwd data packets (packets with payload > 0 header)
        self.act_data_pkt_fwd = 0
        self.min_seg_size_fwd: int = 0
        self._min_seg_set = False

        self.closed = False

        # Process the first packet
        self._add(first_packet, is_forward=True)

    # ------------------------------------------------------------------
    def _add(self, pkt: PacketInfo, is_forward: bool):
        """Internal: accumulate a single packet."""
        self.last_seen = pkt.timestamp
        self.all_timestamps.append(pkt.timestamp)

        # TCP flags
        flags = pkt.tcp_flags
        if flags & FIN:
            self.fin_count += 1
        if flags & SYN:
            self.syn_count += 1
        if flags & RST:
            self.rst_count += 1
        if flags & PSH:
            self.psh_count += 1
        if flags & ACK:
            self.ack_count += 1
        if flags & URG:
            self.urg_count += 1
        if flags & CWR:
            self.cwe_count += 1
        if flags & ECE:
            self.ece_count += 1

        # Active / Idle
        gap = pkt.timestamp - self._last_active_end
        if gap > self._activity_threshold:
            active_duration = self._last_active_end - self._last_active_start
            if active_duration > 0:
                self.active_times.append(active_duration)
            self.idle_times.append(gap)
            self._last_active_start = pkt.timestamp
        self._last_active_end = pkt.timestamp

        if is_forward:
            self.fwd_packets.append(pkt)
            if flags & PSH:
                self.fwd_psh_flags += 1
            if flags & URG:
                self.fwd_urg_flags += 1
            if not self._fwd_win_set and pkt.protocol == "TCP":
                self.init_win_fwd = pkt.tcp_window
                self._fwd_win_set = True
            # Data packets in fwd direction (payload present)
            payload_len = pkt.length - pkt.header_length
            if payload_len > 0:
                self.act_data_pkt_fwd += 1
            if pkt.header_length > 0:
                if not self._min_seg_set:
                    self.min_seg_size_fwd = pkt.header_length
                    self._min_seg_set = True
                else:
                    self.min_seg_size_fwd = min(self.min_seg_size_fwd, pkt.header_length)
        else:
            self.bwd_packets.append(pkt)
            if flags & PSH:
                self.bwd_psh_flags += 1
            if flags & URG:
                self.bwd_urg_flags += 1
            if not self._bwd_win_set and pkt.protocol == "TCP":
                self.init_win_bwd = pkt.tcp_window
                self._bwd_win_set = True

        # Check for connection close
        if flags & FIN or flags & RST:
            self.closed = True

    # ------------------------------------------------------------------
    def add_packet(self, pkt: PacketInfo):
        """Add a packet to this flow, auto-detecting direction."""
        is_forward = pkt.src_ip == self.src_ip and pkt.src_port == self.src_port
        self._add(pkt, is_forward)

    # ------------------------------------------------------------------
    def is_expired(self, now: float) -> bool:
        return (now - self.last_seen) >= FLOW_TIMEOUT

    # ------------------------------------------------------------------
    def compute_features(self) -> Dict[str, float]:
        """Return a dict of CIC-IDS2017-compatible feature values."""

        fwd_lengths = [p.length for p in self.fwd_packets]
        bwd_lengths = [p.length for p in self.bwd_packets]
        all_lengths = fwd_lengths + bwd_lengths

        fwd_ts = sorted([p.timestamp for p in self.fwd_packets])
        bwd_ts = sorted([p.timestamp for p in self.bwd_packets])
        all_ts = sorted(self.all_timestamps)

        flow_duration = (self.last_seen - self.start_time) * 1e6  # microseconds
        total_fwd = len(self.fwd_packets)
        total_bwd = len(self.bwd_packets)
        total_packets = total_fwd + total_bwd

        fwd_iat = compute_iat(fwd_ts)
        bwd_iat = compute_iat(bwd_ts)
        flow_iat = compute_iat(all_ts)

        fwd_header_len = sum(p.header_length for p in self.fwd_packets)
        bwd_header_len = sum(p.header_length for p in self.bwd_packets)

        # Finalize active/idle
        last_active_dur = self._last_active_end - self._last_active_start
        if last_active_dur > 0:
            active_times = self.active_times + [last_active_dur]
        else:
            active_times = list(self.active_times)
        idle_times = list(self.idle_times)

        total_fwd_len = sum(fwd_lengths)
        total_bwd_len = sum(bwd_lengths)

        flow_duration_sec = safe_div(flow_duration, 1e6)

        features: Dict[str, float] = {
            "Source Port": self.src_port,
            "Destination Port": self.dst_port,
            "Protocol": self.protocol_num,
            "Flow Duration": flow_duration,
            "Total Fwd Packets": total_fwd,
            "Total Backward Packets": total_bwd,
            "Total Length of Fwd Packets": total_fwd_len,
            "Total Length of Bwd Packets": total_bwd_len,

            "Fwd Packet Length Max": safe_max(fwd_lengths),
            "Fwd Packet Length Min": safe_min(fwd_lengths),
            "Fwd Packet Length Mean": safe_mean(fwd_lengths),
            "Fwd Packet Length Std": safe_std(fwd_lengths),

            "Bwd Packet Length Max": safe_max(bwd_lengths),
            "Bwd Packet Length Min": safe_min(bwd_lengths),
            "Bwd Packet Length Mean": safe_mean(bwd_lengths),
            "Bwd Packet Length Std": safe_std(bwd_lengths),

            "Flow Bytes/s": safe_div(total_fwd_len + total_bwd_len, flow_duration_sec),
            "Flow Packets/s": safe_div(total_packets, flow_duration_sec),

            "Flow IAT Mean": safe_mean(flow_iat),
            "Flow IAT Std": safe_std(flow_iat),
            "Flow IAT Max": safe_max(flow_iat),
            "Flow IAT Min": safe_min(flow_iat),

            "Fwd IAT Total": sum(fwd_iat) if fwd_iat else 0.0,
            "Fwd IAT Mean": safe_mean(fwd_iat),
            "Fwd IAT Std": safe_std(fwd_iat),
            "Fwd IAT Max": safe_max(fwd_iat),
            "Fwd IAT Min": safe_min(fwd_iat),

            "Bwd IAT Total": sum(bwd_iat) if bwd_iat else 0.0,
            "Bwd IAT Mean": safe_mean(bwd_iat),
            "Bwd IAT Std": safe_std(bwd_iat),
            "Bwd IAT Max": safe_max(bwd_iat),
            "Bwd IAT Min": safe_min(bwd_iat),

            "Fwd PSH Flags": self.fwd_psh_flags,
            "Bwd PSH Flags": self.bwd_psh_flags,
            "Fwd URG Flags": self.fwd_urg_flags,
            "Bwd URG Flags": self.bwd_urg_flags,

            "Fwd Header Length": fwd_header_len,
            "Bwd Header Length": bwd_header_len,

            "Fwd Packets/s": safe_div(total_fwd, flow_duration_sec),
            "Bwd Packets/s": safe_div(total_bwd, flow_duration_sec),

            "Min Packet Length": safe_min(all_lengths),
            "Max Packet Length": safe_max(all_lengths),
            "Packet Length Mean": safe_mean(all_lengths),
            "Packet Length Std": safe_std(all_lengths),
            "Packet Length Variance": safe_variance(all_lengths),

            "FIN Flag Count": self.fin_count,
            "SYN Flag Count": self.syn_count,
            "RST Flag Count": self.rst_count,
            "PSH Flag Count": self.psh_count,
            "ACK Flag Count": self.ack_count,
            "URG Flag Count": self.urg_count,
            "CWE Flag Count": self.cwe_count,
            "ECE Flag Count": self.ece_count,

            "Down/Up Ratio": safe_div(total_bwd, total_fwd),
            "Average Packet Size": safe_div(total_fwd_len + total_bwd_len, total_packets),
            "Avg Fwd Segment Size": safe_mean(fwd_lengths),
            "Avg Bwd Segment Size": safe_mean(bwd_lengths),

            "Fwd Header Length.1": fwd_header_len,

            "Subflow Fwd Packets": total_fwd,
            "Subflow Fwd Bytes": total_fwd_len,
            "Subflow Bwd Packets": total_bwd,
            "Subflow Bwd Bytes": total_bwd_len,

            "Init_Win_bytes_forward": self.init_win_fwd,
            "Init_Win_bytes_backward": self.init_win_bwd,

            "act_data_pkt_fwd": self.act_data_pkt_fwd,
            "min_seg_size_forward": self.min_seg_size_fwd,

            "Active Mean": safe_mean(active_times),
            "Active Std": safe_std(active_times),
            "Active Max": safe_max(active_times),
            "Active Min": safe_min(active_times),

            "Idle Mean": safe_mean(idle_times),
            "Idle Std": safe_std(idle_times),
            "Idle Max": safe_max(idle_times),
            "Idle Min": safe_min(idle_times),
        }

        return features

    # ------------------------------------------------------------------
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol,
        }


# ---------------------------------------------------------------------------
# FlowTracker — top-level class used by the packet sniffer
# ---------------------------------------------------------------------------

FlowKey = Tuple[str, str, int, int, str]


class FlowTracker:
    """Maintains active flows and yields completed ones on demand."""

    def __init__(self, max_flows: int = 100000):
        self.active_flows: Dict[FlowKey, FlowData] = {}
        self.max_flows = max_flows

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_packet_info(packet) -> Optional[PacketInfo]:
        """Extract fields from a Scapy packet."""
        try:
            from scapy.layers.inet import IP, TCP, UDP

            if not packet.haslayer(IP):
                return None

            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            ip_header_length = ip_layer.ihl * 4 if hasattr(ip_layer, "ihl") else 20

            src_port = 0
            dst_port = 0
            protocol = "OTHER"
            tcp_flags = 0
            header_length = ip_header_length
            tcp_window = 0

            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                protocol = "TCP"
                tcp_flags = int(tcp_layer.flags) if tcp_layer.flags else 0
                tcp_header_len = tcp_layer.dataofs * 4 if hasattr(tcp_layer, "dataofs") and tcp_layer.dataofs else 20
                header_length = ip_header_length + tcp_header_len
                tcp_window = tcp_layer.window if hasattr(tcp_layer, "window") else 0
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
                protocol = "UDP"
                header_length = ip_header_length + 8  # UDP header is always 8 bytes

            return PacketInfo(
                timestamp=float(packet.time),
                length=len(packet),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                tcp_flags=tcp_flags,
                header_length=header_length,
                ip_header_length=ip_header_length,
                tcp_window=tcp_window,
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    def _flow_key(self, pkt_info: PacketInfo) -> FlowKey:
        """Canonical flow key (smaller IP first for bidirectional matching)."""
        forward = (pkt_info.src_ip, pkt_info.dst_ip, pkt_info.src_port, pkt_info.dst_port, pkt_info.protocol)
        reverse = (pkt_info.dst_ip, pkt_info.src_ip, pkt_info.dst_port, pkt_info.src_port, pkt_info.protocol)
        # Check if we already track the reverse
        if reverse in self.active_flows:
            return reverse
        return forward

    # ------------------------------------------------------------------
    def add_packet(self, packet) -> None:
        """Process a Scapy packet and assign it to a flow."""
        pkt_info = self._extract_packet_info(packet)
        if pkt_info is None:
            return

        key = self._flow_key(pkt_info)

        if key in self.active_flows:
            self.active_flows[key].add_packet(pkt_info)
        else:
            # Robustness: Hard cap on active flows to prevent memory exhaustion
            if len(self.active_flows) >= self.max_flows:
                # If full, drop the oldest flow to make room
                try:
                    oldest_key = min(self.active_flows.keys(), key=lambda k: self.active_flows[k].last_seen)
                    del self.active_flows[oldest_key]
                except Exception:
                    # Fallback: just clear a random one if min() fails
                    self.active_flows.pop(next(iter(self.active_flows)))
            
            self.active_flows[key] = FlowData(pkt_info)

    # ------------------------------------------------------------------
    def get_completed_flows(self) -> List[Dict[str, Any]]:
        """Return a list of completed flow dicts and remove them from tracking."""
        now = time.time()
        completed: List[Dict[str, Any]] = []
        keys_to_remove: List[FlowKey] = []

        for key, flow in self.active_flows.items():
            if flow.closed or flow.is_expired(now):
                features = flow.compute_features()
                completed.append({
                    "metadata": flow.metadata,
                    "features": features,
                })
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.active_flows[key]

        return completed

    # ------------------------------------------------------------------
    def get_all_flows(self) -> List[Dict[str, Any]]:
        """Return all active flows (for PCAP analysis)."""
        flows: List[Dict[str, Any]] = []
        for key, flow in self.active_flows.items():
            features = flow.compute_features()
            flows.append({
                "metadata": flow.metadata,
                "features": features,
            })
        return flows

    # ------------------------------------------------------------------
    def clear(self) -> None:
        """Clear all active flows (used after PCAP analysis)."""
        self.active_flows.clear()

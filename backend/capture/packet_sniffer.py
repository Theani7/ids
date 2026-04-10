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
from zoneinfo import ZoneInfo
from typing import Optional

from backend.ml.feature_extractor import FlowTracker
from backend.ml.predict import predictor

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
            self.tracker.add_packet(packet)
            self._check_completed_flows()
        except Exception as exc:
            logger.debug("Error processing packet: %s", exc)

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
                "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
            }

            # Thread-safe transfer into the async world
            try:
                self.loop.call_soon_threadsafe(
                    asyncio.ensure_future,
                    self._put_result(result),
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
            from scapy.all import sniff
        except ImportError:
            logger.error(
                "Scapy is not installed. Install it with: pip install scapy"
            )
            return

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

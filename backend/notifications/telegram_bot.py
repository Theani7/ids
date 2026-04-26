"""
Telegram Bot notifications for the IDS.

Sends rate-limited alerts for malicious traffic and periodic summaries
for normal traffic via the Telegram Bot API.
"""

import time
import logging
from datetime import datetime

import httpx

from backend.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_COOLDOWN,
    TELEGRAM_NORMAL_INTERVAL,
    TIMEZONE,
)

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Sends alerts and summaries to a Telegram chat."""

    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.last_malicious_alert: float = 0.0
        self.normal_flow_count: int = 0
        self.last_normal_summary: float = time.time()
        self._enabled = bool(self.token and self.chat_id)

        if not self._enabled:
            logger.warning(
                "Telegram notifications disabled — TELEGRAM_BOT_TOKEN or "
                "TELEGRAM_CHAT_ID not set in .env"
            )

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------
    async def _send_message(self, text: str) -> bool:
        """Low-level: POST to the Telegram sendMessage endpoint."""
        if not self._enabled:
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    logger.debug("Telegram message sent.")
                    return True
                else:
                    logger.warning("Telegram API error %s: %s", resp.status_code, resp.text)
                    return False
        except Exception as exc:
            logger.error("Telegram send failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    async def send_malicious_alert(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: str,
        confidence: float,
        timestamp: str,
    ) -> bool:
        """Send an intrusion alert (rate-limited by TELEGRAM_COOLDOWN)."""
        now = time.time()
        if now - self.last_malicious_alert < TELEGRAM_COOLDOWN:
            return False

        message = (
            "🚨 <b>INTRUSION DETECTED</b>\n\n"
            "🔴 Status: MALICIOUS TRAFFIC\n"
            f"📍 Source: {src_ip}:{src_port}\n"
            f"🎯 Destination: {dst_ip}:{dst_port}\n"
            f"🔌 Protocol: {protocol}\n"
            f"📊 Confidence: {confidence * 100:.1f}%\n"
            f"🕐 Time: {timestamp}\n\n"
            "⚠️ Review your network immediately."
        )

        sent = await self._send_message(message)
        if sent:
            self.last_malicious_alert = now
        return sent

    # ------------------------------------------------------------------
    async def send_normal_summary(self, count: int) -> bool:
        """Send a periodic summary of normal flows."""
        now = time.time()
        if now - self.last_normal_summary < TELEGRAM_NORMAL_INTERVAL:
            return False

        ist_now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        message = (
            "✅ <b>Traffic Status: NORMAL</b>\n\n"
            f"📦 Flows analyzed: {count}\n"
            "🛡️ No threats detected\n"
            f"🕐 Last checked: {ist_now} IST\n\n"
            "IDS is monitoring your network."
        )

        sent = await self._send_message(message)
        if sent:
            self.normal_flow_count = 0
            self.last_normal_summary = now
        return sent

    # ------------------------------------------------------------------
    async def notify(self, result: dict) -> None:
        """Route a flow result to the appropriate notification handler."""
        label = result.get("label", "NORMAL")

        if label == "MALICIOUS":
            await self.send_malicious_alert(
                src_ip=result.get("src_ip", "?"),
                dst_ip=result.get("dst_ip", "?"),
                src_port=result.get("src_port", 0),
                dst_port=result.get("dst_port", 0),
                protocol=result.get("protocol", "?"),
                confidence=result.get("confidence", 0.0),
                timestamp=result.get("timestamp", ""),
            )
        else:
            self.normal_flow_count += 1
            await self.send_normal_summary(self.normal_flow_count)

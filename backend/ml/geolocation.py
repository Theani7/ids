import httpx
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Very basic thread-safe caching (lru_cache holds arguments locally)
@lru_cache(maxsize=1000)
def _get_geolocation_cached_sync(ip: str) -> dict:
    # IP-API free tier does not require an API key
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,city,lat,lon"
    try:
        # We use a synchronous request here because lru_cache doesn't support async cleanly without specialized wrappers,
        # and we don't want to overcomplicate the caching mechanism.
        with httpx.Client(timeout=3) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return {
                        "lat": data.get("lat", 0.0),
                        "lon": data.get("lon", 0.0),
                        "country": data.get("country", "Unknown"),
                        "city": data.get("city", "Unknown")
                    }
                else:
                    logger.warning(f"Geolocation API failed for IP {ip}: {data.get('message')}")
    except Exception as e:
        logger.error(f"Geolocation request failed for {ip}: {e}")
        
    return {"lat": 0.0, "lon": 0.0, "country": "Unknown", "city": "Unknown"}

async def get_geolocation_for_ip(ip: str) -> dict:
    """
    Returns geographical coordinates and location info for a given IP address.
    """
    # Exclude internal / local IPs quickly
    if (
        ip.startswith("192.168.") or
        ip.startswith("10.") or
        ip.startswith("172.16.") or
        ip.startswith("172.31.") or
        ip == "127.0.0.1" or
        ip == "::1"
    ):
        return {"lat": 0.0, "lon": 0.0, "country": "Internal Network", "city": "LAN"}
        
    # We offload the sync cached function to the async event loop to avoid blocking fastapi
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_geolocation_cached_sync, ip)

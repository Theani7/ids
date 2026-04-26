import httpx
import logging
import threading

logger = logging.getLogger(__name__)

# Thread-safe cache using a lock
class ThreadSafeCache:
    def __init__(self, maxsize: int = 1000):
        self._cache = {}
        self._lock = threading.Lock()
        self._maxsize = maxsize
    
    def get(self, key: str):
        with self._lock:
            return self._cache.get(key)
    
    def set(self, key: str, value: dict):
        with self._lock:
            if len(self._cache) >= self._maxsize:
                # Remove oldest entry (simple FIFO)
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[key] = value
    
    def clear(self):
        with self._lock:
            self._cache.clear()


_geolocation_cache = ThreadSafeCache(maxsize=1000)


def _get_geolocation_sync(ip: str) -> dict:
    # Check cache first
    cached = _geolocation_cache.get(ip)
    if cached is not None:
        return cached
    
    # IP-API free tier does not require an API key
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,city,lat,lon"
    try:
        with httpx.Client(timeout=3) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    result = {
                        "lat": data.get("lat", 0.0),
                        "lon": data.get("lon", 0.0),
                        "country": data.get("country", "Unknown"),
                        "city": data.get("city", "Unknown")
                    }
                    _geolocation_cache.set(ip, result)
                    return result
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
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    return await loop.run_in_executor(None, _get_geolocation_sync, ip)
